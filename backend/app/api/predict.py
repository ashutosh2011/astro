"""Prediction endpoint for LLM-powered astrological predictions."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.calc_snapshot import CalcSnapshot
from app.models.prediction import Prediction
from app.models.profile import Profile
from app.schemas.predict import QuestionRequest, AnswerResponse
from app.services.llm.classifier import topic_classifier
from app.services.llm.payload_builder import payload_builder
from app.services.llm.openai_client import openai_client
from app.services.calc_engine.orchestrator import calc_orchestrator
from app.services.encryption_service import encryption_service
from app.utils.errors import LLMError, NotFoundError, ValidationError
from app.utils.rate_limit import predict_rate_limit
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


def _finalize_confidence(llm_result: Dict, sensitivity_data: Dict = None, uncertainty_minutes: int = 0) -> float:
    """Finalize confidence score with sensitivity adjustments."""
    try:
        # Start with LLM confidence
        confidence_topic = llm_result.get("answer", {}).get("confidence_topic", 0.5)
        overall = confidence_topic
        
        # Apply sensitivity penalties
        if sensitivity_data:
            if sensitivity_data.get("dasha_boundary_risky", False):
                overall -= 0.10
                logger.debug("Applied dasha boundary penalty: -0.10")
            
            if sensitivity_data.get("lagna_flips", False) or sensitivity_data.get("moon_sign_flips", False):
                overall -= 0.05
                logger.debug("Applied lagna/moon flip penalty: -0.05")
        
        # Apply uncertainty penalty
        if uncertainty_minutes > 0:
            overall -= 0.10
            logger.debug(f"Applied uncertainty penalty for {uncertainty_minutes} minutes: -0.10")
        
        # Clamp to [0, 1]
        overall = max(0.0, min(1.0, overall))
        
        logger.info(f"Final confidence: {overall:.2f} (base: {confidence_topic:.2f})")
        return overall
        
    except Exception as e:
        logger.error(f"Error calculating confidence: {str(e)}", exc_info=True)
        return 0.5  # Default confidence


def _get_conversation_context(profile_id: int, db: Session, limit: int = 2) -> List[Dict]:
    """Get recent conversation context."""
    try:
        recent_predictions = db.query(Prediction).filter(
            Prediction.profile_id == profile_id
        ).order_by(Prediction.created_at.desc()).limit(limit).all()
        
        context = []
        for pred in reversed(recent_predictions):  # Reverse to get chronological order
            context.append({
                "role": "user",
                "question": pred.question
            })
            context.append({
                "role": "assistant",
                "answer_summary": pred.result_json.get("answer", {}).get("summary", "")[:100] + "..."
            })
        
        return context
        
    except Exception:
        return []


@router.post("/question", response_model=AnswerResponse)
# @predict_rate_limit  # Temporarily disabled for testing
async def predict_question(
    http_request: Request,
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get astrological prediction for a question."""
    try:
        # Get profile
        profile = db.query(Profile).filter(
            Profile.id == request.profile_id,
            Profile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise NotFoundError("Profile not found")
        
        # Get latest calc snapshot
        calc_snapshot = db.query(CalcSnapshot).filter(
            CalcSnapshot.profile_id == request.profile_id,
            CalcSnapshot.user_id == current_user.id
        ).order_by(CalcSnapshot.created_at.desc()).first()
        
        if not calc_snapshot:
            raise NotFoundError("No calculation snapshot found. Please run calculation first.")
        
        # Decompress calc snapshot
        import base64
        compressed_data = base64.b64decode(calc_snapshot.payload_json.encode('ascii'))
        calc_snapshot_data = calc_orchestrator.decompress_calc_snapshot(compressed_data)
        
        # Classify question topic
        topic = await topic_classifier.classify_question(request.question)
        
        # Get conversation context
        conversation_context = _get_conversation_context(request.profile_id, db)
        
        # Prepare user profile
        decrypted_profile = encryption_service.decrypt_dict(
            {"name": profile.name},
            ["name"]
        )
        
        user_profile = {
            "name": decrypted_profile["name"],
            "gender": profile.gender,
            "tz": profile.tz,
            "place": profile.place
        }
        
        # Build LLM payload
        payload = payload_builder.build_payload(
            user_profile=user_profile,
            calc_snapshot=calc_snapshot_data,
            question=request.question,
            topic=topic,
            conversation_context=conversation_context,
            time_horizon_months=request.time_horizon_months
        )
        
        # Create LLM messages
        system_prompt = """You are an expert Vedic astrologer. Analyze the provided astrological data and answer the user's question with specific, actionable insights.

Guidelines:
- Provide time-bound predictions with specific time windows
- Base your analysis on the provided astrological calculations
- Give 2-4 actionable suggestions
- Mention 0-2 risks or cautions if relevant
- Cite specific astrological evidence for your conclusions
- Be concise but comprehensive
- Avoid fatalistic language
- Do not suggest remedies or rituals

Return your response as valid JSON matching this schema:
{
  "topic": "string",
  "answer": {
    "summary": "string (≤150 words)",
    "time_windows": [
      {
        "start": "YYYY-MM-DD",
        "end": "YYYY-MM-DD", 
        "focus": "string",
        "confidence": 0.0-1.0
      }
    ],
    "actions": ["string", "string", "string"],
    "risks": ["string"] (optional),
    "evidence": [
      {
        "calc_field": "string",
        "value": "any",
        "interpretation": "string"
      }
    ],
    "confidence_topic": 0.0-1.0,
    "rationale": "Short explanation connecting evidence to conclusion",
    "sources": [
      { "title": "string", "url": "string?", "note": "string?" }
    ]
  },
  "confidence_overall": 0.0-1.0
}"""
        
        user_prompt = json.dumps(payload, default=str)
        
        messages = openai_client.create_messages(system_prompt, user_prompt)
        
        # Get LLM response
        llm_result = await openai_client.generate_response(messages, purpose="predict-json")
        
        # Finalize confidence
        sensitivity_data = calc_snapshot_data.get("sensitivity")
        final_confidence = _finalize_confidence(llm_result, sensitivity_data, profile.uncertainty_minutes)
        
        # Update LLM result with final confidence
        llm_result["confidence_overall"] = final_confidence
        
        # Store prediction
        prediction = Prediction(
            user_id=current_user.id,
            profile_id=request.profile_id,
            calc_snapshot_id=calc_snapshot.id,
            question=request.question,
            topic=topic,
            llm_model=openai_client.model,
            llm_params_json=json.dumps({
                "temperature": openai_client.temperature,
                "max_tokens": openai_client.max_tokens,
                "seed": openai_client.seed
            }),
            result_json=json.dumps(llm_result),
            confidence_overall=final_confidence
        )
        
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        # Prepare response
        answer = llm_result.get("answer", {})
        sensitivity_notice = None
        
        if sensitivity_data and (sensitivity_data.get("lagna_flips") or 
                                sensitivity_data.get("moon_sign_flips") or 
                                sensitivity_data.get("dasha_boundary_risky")):
            sensitivity_notice = "Birth time uncertainty may affect accuracy of predictions"
        
        return AnswerResponse(
            prediction_id=prediction.id,
            topic=topic,
            answer=answer,
            confidence_overall=final_confidence,
            sensitivity_notice=sensitivity_notice,
            calc_snapshot_id=calc_snapshot.id,
            llm_model=openai_client.model,
            created_at=prediction.created_at.isoformat() + "Z"
        )
        
    except (LLMError, NotFoundError, ValidationError) as e:
        logger.error(f"Prediction failed with known error: {type(e).__name__}: {e.message}", exc_info=False)
        raise HTTPException(
            status_code=400 if isinstance(e, (NotFoundError, ValidationError)) else 500,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected prediction error for user {current_user.id}, profile {request.profile_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during prediction: {str(e)}"
        )


@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get prediction by ID."""
    try:
        prediction = db.query(Prediction).filter(
            Prediction.id == prediction_id,
            Prediction.user_id == current_user.id
        ).first()
        
        if not prediction:
            raise NotFoundError("Prediction not found")
        
        return {
            "id": prediction.id,
            "question": prediction.question,
            "topic": prediction.topic,
            "result": prediction.result_json,
            "confidence_overall": prediction.confidence_overall,
            "llm_model": prediction.llm_model,
            "created_at": prediction.created_at.isoformat() + "Z"
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving prediction")


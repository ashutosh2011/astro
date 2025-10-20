"""Chat endpoints for conversational astrology mode."""

import json
from typing import List, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.chat_message import ChatMessage
from app.models.calc_snapshot import CalcSnapshot
from app.models.profile import Profile
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryResponse,
    ChatHistoryItem,
)
from app.api.auth import get_current_user
from app.models.user import User
from app.services.llm.openai_client import openai_client
from app.services.calc_engine.orchestrator import calc_orchestrator
from app.services.encryption_service import encryption_service
from app.utils.errors import NotFoundError


router = APIRouter()


def _extract_conversation_themes(chat_history: List[Dict]) -> List[str]:
    """Extract key themes from conversation history."""
    themes = []
    if not chat_history:
        return themes
    
    # Simple keyword-based theme extraction
    all_content = " ".join([msg.get("content", "") for msg in chat_history])
    all_content_lower = all_content.lower()
    
    theme_keywords = {
        "career": ["job", "career", "work", "profession", "business", "promotion", "salary"],
        "relationships": ["marriage", "relationship", "love", "partner", "romance", "dating"],
        "health": ["health", "illness", "medical", "wellness", "disease", "symptoms"],
        "family": ["family", "children", "parents", "siblings", "relatives"],
        "finance": ["money", "finance", "wealth", "investment", "financial", "income"],
        "spirituality": ["spiritual", "meditation", "prayer", "religion", "faith", "enlightenment"],
        "education": ["education", "study", "learning", "school", "college", "knowledge"],
        "travel": ["travel", "journey", "migration", "foreign", "abroad", "relocation"]
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in all_content_lower for keyword in keywords):
            themes.append(theme)
    
    return themes[:5]  # Return max 5 themes


def _extract_previous_topics(chat_history: List[Dict]) -> List[str]:
    """Extract previous discussion topics from chat history."""
    topics = []
    if not chat_history:
        return topics
    
    # Extract topics from assistant messages (responses)
    for msg in chat_history:
        if msg.get("role") == "assistant":
            content = msg.get("content", "").lower()
            # Look for section headers in responses
            if "**analysis**" in content or "analysis:" in content:
                topics.append("detailed_analysis")
            if "**current influences**" in content or "current influences:" in content:
                topics.append("current_timing")
            if "**future outlook**" in content or "future outlook:" in content:
                topics.append("future_predictions")
    
    return list(set(topics))  # Remove duplicates


def _calculate_age_years(birth_date_str: str) -> int:
    """Calculate age in years from birth date string (format: YYYY-MM-DD)."""
    if not birth_date_str:
        return 0
    
    try:
        # Parse the date string (format: YYYY-MM-DD)
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        current_date = datetime.utcnow().date()
        age = current_date.year - birth_date.year
        if current_date.month < birth_date.month or (current_date.month == birth_date.month and current_date.day < birth_date.day):
            age -= 1
        return age
    except:
        return 0


def _determine_life_phase(birth_date_str: str) -> str:
    """Determine life phase based on age."""
    age = _calculate_age_years(birth_date_str)
    
    if age < 18:
        return "youth"
    elif age < 30:
        return "early_adult"
    elif age < 45:
        return "mid_adult"
    elif age < 60:
        return "mature_adult"
    else:
        return "senior"


def _get_seasonal_context() -> Dict[str, str]:
    """Get current seasonal context."""
    now = datetime.utcnow()
    month = now.month
    
    seasons = {
        12: "winter", 1: "winter", 2: "winter",
        3: "spring", 4: "spring", 5: "spring",
        6: "summer", 7: "summer", 8: "summer",
        9: "autumn", 10: "autumn", 11: "autumn"
    }
    
    return {
        "current_season": seasons.get(month, "unknown"),
        "month": now.strftime("%B"),
        "year": str(now.year)
    }


def _get_planetary_periods_context(dasha_info: Dict) -> Dict[str, str]:
    """Get context about current planetary periods."""
    if not dasha_info:
        return {}
    
    return {
        "current_mahadasha": dasha_info.get("current_md", "unknown"),
        "current_antardasha": dasha_info.get("current_ad", "unknown"),
        "dasha_balance": dasha_info.get("md_balance_years", 0),
        "next_mahadasha": dasha_info.get("next_md", "unknown")
    }


def _serialize_message(msg: ChatMessage) -> ChatHistoryItem:
    return ChatHistoryItem(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        created_at=msg.created_at.isoformat() + "Z",
    )


@router.get("/history/{profile_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return chat history for a profile."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise NotFoundError("Profile not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.profile_id == profile_id, ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    items: List[ChatHistoryItem] = [_serialize_message(m) for m in messages]
    return ChatHistoryResponse(messages=items, total=len(items))


@router.post("/message", response_model=ChatMessageResponse)
async def post_chat_message(
    http_request: Request,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Post a chat message and get assistant reply grounded in calc snapshot."""
    # Validate profile
    profile = db.query(Profile).filter(
        Profile.id == request.profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise NotFoundError("Profile not found")

    # Get latest calc snapshot
    calc_snapshot = (
        db.query(CalcSnapshot)
        .filter(CalcSnapshot.profile_id == request.profile_id, CalcSnapshot.user_id == current_user.id)
        .order_by(CalcSnapshot.created_at.desc())
        .first()
    )
    if not calc_snapshot:
        raise NotFoundError("No calculation snapshot found. Please run calculation first.")

    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        profile_id=request.profile_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    db.flush()

    # Build comprehensive context from calc snapshot
    import base64
    compressed_data = base64.b64decode(calc_snapshot.payload_json.encode("ascii"))
    calc_snapshot_data = calc_orchestrator.decompress_calc_snapshot(compressed_data)

    # Enhanced profile info with decrypted birth data
    decrypted_profile = encryption_service.decrypt_dict({
        "name": profile.name,
        "dob": profile.dob,
        "tob": profile.tob
    }, ["name", "dob", "tob"]) 
    
    user_profile = {
        "name": decrypted_profile["name"],
        "gender": profile.gender,
        "tz": profile.tz,
        "place": profile.place,
        "birth_date": decrypted_profile["dob"],
        "birth_time": decrypted_profile["tob"],
        "lat": profile.lat,
        "lon": profile.lon,
        "ayanamsa": profile.ayanamsa,
        "house_system": profile.house_system,
        "uncertainty_minutes": profile.uncertainty_minutes
    }

    # Get chat history (expanded for GPT-5's large context window)
    chat_history = [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in db.query(ChatMessage)
        .filter(ChatMessage.profile_id == request.profile_id, ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)  # Increased to 20 to leverage GPT-5's context window
        .all()[::-1]
    ]

    # Optimized system prompt (shorter to avoid rate limits)
    system_prompt = (
        "You are Dr. Astro, a Vedic astrologer with 40+ years of experience. "
        "Analyze the provided astrological data and give comprehensive insights.\n\n"
        
        "**Analysis Framework:**\n"
        "1. Examine planetary positions, houses, aspects, and yogas\n"
        "2. Consider current dasha periods and transits\n"
        "3. Provide practical guidance with confidence levels\n\n"
        
        "**Response Format:**\n"
        "**Analysis**: Key astrological factors (200-300 words)\n"
        "**Current Influences**: What's happening now (150-200 words)\n"
        "**Future Outlook**: Upcoming periods (150-200 words)\n"
        "**Guidance**: Actionable recommendations (100-150 words)\n"
        "**Timeline**: Specific periods to watch\n"
        "**Key Factors**: 3-4 main astrological elements"
    )

    # Build optimized context payload (reduced size to avoid rate limits)
    optimized_context = {
        "user_profile": {
            "name": user_profile["name"],
            "birth_date": user_profile["birth_date"],
            "birth_time": user_profile["birth_time"],
            "place": user_profile["place"],
            "age_years": _calculate_age_years(user_profile.get("birth_date")),
            "life_phase": _determine_life_phase(user_profile.get("birth_date"))
        },
        "astrological_data": {
            "planetary_positions": [
                {
                    "planet": planet.get("name", ""),
                    "sign": planet.get("sign", ""),
                    "degree": planet.get("degree", 0),
                    "house": planet.get("house", 0)
                }
                for planet in calc_snapshot_data.get("d1", {}).get("planets", [])  # Include all planets
            ],
            "dasha_info": {
                "current_mahadasha": calc_snapshot_data.get("dasha", {}).get("current_mahadasha", ""),
                "current_antardasha": calc_snapshot_data.get("dasha", {}).get("current_antardasha", ""),
                "remaining_years": calc_snapshot_data.get("dasha", {}).get("remaining_years", 0)
            },
            "transits": {
                "jupiter_transit": calc_snapshot_data.get("transits", {}).get("jupiter_transit", ""),
                "saturn_transit": calc_snapshot_data.get("transits", {}).get("saturn_transit", ""),
                "mars_transit": calc_snapshot_data.get("transits", {}).get("mars_transit", "")
            },
            "yogas": [
                {
                    "name": yoga.get("name", ""),
                    "description": yoga.get("description", "")
                }
                for yoga in calc_snapshot_data.get("yogas", [])  # Include all yogas
            ]
        },
        "conversation_context": {
            "chat_history": chat_history,
            "conversation_themes": _extract_conversation_themes(chat_history)
        },
        "current_message": request.message
    }

    # Compose user content as JSON for grounding (optimized size)
    user_content = json.dumps(optimized_context, default=str, indent=2)

    # Ask LLM for freeform text (no strict JSON needed here)
    messages = [
        openai_client.create_system_message(system_prompt),
        openai_client.create_user_message(user_content),
    ]

    assistant_text = await openai_client.generate_text(messages, purpose="chat-text")

    # Store assistant reply
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        profile_id=request.profile_id,
        role="assistant",
        content=assistant_text,
        llm_model=openai_client.model,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageResponse(
        message_id=assistant_msg.id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        llm_model=assistant_msg.llm_model,
        created_at=assistant_msg.created_at.isoformat() + "Z",
    )



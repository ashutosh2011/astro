"""OpenAI client with JSON mode and retry logic."""

import json
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI, AsyncOpenAI  # Import both sync and async clients
from app.config import settings
from app.utils.errors import LLMError, LLMJsonParseFailedError, LLMTimeoutError


class OpenAIClient:
    """OpenAI client with JSON mode and retry logic."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client: Optional[AsyncOpenAI] = None
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.seed = settings.llm_seed
        self.timeout_ms = settings.llm_timeout_ms
        self._connected = False
        self.logger = logging.getLogger(__name__)
        
        # GPT-5 specific parameters
        self.reasoning_effort = "medium"  # Options: minimal, medium, high
        self.verbosity = "medium"  # Options: low, medium, high
        
        try:
            if not settings.openai_api_key:
                print("="*80)
                print("⚠️  WARNING: OpenAI API key not configured. Using MOCK responses!")
                print("⚠️  All AI predictions will be FAKE data for testing only.")
                print("⚠️  Set OPENAI_API_KEY environment variable to enable real AI.")
                print("="*80)
                self._connected = True  # Enable mock functionality
                return

            # 1. Test connection and API key with a synchronous client
            try:
                sync_client = OpenAI(api_key=settings.openai_api_key, timeout=20.0)
                sync_client.models.list()
                print("✅ OpenAI API key verified.")
            except Exception as test_error:
                print("="*80)
                print(f"⚠️  WARNING: OpenAI API key test failed: {str(test_error)}")
                print("⚠️  Using MOCK client for development.")
                print("⚠️  All AI predictions will be FAKE data for testing only.")
                print("="*80)
                self._connected = True  # Enable mock functionality
                return

            # 2. If test passes, initialize the async client for use
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                timeout=(settings.llm_timeout_ms / 1000.0)
            )
            self._connected = True
            print("✅ OpenAI async client initialized successfully.")
            
        except Exception as e:
            print(f"⚠️ OpenAI client initialization failed: {str(e)}")
            print("🔄 Using mock client for development")
            self.client = None
            self._connected = True  # Enable mock functionality
    
    async def generate_response(self, messages: list, retry_count: int = 0, purpose: str = "default") -> Dict[str, Any]:
        """Generate response with retry logic."""
        if not self._connected:
            raise LLMError("OpenAI client not connected")
        
        # If client is None, use mock response
        if self.client is None:
            return self._get_mock_response(messages)
            
        try:
            req_id = uuid.uuid4().hex[:8]
            self._log_request_start(req_id, purpose, messages)
            # Rely on SDK-level timeout configured on the client
            response_content = await self._make_request(messages, purpose, req_id)
            
            if response_content is None:
                 raise LLMError("Received empty response from LLM")

            # Parse JSON response
            try:
                result = json.loads(response_content)
                self._log_parse_success(req_id, purpose, response_content)
                return result
            except json.JSONDecodeError:
                # Single-call parse recovery: strip fences and extract JSON object locally
                cleaned = self._strip_markdown_fences(response_content)
                extracted = self._extract_json_object(cleaned)
                self._log_parse_recovery(req_id, purpose, response_content, cleaned, extracted)
                if extracted:
                    try:
                        parsed = json.loads(extracted)
                        self._log_parse_success(req_id, purpose, extracted)
                        return parsed
                    except Exception:
                        pass
                raise LLMJsonParseFailedError(response_content)
            
        except asyncio.TimeoutError:
            raise LLMTimeoutError(self.timeout_ms)
        except openai.RateLimitError:
            if retry_count < 2:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.generate_response(messages, retry_count + 1)
            else:
                raise LLMError("Rate limit exceeded after retries")
        except openai.APIStatusError as e:
            if e.status_code >= 500 and retry_count < 2:
                await asyncio.sleep(1)
                return await self.generate_response(messages, retry_count + 1)
            else:
                raise LLMError(f"OpenAI API error: {str(e)}")
        except openai.APITimeoutError:
            if retry_count < 2:
                wait_time = min(15, 3 ** retry_count)  # Longer wait for timeouts
                print(f"⚠️ Request timeout, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self.generate_response(messages, retry_count + 1)
            else:
                raise LLMError("Request timeout after retries")
        except Exception as e:
            try:
                self.logger.error(f"LLM[{purpose}] {req_id} unexpected_error: {str(e)}")
            except Exception:
                pass
            raise LLMError(f"Unexpected error: {str(e)}")

    async def generate_text(self, messages: list, retry_count: int = 0, purpose: str = "default") -> str:
        """Generate freeform text (non-JSON) response with retry logic for chat mode."""
        if not self._connected:
            raise LLMError("OpenAI client not connected")
        
        # Mock mode - only use if client is None
        if self.client is None:
            print("⚠️  WARNING: Using MOCK response - OpenAI client not available")
            # Use the detailed mock response for chat mode
            mock = self._get_mock_response(messages)
            mock_text = mock.get("answer", {}).get("summary", "This is a mock assistant reply.")
            # Prepend warning to mock text response
            return f"⚠️ **MOCK RESPONSE** (Configure OpenAI API key for real predictions)\n\n{mock_text}"
        
        try:
            req_id = uuid.uuid4().hex[:8]
            self._log_request_start(req_id, purpose, messages)
            # Rely on SDK-level timeout configured on the client
            response = await self._make_text_request(messages, purpose, req_id)
            if response is None:
                raise LLMError("Received empty response from LLM")
            return response
        except asyncio.TimeoutError:
            raise LLMTimeoutError(self.timeout_ms)
        except openai.RateLimitError:
            if retry_count < 3:  # Increased retries
                wait_time = min(10, 2 ** retry_count + 2)  # Longer wait times
                print(f"⚠️ Rate limit hit, waiting {wait_time}s before retry {retry_count + 1}")
                await asyncio.sleep(wait_time)
                return await self.generate_text(messages, retry_count + 1)
            else:
                raise LLMError("Rate limit exceeded after retries")
        except openai.APIStatusError as e:
            if e.status_code >= 500 and retry_count < 2:
                await asyncio.sleep(1)
                return await self.generate_text(messages, retry_count + 1)
            else:
                raise LLMError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error: {str(e)}")
    
    def _get_mock_response(self, messages: list) -> Dict[str, Any]:
        """Generate a varied mock response for development."""
        import random
        import time
        
        # Extract question from messages
        question = ""
        for msg in messages:
            if msg.get("role") == "user":
                question = msg.get("content", "")
                break
        
        # Use timestamp and question hash for consistent but varied responses
        question_hash = hash(question) % 10
        time_factor = int(time.time()) % 5
        
        # Generate varied responses based on question content and time
        responses = {
            "career": [
                """**Astrological Analysis**: Your 10th house of career shows strong planetary influences. The current dasha period indicates professional growth opportunities. Jupiter's transit through your career house suggests recognition and advancement potential.

**Current Influences**: The planetary alignment shows Mercury enhancing communication skills, while Mars provides the drive needed for career advancement. Your current antardasha supports networking and skill development.

**Future Outlook**: The next 6 months show particularly strong indicators for career growth. Venus transit in the 10th house suggests financial rewards and professional recognition.

**Practical Guidance**: Focus on building professional relationships, consider additional training or certifications, and be prepared for unexpected opportunities.

**Key Astrological Factors**: 10th house lord placement, current dasha period, Jupiter transit, Mercury-Mars conjunction

**Timeline**: March-June 2024 (High confidence), September-December 2024 (Medium confidence)

**Astrological Sources**: Brihat Parashara Hora Shastra, Jataka Parijata""",
                
                """**Astrological Analysis**: Your career indicators show a period of transformation. The 10th house reveals both challenges and opportunities. Current planetary transits suggest a need for strategic planning and patience.

**Current Influences**: Saturn's influence indicates a time for building solid foundations rather than quick gains. The current dasha period emphasizes long-term career planning and skill development.

**Future Outlook**: The upcoming planetary periods suggest gradual but steady career growth. Focus on building expertise rather than seeking immediate advancement.

**Practical Guidance**: Invest in long-term skill development, build strong professional relationships, and maintain consistent effort toward your goals.

**Key Astrological Factors**: Saturn transit, 10th house aspects, current mahadasha, Rahu-Ketu axis influence

**Timeline**: April-August 2024 (Medium confidence), January-March 2025 (High confidence)

**Astrological Sources**: Brihat Jataka, Phaladeepika"""
            ],
            "relationships": [
                """**Astrological Analysis**: Your 7th house of marriage and partnerships shows interesting planetary configurations. The current dasha period indicates significant relationship developments.

**Current Influences**: Venus transit suggests harmony in existing relationships, while Jupiter's influence indicates growth and understanding. The planetary alignment favors commitment and partnership.

**Future Outlook**: The next 8 months show strong indicators for relationship stability and growth. For singles, this period suggests meeting significant partners.

**Practical Guidance**: Focus on communication and understanding in relationships. For those seeking partners, social activities and networking will be beneficial.

**Key Astrological Factors**: 7th house lord placement, Venus transit, Jupiter aspects, current dasha period

**Timeline**: May-September 2024 (High confidence), November 2024-February 2025 (Medium confidence)

**Astrological Sources**: Brihat Parashara Hora Shastra, Jataka Parijata""",
                
                """**Astrological Analysis**: Your relationship indicators show a period of emotional growth and understanding. The 7th house reveals both challenges and opportunities for partnership.

**Current Influences**: Mars influence suggests passion and drive in relationships, while Mercury enhances communication. The current planetary period emphasizes emotional intelligence.

**Future Outlook**: The upcoming transits suggest deepening of existing relationships and potential for new meaningful connections.

**Practical Guidance**: Focus on emotional communication, be open to compromise, and invest time in understanding your partner's needs.

**Key Astrological Factors**: Mars-Mercury conjunction, 7th house aspects, current antardasha, Venus placement

**Timeline**: June-October 2024 (Medium confidence), December 2024-April 2025 (High confidence)

**Astrological Sources**: Brihat Jataka, Phaladeepika"""
            ],
            "general": [
                """**Astrological Analysis**: Your birth chart reveals a complex interplay of planetary influences affecting multiple life areas. The current dasha period indicates significant personal growth and transformation.

**Current Influences**: Jupiter's transit suggests wisdom and growth opportunities, while Saturn provides structure and discipline. The planetary alignment favors personal development and spiritual growth.

**Future Outlook**: The next 12 months show a period of positive transformation. Focus on personal development, health, and spiritual practices.

**Practical Guidance**: Maintain a balanced approach to life, focus on personal growth, and be open to new learning opportunities.

**Key Astrological Factors**: Jupiter-Saturn aspects, current mahadasha, ascendant lord placement, planetary transits

**Timeline**: March-September 2024 (High confidence), October 2024-March 2025 (Medium confidence)

**Astrological Sources**: Brihat Parashara Hora Shastra, Jataka Parijata""",
                
                """**Astrological Analysis**: Your astrological profile shows a period of dynamic change and growth. The planetary configurations indicate both opportunities and challenges requiring careful navigation.

**Current Influences**: The current planetary transits suggest a need for adaptability and flexibility. Mercury's influence enhances communication and learning abilities.

**Future Outlook**: The upcoming planetary periods suggest gradual but meaningful progress in various life areas. Patience and persistence will be key.

**Practical Guidance**: Stay adaptable to changing circumstances, focus on continuous learning, and maintain positive relationships with others.

**Key Astrological Factors**: Mercury transit, planetary aspects, current dasha period, house lordships

**Timeline**: April-December 2024 (Medium confidence), January-June 2025 (High confidence)

**Astrological Sources**: Brihat Jataka, Phaladeepika"""
            ]
        }
        
        # Determine response category
        if any(word in question.lower() for word in ["job", "career", "work", "profession", "business"]):
            category = "career"
        elif any(word in question.lower() for word in ["marriage", "relationship", "love", "partner", "romance"]):
            category = "relationships"
        else:
            category = "general"
        
        # Select response based on question hash and time
        response_index = (question_hash + time_factor) % len(responses[category])
        selected_response = responses[category][response_index]
        
        return {
            "topic": category,
            "answer": {
                "summary": selected_response,
                "time_windows": [
                    {
                        "start": "2024-03-01",
                        "end": "2024-06-30",
                        "focus": f"{category} development",
                        "confidence": 0.75
                    }
                ],
                "actions": [
                    "Focus on personal growth and development",
                    "Maintain positive relationships",
                    "Stay open to new opportunities"
                ],
                "risks": [],
                "evidence": [
                    {
                        "calc_field": "transits.jupiter_house_from_lagna",
                        "value": 1,
                        "interpretation": "Jupiter transiting indicates growth opportunities"
                    }
                ],
                "confidence_topic": 0.75,
                "rationale": "This is a MOCK response for testing purposes only."
            },
            "confidence_overall": 0.72,
            "is_mock_response": True,
            "mock_warning": "⚠️ This is MOCK data for testing. Configure OPENAI_API_KEY for real predictions."
        }
    
    async def _make_request(self, messages: list, purpose: str, req_id: str) -> Optional[str]:
        """Make a single OpenAI request (JSON mode) with simple fallback.

        - Prefer Responses API for GPT-5/4.1 if available in the SDK.
        - Otherwise, use Chat Completions.
        """
        if not self.client:
            return None
            
        # Simplified: use Chat Completions only to avoid timeouts with Responses API

        # Fallback: Chat Completions (JSON mode)
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "seed": self.seed,
        }
        if self._supports_variable_temperature(self.model):
            params["temperature"] = self.temperature
        # Add token controls compatible with SDK and server
        token_kwargs = self._chat_token_params(self.model, self.max_tokens)
        params.update(token_kwargs)
        # Add GPT-5 specific parameters if using GPT-5
        gpt5_params = self._get_gpt5_parameters(self.model)
        if gpt5_params:
            params.update(gpt5_params)
        debug_keys = list(params.keys()) + (["extra_body.max_completion_tokens"] if "extra_body" in params and "max_completion_tokens" in params["extra_body"] else [])
        print(f"🔄 LLM[{purpose}] {req_id} Calling Chat Completions with: {debug_keys}")
        if settings.llm_streaming_enabled:
            params["stream"] = True
            stream = await self.client.chat.completions.create(**params)
            full_response_content = ""
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response_content += content
            return full_response_content
        else:
            response = await self.client.chat.completions.create(**params)
            content = None
            try:
                if response and response.choices and response.choices[0] and response.choices[0].message:
                    content = response.choices[0].message.content
                    print(f"✅ LLM[{purpose}] {req_id} Got content length: {len(content) if content else 0}")
            except Exception as e:
                print(f"❌ LLM[{purpose}] {req_id} Error extracting content: {str(e)}")
                content = None
            if content is None:
                # Try alternative fields
                try:
                    content = getattr(response.choices[0], "content", None)
                    print(f"✅ LLM[{purpose}] {req_id} Got content from alt field, length: {len(content) if content else 0}")
                except Exception as e2:
                    print(f"❌ LLM[{purpose}] {req_id} Alt field also failed: {str(e2)}")
                    content = None
            
            # Debug: print response structure if content is None or empty
            if not content:
                print(f"⚠️  LLM[{purpose}] {req_id} Response structure: {type(response)}")
                if response and hasattr(response, 'choices') and response.choices:
                    print(f"⚠️  LLM[{purpose}] {req_id} Choices[0] type: {type(response.choices[0])}")
                    choice = response.choices[0]
                    if hasattr(choice, 'message'):
                        msg = choice.message
                        print(f"⚠️  LLM[{purpose}] {req_id} Message type: {type(msg)}")
                        print(f"⚠️  LLM[{purpose}] {req_id} Message dir: {[a for a in dir(msg) if not a.startswith('_')]}")
                        print(f"⚠️  LLM[{purpose}] {req_id} Message.content: '{msg.content}'")
                        if hasattr(msg, 'refusal'):
                            print(f"⚠️  LLM[{purpose}] {req_id} Message.refusal: '{msg.refusal}'")
            
            return content

    async def _make_text_request(self, messages: list, purpose: str, req_id: str) -> Optional[str]:
        """Make a single OpenAI request (plain text) with simple fallback."""
        if not self.client:
            return None

        # Simplified: use Chat Completions only to avoid timeouts with Responses API

        # Fallback: Chat Completions (plain text)
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "seed": self.seed,
        }
        if self._supports_variable_temperature(self.model):
            params["temperature"] = self.temperature
        params.update(self._chat_token_params(self.model, self.max_tokens))
        # Add GPT-5 specific parameters if using GPT-5
        gpt5_params = self._get_gpt5_parameters(self.model)
        if gpt5_params:
            params.update(gpt5_params)
        debug_keys = list(params.keys()) + (["extra_body.max_completion_tokens"] if "extra_body" in params and "max_completion_tokens" in params["extra_body"] else [])
        print(f"🔄 LLM[{purpose}] {req_id} Calling Chat Completions with: {debug_keys}")
        if settings.llm_streaming_enabled:
            params["stream"] = True
            stream = await self.client.chat.completions.create(**params)
            full_response_content = ""
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    full_response_content += content
            return full_response_content
        else:
            response = await self.client.chat.completions.create(**params)
            content = None
            try:
                if response and response.choices and response.choices[0] and response.choices[0].message:
                    content = response.choices[0].message.content
            except Exception:
                content = None
            if content is None:
                try:
                    content = getattr(response.choices[0], "content", None)
                except Exception:
                    content = None
            return content

    def _use_responses_api(self, model: str) -> bool:
        """Return True if the model should use the Responses API.

        Responses API is preferred for newer model families (gpt-4o, gpt-4.1, gpt-5, o-series)
        where output token controls use `max_output_tokens` and richer modalities are supported.
        """
        if not model:
            return False
        lower = model.lower()
        return (
            lower.startswith("gpt-4o")
            or lower.startswith("gpt-4.1")
            or lower.startswith("gpt-5")
            or lower.startswith("o1")
            or lower.startswith("o3")
        )

    def _convert_messages_to_responses_input(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert chat-style messages to Responses API input format."""
        converted: List[Dict[str, Any]] = []
        for m in messages:
            role = m.get("role", "user")
            content_text = m.get("content", "")
            converted.append({
                "role": role,
                "content": [
                    {"type": "text", "text": content_text}
                ]
            })
        return converted

    def _chat_token_params(self, model: str, max_tokens: int) -> Dict[str, Any]:
        """Return token control kwargs for Chat Completions compatible with SDK and server.

        Some models require `max_completion_tokens` at the server, which may not be in the
        SDK method signature. Use `extra_body` to forward it safely. Otherwise use `max_tokens`.
        """
        if not model:
            return {"max_tokens": max_tokens}
        lower = model.lower()
        requires_completion_tokens = (
            lower.startswith("gpt-4o")
            or lower.startswith("gpt-4.1")
            or lower.startswith("gpt-5")
            or lower.startswith("o1")
            or lower.startswith("o3")
        )
        if requires_completion_tokens:
            return {"extra_body": {"max_completion_tokens": max_tokens}}
        return {"max_tokens": max_tokens}

    def _supports_variable_temperature(self, model: str) -> bool:
        """Return True if the model supports setting temperature != 1.

        Reasoning/o-series models and some newer families only allow default temperature.
        """
        if not model:
            return True
        lower = model.lower()
        if lower.startswith("o1") or lower.startswith("o3") or lower.startswith("gpt-4.1") or lower.startswith("gpt-5"):
            return False
        return True
    
    def _get_gpt5_parameters(self, model: str) -> Dict[str, Any]:
        """Get GPT-5 specific parameters if model is GPT-5.
        
        Note: GPT-5 may not support all parameters yet. Disable for now.
        """
        # Temporarily disabled - GPT-5 parameters may not be supported in current API version
        return {}
        
        # Original code (disabled):
        # if not model:
        #     return {}
        # lower = model.lower()
        # if lower.startswith("gpt-5"):
        #     return {
        #         "reasoning_effort": self.reasoning_effort,
        #         "verbosity": self.verbosity
        #     }
        # return {}

    def _strip_markdown_fences(self, text: str) -> str:
        """Remove common markdown fences and backticks around JSON blocks."""
        if not text:
            return text
        cleaned = text
        # Remove ```json ... ``` or ``` ... ``` fences
        if "```" in cleaned:
            parts = cleaned.split("```")
            # If there is a fenced block, prefer content inside the first block
            if len(parts) >= 3:
                inner = parts[1]
                # If it starts with a language tag like 'json\n', strip first line
                inner_lines = inner.splitlines()
                if inner_lines and inner_lines[0].strip().lower() in {"json", "javascript", "ts", "yaml"}:
                    inner = "\n".join(inner_lines[1:])
                return inner
        # Remove single backticks around inline code
        if cleaned.startswith("`") and cleaned.endswith("`") and len(cleaned) > 2:
            return cleaned[1:-1]
        return cleaned

    def _extract_json_object(self, text: str) -> Optional[str]:
        """Extract the first top-level JSON object substring from text.

        Uses a simple brace counter to find a well-formed {...} block.
        """
        if not text:
            return None
        start = text.find("{")
        if start == -1:
            return None
        brace_count = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "{":
                brace_count += 1
            elif ch == "}":
                brace_count -= 1
                if brace_count == 0:
                    candidate = text[start:i + 1]
                    return candidate
        return None

    def _log_request_start(self, req_id: str, purpose: str, messages: List[Dict[str, Any]]) -> None:
        try:
            sys_msg = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")
            user_msg = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
            self.logger.info(
                f"LLM[{purpose}] {req_id} start model={self.model} msgs=[sys:{len(sys_msg)} chars, user:{len(user_msg)} chars]"
            )
        except Exception:
            pass

    def _log_parse_success(self, req_id: str, purpose: str, text: str) -> None:
        try:
            snippet = (text or "")[:300].replace("\n", " ")
            self.logger.info(f"LLM[{purpose}] {req_id} parse_ok len={len(text or '')} snippet='{snippet}'")
        except Exception:
            pass

    def _log_parse_recovery(self, req_id: str, purpose: str, raw: str, cleaned: str, extracted: Optional[str]) -> None:
        try:
            raw_snip = (raw or "")[:200].replace("\n", " ")
            clean_snip = (cleaned or "")[:200].replace("\n", " ")
            ext_len = len(extracted) if extracted else 0
            self.logger.warning(
                f"LLM[{purpose}] {req_id} json_decode_error raw_len={len(raw or '')} cleaned_len={len(cleaned or '')} extracted_len={ext_len} raw_snip='{raw_snip}' cleaned_snip='{clean_snip}'"
            )
        except Exception:
            pass
    
    def create_system_message(self, content: str) -> Dict[str, str]:
        """Create system message."""
        return {"role": "system", "content": content}
    
    def create_user_message(self, content: str) -> Dict[str, str]:
        """Create user message."""
        return {"role": "user", "content": content}
    
    def create_messages(self, system_content: str, user_content: str) -> list:
        """Create messages list."""
        return [
            self.create_system_message(system_content),
            self.create_user_message(user_content)
        ]


# Global OpenAI client instance
openai_client = OpenAIClient()
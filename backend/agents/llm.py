"""
Composio Toolkit Radar – Shared LLM helper.
Uses google-genai SDK (official Gemini Python SDK).
"""
from typing import Optional, Type, TypeVar, Any
from pydantic import BaseModel
from tenacity import (
    retry, stop_after_attempt, wait_exponential_jitter,
    retry_if_exception, RetryError,
)

T = TypeVar("T", bound=BaseModel)


class DailyQuotaExhausted(Exception):
    """Raised when the Gemini free-tier daily quota is hit. Not retriable."""
    pass


def _is_retriable_error(exc: BaseException) -> bool:
    """Return True only for transient errors worth retrying (per-minute rate-limit, timeouts)."""
    msg = str(exc)
    # Daily quota – retrying is pointless
    if "PerDay" in msg:
        return False
    # Per-minute rate limits or server errors ARE retriable
    return True


def get_client():
    from backend.config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[LLM] Failed to create client: {e}")
        return None


@retry(
    wait=wait_exponential_jitter(initial=4, max=60),
    stop=stop_after_attempt(4),
    retry=retry_if_exception(_is_retriable_error),
    reraise=True,
)
async def ask_llm(prompt: str, schema: Optional[Type[T]] = None) -> Any:
    from backend.config import GEMINI_MODEL
    client = get_client()
    if not client:
        print("[LLM] No GEMINI_API_KEY set – returning None.")
        return None

    schema_name = schema.__name__ if schema else "free-text"
    print(f"[LLM] Calling {GEMINI_MODEL} (schema={schema_name}, prompt_len={len(prompt)})...")

    cfg: dict = {}
    if schema:
        cfg["response_schema"] = schema
        cfg["response_mime_type"] = "application/json"

    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=cfg if cfg else None,
        )
    except Exception as api_err:
        err_str = str(api_err)
        # Check for daily quota exhaustion – fail fast, don't retry
        if "PerDay" in err_str:
            print(f"[LLM] FATAL: Daily API quota exhausted. Cannot retry.")
            print(f"[LLM]   Detail: {err_str[:200]}")
            raise DailyQuotaExhausted(err_str) from api_err
        # Log and let tenacity decide whether to retry
        print(f"[LLM] API error (will retry if transient): {err_str[:200]}")
        raise

    raw_text = response.text
    if not raw_text or not raw_text.strip():
        print(f"[LLM] WARNING: Empty response from model for schema={schema_name}")
        return None

    text = raw_text.strip()
    print(f"[LLM] SUCCESS: Got {len(text)} chars for schema={schema_name}")

    if schema:
        try:
            parsed = schema.model_validate_json(text)
            return parsed
        except Exception as parse_err:
            print(f"[LLM] JSON PARSE ERROR for schema={schema_name}: {parse_err}")
            print(f"[LLM]   Raw response (first 300 chars): {text[:300]}")
            return None
    return text


async def safe_ask_llm(prompt: str, schema: Optional[Type[T]] = None, label: str = "unknown") -> tuple[Any, Optional[str]]:
    """Wrapper that never raises – returns (result, error_msg)."""
    try:
        result = await ask_llm(prompt, schema)
        return result, None
    except DailyQuotaExhausted:
        msg = "Gemini daily quota exhausted"
        print(f"[{label}] FAILED: {msg}")
        return None, msg
    except RetryError as e:
        msg = f"Failed after all retries: {e.last_attempt.exception()}"
        print(f"[{label}] {msg}")
        return None, msg
    except Exception as e:
        msg = f"Unexpected error: {type(e).__name__}: {e}"
        print(f"[{label}] {msg}")
        return None, msg

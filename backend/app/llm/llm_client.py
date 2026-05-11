

import json
import re
import os
from pathlib import Path
from datetime import datetime
from groq import AsyncGroq
from dotenv import load_dotenv
import google.generativeai as genai

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =============================================================================
# CONFIG - GROQ
# =============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY is not set in your .env file.\n"
        "Get a free key at https://console.groq.com"
    )

# =============================================================================
# CONFIG - GEMINI
# =============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")

if not GEMINI_API_KEY:
    raise EnvironmentError(
        "GEMINI_API_KEY is not set in your .env file.\n"
        "Get a free key at https://ai.google.dev"
    )

# =============================================================================
# CLIENT INSTANCES
# =============================================================================

groq_client = AsyncGroq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(GEMINI_MODEL)

# For backwards compatibility
client = groq_client


# =============================================================================
# HELPER — Strip markdown fences from LLM response
# LLMs sometimes wrap JSON in ```json ... ``` even when told not to
# =============================================================================

def clean_llm_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# =============================================================================
# HELPER — Parse JSON safely
# =============================================================================

def parse_json_response(text: str) -> dict:
    cleaned = clean_llm_response(text)
    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("LLM JSON response must be an object.")
        return parsed
    except json.JSONDecodeError:
        # Some model responses contain extra text or multiple JSON objects.
        # Recover by decoding the first JSON value from the first brace/bracket.
        first_object_start = min(
            [idx for idx in [cleaned.find("{"), cleaned.find("[")] if idx != -1],
            default=-1,
        )
        if first_object_start != -1:
            decoder = json.JSONDecoder()
            try:
                parsed, _ = decoder.raw_decode(cleaned[first_object_start:])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"LLM returned invalid JSON.\n"
            f"Raw response (first 500 chars):\n{cleaned[:500]}"
        )


# =============================================================================
# CORE FUNCTION — Send prompt, get JSON back (with provider routing)
# Used by all extraction modules
# =============================================================================

async def ask_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 512,
    provider: str = "groq"
) -> dict:
    """
    Sends a prompt to Groq or Gemini and returns parsed JSON.

    Args:
        system_prompt : Role + output format instructions
        user_prompt   : CV text or data to analyze
        temperature   : 0.1 for extraction, 0.5 for summaries
        max_tokens    : Max response length
        provider      : "groq" or "gemini"

    Returns:
        dict: Parsed JSON from LLM
    """
    if provider.lower() == "gemini":
        return await _ask_gemini_json(system_prompt, user_prompt, temperature, max_tokens)
    else:
        return await _ask_groq_json(system_prompt, user_prompt, temperature, max_tokens)


async def _ask_groq_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 512
) -> dict:
    """Send prompt to Groq and return parsed JSON."""
    try:
        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        raw_text = response.choices[0].message.content
        return parse_json_response(raw_text)

    except ValueError:
        raise

    except Exception as e:
        error_text = str(e)
        if "Request too large" in error_text or "rate_limit_exceeded" in error_text or "tokens per minute" in error_text:
            raise Exception(
                "Groq request exceeded token limits (TPM/context). "
                "Reduce input size, lower max_tokens, or use chunked analysis. "
                f"Original error: {error_text}"
            )
        raise Exception(
            f"Groq API call failed.\n"
            f"Error: {error_text}"
        )


async def _ask_gemini_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 512
) -> dict:
    """Send prompt to Gemini and return parsed JSON."""
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = gemini_model.generate_content(
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        raw_text = response.text
        return parse_json_response(raw_text)

    except ValueError:
        raise

    except Exception as e:
        error_text = str(e)
        if "rate_limit" in error_text.lower() or "quota" in error_text.lower():
            raise Exception(
                "Gemini request exceeded rate limits. "
                "Try again in a few moments or reduce request size. "
                f"Original error: {error_text}"
            )
        raise Exception(
            f"Gemini API call failed.\n"
            f"Error: {error_text}"
        )


# =============================================================================
# CORE FUNCTION — Send prompt, get plain text back (with provider routing)
# Used for summaries, emails, narrative outputs
# =============================================================================

async def ask_llm_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 512,
    provider: str = "groq"
) -> str:
    """
    Same as ask_llm() but returns plain text.
    Use for candidate summaries and email drafting.
    
    Args:
        provider : "groq" or "gemini"
    """
    if provider.lower() == "gemini":
        return await _ask_gemini_text(system_prompt, user_prompt, temperature, max_tokens)
    else:
        return await _ask_groq_text(system_prompt, user_prompt, temperature, max_tokens)


async def _ask_groq_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 512
) -> str:
    """Send prompt to Groq and return plain text."""
    try:
        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        error_text = str(e)
        if "Request too large" in error_text or "rate_limit_exceeded" in error_text or "tokens per minute" in error_text:
            raise Exception(
                "Groq request exceeded token limits (TPM/context). "
                "Reduce input size, lower max_tokens, or use chunked analysis. "
                f"Original error: {error_text}"
            )
        raise Exception(
            f"Groq API call failed.\n"
            f"Error: {error_text}"
        )


async def _ask_gemini_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5,
    max_tokens: int = 512
) -> str:
    """Send prompt to Gemini and return plain text."""
    try:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = gemini_model.generate_content(
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text.strip()

    except Exception as e:
        error_text = str(e)
        if "rate_limit" in error_text.lower() or "quota" in error_text.lower():
            raise Exception(
                "Gemini request exceeded rate limits. "
                "Try again in a few moments or reduce request size. "
                f"Original error: {error_text}"
            )
        raise Exception(
            f"Gemini API call failed.\n"
            f"Error: {error_text}"
        )


# =============================================================================
# HEALTH CHECK — Verify API keys and connections
# =============================================================================

async def check_groq_health() -> dict:
    try:
        await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Reply with just the word: ok"}],
            max_tokens=5
        )
        return {"groq": "connected", "model": GROQ_MODEL, "status": "ok"}
    except Exception as e:
        return {"groq": "unreachable", "model": GROQ_MODEL, "status": "error", "detail": str(e)}


def check_gemini_health() -> dict:
    """Synchronous health check for Gemini."""
    try:
        response = gemini_model.generate_content("Reply with just the word: ok")
        return {"gemini": "connected", "model": GEMINI_MODEL, "status": "ok"}
    except Exception as e:
        return {"gemini": "unreachable", "model": GEMINI_MODEL, "status": "error", "detail": str(e)}


async def check_all_llm_health() -> dict:
    """Check health of all LLM providers."""
    groq_status = await check_groq_health()
    gemini_status = check_gemini_health()
    return {
        "timestamp": str(datetime.now()),
        "providers": {
            **groq_status,
            **gemini_status
        }
    }
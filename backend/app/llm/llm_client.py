

import json
import re
import os
from pathlib import Path
from groq import AsyncGroq
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =============================================================================
# CONFIG
# =============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY is not set in your .env file.\n"
        "Get a free key at https://console.groq.com"
    )

# =============================================================================
# GROQ CLIENT INSTANCE
# =============================================================================

client = AsyncGroq(api_key=GROQ_API_KEY)


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
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON.\n"
            f"Error: {e}\n"
            f"Raw response (first 500 chars):\n{cleaned[:500]}"
        )


# =============================================================================
# CORE FUNCTION — Send prompt, get JSON back
# Used by all extraction modules
# =============================================================================

async def ask_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1
) -> dict:
    """
    Sends a prompt to Groq and returns parsed JSON.

    Args:
        system_prompt : Role + output format instructions
        user_prompt   : CV text or data to analyze
        temperature   : 0.1 for extraction, 0.5 for summaries

    Returns:
        dict: Parsed JSON from LLM
    """
    try:
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=4096
        )
        raw_text = response.choices[0].message.content
        return parse_json_response(raw_text)

    except ValueError:
        raise

    except Exception as e:
        raise Exception(
            f"Groq API call failed.\n"
            f"Check your GROQ_API_KEY in .env\n"
            f"Error: {str(e)}"
        )


# =============================================================================
# CORE FUNCTION — Send prompt, get plain text back
# Used for summaries, emails, narrative outputs
# =============================================================================

async def ask_llm_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.5
) -> str:
    """
    Same as ask_llm() but returns plain text.
    Use for candidate summaries and email drafting.
    """
    try:
        response = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        raise Exception(
            f"Groq API call failed.\n"
            f"Check your GROQ_API_KEY in .env\n"
            f"Error: {str(e)}"
        )


# =============================================================================
# HEALTH CHECK — Verify API key and connection
# =============================================================================

async def check_groq_health() -> dict:
    try:
        await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Reply with just the word: ok"}],
            max_tokens=5
        )
        return {"groq": "connected", "model": GROQ_MODEL, "status": "ok"}
    except Exception as e:
        return {"groq": "unreachable", "model": GROQ_MODEL, "status": "error", "detail": str(e)}
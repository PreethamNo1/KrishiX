import json
from typing import Dict, Any
from groq import Groq
from app.config import settings


def get_groq_client() -> Groq:
    """Initialize and return the Groq client."""
    return Groq(api_key=settings.GROQ_API_KEY)


def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extract agricultural entities (crop, qty, location) from English text using Groq LLM.
    
    :param text: Translated text from farmer audio.
    :return: Dictionary containing 'crop', 'qty', and 'location'.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured in .env")

    prompt = f"""
Extract the crop name, quantity (with units), and location from the following text.
Return ONLY a valid JSON object with the exact keys: 'crop', 'qty', 'location'.
If a value is missing, return "Unknown".

Text: "{text}"
"""
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        # Ensure required keys exist
        return {
            "crop": data.get("crop", "Unknown"),
            "qty": data.get("qty", "Unknown"),
            "location": data.get("location", "Unknown"),
        }
    except json.JSONDecodeError as e:
        raise ValueError(f"Groq returned invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Groq entity extraction failed: {e}")


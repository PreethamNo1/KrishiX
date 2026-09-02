from sarvamai import SarvamAI
from app.config import settings


def get_sarvam_client() -> SarvamAI:
    """Initialize and return the Sarvam AI client."""
    return SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)


def transcribe_and_translate(file_path: str, language_code: str = None) -> str:
    """
    Transcribes audio and translates it directly to English using Sarvam AI.
    
    :param file_path: Path to the local audio file.
    :param language_code: Source audio language (default: settings.SARVAM_DEFAULT_LANGUAGE).
    :return: Translated English text.
    """
    if not settings.SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not configured in .env")

    client = get_sarvam_client()
    lang = language_code or settings.SARVAM_DEFAULT_LANGUAGE

    with open(file_path, "rb") as audio_file:
        response = client.speech_to_text.transcribe(
            file=audio_file,
            model=settings.SARVAM_MODEL,
            mode="translate",
            language_code=lang,
        )

    return getattr(response, "transcript", str(response))


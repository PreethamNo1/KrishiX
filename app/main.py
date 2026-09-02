import os
import uuid
import shutil
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import fetch_all_buyers
from app.services.speech import transcribe_and_translate
from app.services.llm import extract_entities
from app.services.geo import geocode_location, find_buyers_in_radius
from app.services.notifier import send_buyer_alerts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("krishix")

app = FastAPI(
    title="KrishiX API",
    version="1.0.0",
    description="AI-driven voice-first agricultural matchmaking connecting rural farmers to buyers."
)

# Enable CORS for local client development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint to verify service status."""
    return {"status": "ok", "service": "KrishiX API", "version": "1.0.0"}


@app.post("/process-voice")
async def process_farmer_voice(
    file: UploadFile = File(...),
    farmer_phone: str = Form("+919999999999")
):
    """
    Process farmer voice recording:
    1. Transcribe and translate voice audio (Kannada to English) via Sarvam AI.
    2. Extract crop, quantity, and location entities via Groq LLM.
    3. Geocode farmer location and filter buyers within matched radius.
    4. Dispatch SMS alerts to nearby buyers via Twilio.
    """
    temp_id = uuid.uuid4().hex[:8]
    safe_filename = os.path.basename(file.filename or "audio.ogg")
    temp_file_path = f"temp_{temp_id}_{safe_filename}"

    try:
        # Save incoming audio stream to temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Step 1: Sarvam AI - Audio Transcription & Translation
        try:
            english_text = transcribe_and_translate(temp_file_path)
        except Exception as e:
            logger.error(f"Sarvam API transcription failed: {e}")
            return {"error": f"Sarvam API failed: {str(e)}"}

        # Step 2: Groq LLM - Entity Extraction
        try:
            entities = extract_entities(english_text)
        except Exception as e:
            logger.error(f"Groq entity extraction failed: {e}")
            return {"error": f"Groq entity extraction failed: {str(e)}"}

        farmer_location = entities.get("location", "Unknown")

        # Step 3: Geocoding & Proximity Radius Matching
        farmer_coords = geocode_location(farmer_location)
        if not farmer_coords:
            logger.warning(f"Could not geocode location: {farmer_location}")
            return {"error": f"Could not geocode location: {farmer_location}"}

        # Query buyers from MySQL database
        try:
            buyers = fetch_all_buyers()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            return {"error": f"Database query failed: {str(e)}"}

        matched_buyers = find_buyers_in_radius(farmer_coords, buyers)

        # Step 4: Dispatch Outbound Alerts via Twilio
        alerts_sent = send_buyer_alerts(
            matched_buyers=matched_buyers,
            crop=entities.get("crop", "produce"),
            qty=entities.get("qty", "quantity"),
            location=farmer_location,
            farmer_phone=farmer_phone
        )

        return {
            "status": "success",
            "translation": english_text,
            "extracted_data": entities,
            "buyers_alerted": alerts_sent,
            "matched_buyers_count": len(matched_buyers)
        }

    finally:
        # Guaranteed cleanup of temporary audio file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as e:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)


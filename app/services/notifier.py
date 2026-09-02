import logging
from typing import List, Dict, Any
from twilio.rest import Client
from app.config import settings

logger = logging.getLogger(__name__)


def get_twilio_client() -> Client:
    """Initialize and return the Twilio REST client."""
    return Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)


def send_buyer_alerts(
    matched_buyers: List[Dict[str, Any]],
    crop: str,
    qty: str,
    location: str,
    farmer_phone: str
) -> int:
    """
    Dispatches outbound SMS alerts to matched buyers via Twilio.
    
    :return: Number of alerts successfully dispatched.
    """
    if not settings.TWILIO_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
        logger.warning("Twilio credentials not configured. Skipping SMS dispatch.")
        return 0

    client = get_twilio_client()
    alerts_sent = 0

    for buyer in matched_buyers:
        phone = buyer.get("phone")
        dist = buyer.get("distance", "N/A")
        msg_body = (
            f"AGRI ALERT: Fresh {crop} ({qty}) "
            f"available near {location} ({dist}km away). "
            f"Call Farmer: {farmer_phone}"
        )
        try:
            client.messages.create(
                body=msg_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone
            )
            alerts_sent += 1
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")

    return alerts_sent


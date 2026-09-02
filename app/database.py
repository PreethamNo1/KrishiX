import mysql.connector
from typing import List, Dict, Any
from app.config import settings


def get_db_connection():
    """Create and return a new MySQL database connection."""
    return mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        connect_timeout=10
    )


def fetch_all_buyers() -> List[Dict[str, Any]]:
    """
    Fetch all active buyers from the database.
    Returns a list of dictionaries with keys: name, phone, lat, lon.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT name, phone, lat, lon FROM buyers")
            return cursor.fetchall()
        finally:
            cursor.close()
    finally:
        conn.close()


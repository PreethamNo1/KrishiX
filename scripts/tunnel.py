import os
import sys
import ngrok

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings


def start_tunnel():
    """Start ngrok reverse proxy tunnel for the FastAPI backend."""
    target_addr = f"localhost:{settings.API_PORT}"
    kwargs = {
        "addr": target_addr,
        "authtoken_from_env": True,
    }

    if settings.NGROK_AUTHTOKEN:
        kwargs["authtoken"] = settings.NGROK_AUTHTOKEN

    if settings.NGROK_DOMAIN:
        kwargs["domain"] = settings.NGROK_DOMAIN

    print(f"Starting Ngrok tunnel to {target_addr}...")
    try:
        forwarder = ngrok.forward(**kwargs)
        print(f"\n=======================================================")
        print(f"  KrishiX Public URL: {forwarder.url()}")
        print(f"=======================================================\n")
        print("Press Ctrl+C to terminate tunnel.")
        
        # Keep process alive
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Ngrok tunnel...")
    except Exception as e:
        print(f"Failed to establish Ngrok tunnel: {e}")


if __name__ == "__main__":
    start_tunnel()


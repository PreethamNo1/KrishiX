import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import requests

# Ensure project root is in sys.path when running client directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from app.config import settings
    DEFAULT_API_URL = settings.API_URL
except Exception:
    DEFAULT_API_URL = "http://127.0.0.1:8000/process-voice"


class VoicemailUploaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KrishiX - Voice Marketplace Client")
        self.root.geometry("540x520")
        self.root.resizable(True, True)
        
        self.file_path = None
        self.api_url = DEFAULT_API_URL

        self._build_ui()

    def _build_ui(self):
        # --- File picker section ---
        tk.Label(self.root, text="WhatsApp Voicemail Audio File", font=("Arial", 11, "bold")).pack(pady=(15, 5))

        self.file_label = tk.Label(self.root, text="No file selected", fg="gray", wraplength=480)
        self.file_label.pack()

        tk.Button(self.root, text="Browse Audio File", command=self.browse_file, width=20).pack(pady=5)

        # --- Farmer phone number section ---
        tk.Label(self.root, text="Farmer's Phone Number (with country code)", font=("Arial", 11, "bold")).pack(pady=(15, 5))

        self.phone_entry = tk.Entry(self.root, width=30, justify="center", font=("Arial", 10))
        self.phone_entry.insert(0, "+919999999999")
        self.phone_entry.pack()

        # --- Submit button ---
        self.submit_btn = tk.Button(
            self.root, text="Upload & Match Buyers", bg="#E8701A", fg="white",
            font=("Arial", 11, "bold"), command=self.start_upload, height=2, width=25
        )
        self.submit_btn.pack(pady=20)

        # --- Status / result log ---
        tk.Label(self.root, text="Status & Execution Log:", font=("Arial", 10, "bold")).pack(anchor="w", padx=20)
        self.log_box = scrolledtext.ScrolledText(self.root, height=14, width=65, state="disabled", font=("Consolas", 9))
        self.log_box.pack(padx=20, pady=(5, 15), fill=tk.BOTH, expand=True)

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Select WhatsApp Voicemail",
            filetypes=[
                ("Audio files", "*.ogg *.opus *.mp3 *.wav *.m4a *.aac"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.file_path = path
            self.file_label.config(text=os.path.basename(path), fg="black")
            self.log(f"Selected file: {path}")

    def log(self, text: str):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def start_upload(self):
        if not self.file_path:
            messagebox.showwarning("No File Selected", "Please select a voicemail audio file first.")
            return

        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showwarning("Missing Phone", "Please enter the farmer's phone number.")
            return

        # Disable button while request runs to prevent duplicate submissions
        self.submit_btn.config(state="disabled", text="Processing Voice...")
        self.log(f"\n[Starting Upload] {os.path.basename(self.file_path)}...")

        # Run network request in background thread to avoid freezing GUI
        thread = threading.Thread(target=self.upload_file, args=(self.file_path, phone), daemon=True)
        thread.start()

    def upload_file(self, path: str, phone: str):
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f)}
                data = {"farmer_phone": phone}
                response = requests.post(self.api_url, files=files, data=data, timeout=120)

            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    self.log("\n[BACKEND ERROR]")
                    self.log(result["error"])
                else:
                    self.log("\n[SUCCESS]")
                    self.log(f"Translation: {result.get('translation')}")
                    self.log(f"Extracted: {result.get('extracted_data')}")
                    self.log(f"Buyers Alerted: {result.get('buyers_alerted')}")
                    if "matched_buyers_count" in result:
                        self.log(f"Total Matched: {result.get('matched_buyers_count')}")
            else:
                self.log(f"\n[SERVER ERROR {response.status_code}]")
                self.log(response.text)

        except requests.exceptions.ConnectionError:
            self.log("\n[CONNECTION ERROR]")
            self.log(f"Could not connect to {self.api_url}. Make sure the FastAPI server is running.")
        except Exception as e:
            self.log(f"\n[ERROR] {str(e)}")
        finally:
            # Re-enable button on main thread
            self.root.after(0, lambda: self.submit_btn.config(state="normal", text="Upload & Match Buyers"))


if __name__ == "__main__":
    root = tk.Tk()
    app = VoicemailUploaderApp(root)
    root.mainloop()


# KrishiX — Feature Testing Guide & Purpose

This document explains **what each current feature does in the codebase** and **how to test it** properly. It is the authoritative reference for validating your changes before opening a PR.

> 📁 Related docs: see the [README](../README.md) for architecture, setup, and API reference.

---

## Table of Contents

1. [Feature Purpose Overview](#1-feature-purpose-overview)
2. [Pre-Test Setup](#2-pre-test-setup)
3. [Feature 1: Voice Transcription & Translation](#3-feature-1-voice-transcription--translation)
4. [Feature 2: Intent Classification & Routing](#4-feature-2-intent-classification--routing)
5. [Feature 3: Sell-Offer Pipeline (Buyer Matching + SMS)](#5-feature-3-sell-offer-pipeline)
6. [Feature 4: Agricultural Q&A Agent Orchestration](#6-feature-4-agricultural-qa-agent-orchestration)
7. [Feature 5: Desktop GUI Client](#7-feature-5-desktop-gui-client)
8. [Feature 6: Ngrok Webhook Tunnel](#8-feature-6-ngrok-webhook-tunnel)
9. [Running Automated Tests](#9-running-automated-tests)
10. [End-to-End Test Checklist](#10-end-to-end-test-checklist)

---

## 1. Feature Purpose Overview

| # | Feature | Modules | Purpose |
|---|---------|---------|---------|
| 1 | Voice transcription & translation | `app/services/speech.py` | Convert Kannada voice audio into English text so downstream agents can process it. |
| 2 | Intent classification & routing | `app/agents/classifier.py`, `app/agents/orchestrator.py` | Decide whether a message is a **sell offer** or an **agricultural question**, then route it to the correct pipeline. |
| 3 | Sell-offer pipeline | `app/services/llm.py`, `geo.py`, `database.py`, `notifier.py` | Extract crop/qty/location, geocode, find nearby buyers within a radius, and alert them via SMS. |
| 4 | Agricultural Q&A agents | `app/agents/qa.py`, `app/agents/utils.py` | Answer farmer questions by researching the web + free literature in parallel and synthesizing a single paragraph. |
| 5 | Desktop GUI client | `client/gui.py` | Provide coordinators a simple way to upload voicemails and view results. |
| 6 | Ngrok webhook tunnel | `scripts/tunnel.py` | Expose the local API publicly for WhatsApp/Twilio webhooks. |

---

## 2. Pre-Test Setup

Install dependencies and configure the environment **before** testing.

```bash
cd KrishiX
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt

cp env.example .env              # then edit .env with your real keys
```

Add these to `.env` (copy values from your accounts):

```ini
SARVAM_API_KEY=...
GROQ_API_KEY=...
TWILIO_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
OPENROUTER_API_KEY=...
DB_PASSWORD=...
```

Set up the database:

```bash
mysql -u root -p < scripts/schema.sql
```

> ⚠️ **Never commit `.env`.** It is gitignored.

---

## 3. Feature 1: Voice Transcription & Translation

**Purpose:** `transcribe_and_translate()` in `app/services/speech.py` uses Sarvam AI's Saaras v4 model to convert a Kannada voice recording into English text. This text feeds the classifier.

**How to test:**

1. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Upload a **valid Kannada audio file** (`.ogg`/`.wav`/`.m4a`):
   ```bash
   curl -F "file=@/path/to/kannada_message.ogg" \
        -F "farmer_phone=+919876543210" \
        http://127.0.0.1:8000/process-voice
   ```
3. **Expected:** `"translation"` field contains the English transcript.

**Failure tests:**
- No `SARVAM_API_KEY` → expect `{"error": "Sarvam API failed: ..."}`.
- Corrupt/garbage audio → expect a graceful `{"error": ...}` (Sarvam returns 400; app catches it).

**Note:** A fake/empty audio file will cause Sarvam to reject it — that is an expected error-path, not a bug.

---

## 4. Feature 2: Intent Classification & Routing

**Purpose:** `classify_intent()` (`app/agents/classifier.py`) uses an OpenRouter LLM (via LangChain) to classify the transcribed text into `offer`, `question`, or `unknown`. `route_message()` (`app/agents/orchestrator.py`) returns the decision and, for questions, the synthesized answer.

**How to test:**

1. Ensure `OPENROUTER_API_KEY` is set in `.env`.
2. Test offers route to the buyer pipeline and questions route to the Q&A agents using `curl` with real audio (see Features 3 and 4 for expected responses).

**Direct (unit-level) test of routing:**
```bash
python - <<'PY'
from app.agents.orchestrator import route_message
print(route_message("I want to sell 5 quintals of tomato near Mandya"))
print(route_message("How do I control tomato blight?"))
PY
```
- First should show `intent == 'offer'` (no `answer`).
- Second should show `intent == 'question'` with an `answer`.

**Graceful-degradation test:** With **no** `OPENROUTER_API_KEY`, `route_message()` must **not crash** — it should return `intent == 'unknown'` and a `reason` describing the error.

---

## 5. Feature 3: Sell-Offer Pipeline

**Purpose:** For `offer`/`unknown` intents, `app/services/` extract entities (Groq), geocode (Geopy), query buyers (MySQL), filter by radius, and dispatch SMS (Twilio).

**How to test:**

1. `OPENROUTER_API_KEY`, `GROQ_API_KEY`, and `TWILIO_*` must be set.
2. Upload Kannada audio stating a sale, e.g. *"I have 5 quintals of tomatoes in Mandya"*.
3. **Expected response:**
   ```json
   {
     "status": "success",
     "type": "offer",
     "confidence": 0.98,
     "extracted_data": {"crop": "tomato", "qty": "5 quintals", "location": "Mandya"},
     "matched_buyers_count": 2,
     "buyers_alerted": 2
   }
   ```
4. Verify in **MySQL** that the seed buyers load:
   ```bash
   mysql -u root -p -e "SELECT name, phone, lat, lon FROM agrimatch.buyers;"
   ```
5. Verify **geo matching** directly:
   ```bash
   python - <<'PY'
   from app.database import fetch_all_buyers
   from app.services.geo import find_buyers_in_radius
   matches = find_buyers_in_radius((12.9716, 77.5946), fetch_all_buyers(), radius_km=50)
   print(len(matches), [m['name'] for m in matches])
   PY
   ```

**Failure/edge tests:**
- Un-geocodable location → `{"error": "Could not geocode location: ..."}`.
- Twilio creds missing → `buyers_alerted: 0` with a warning log (SMS disabled gracefully).
- Missing `file` field → HTTP 422 (FastAPI validation).

---

## 6. Feature 4: Agricultural Q&A Agent Orchestration

**Purpose:** For `question` intents, the LangGraph workflow (`app/agents/qa.py`) runs:
1. **Researcher** → produces a research brief.
2. **Web agent** (DuckDuckGo, no key) + **Literature agent** (free knowledge) → gather information **in parallel**.
3. **Synthesizer** → merges both into **one paragraph**.

**Prerequisites:** `OPENROUTER_API_KEY` set. Web search needs DuckDuckGo (no key).

**How to test the full flow via `/process-voice`:**
1. Upload Kannada audio with a **question**, e.g. *"Tomato blight aadre enu madabeku?"*.
2. **Expected response:**
   ```json
   {
     "status": "success",
     "type": "question",
     "intent": "question",
     "confidence": 0.97,
     "answer": "<single synthesized paragraph>"
   }
   ```

**How to test the graph directly (no HTTP):**
```bash
python - <<'PY'
from app.agents.qa import answer_agricultural_question
print(answer_agricultural_question("How do I control tomato blight?"))
PY
```
- Expect one coherent paragraph, not bullets.

**Verify graph topology** (without network/keys) using a mocked LLM — confirm the graph contains all 5 nodes (`researcher`, `web_agent`, `literature_agent`, `synthesizer`).

**Failure/edge tests:**
- No `OPENROUTER_API_KEY` → the `/process-voice` question branch returns `answer_error` (or falls back to `unknown` in the classifier) rather than crashing.

---

## 7. Feature 5: Desktop GUI Client

**Purpose:** `client/gui.py` gives coordinators a GUI to pick an audio file, enter the farmer phone, upload, and view the transcription/result.

**How to test:**
```bash
python client/gui.py
```
1. Click **Browse Audio File** and select a voice message.
2. Enter a phone number.
3. Click **Upload & Match Buyers** (or equivalent button).
4. Confirm the log shows a successful response (either an offer match or a Q&A answer).

---

## 8. Feature 6: Ngrok Webhook Tunnel

**Purpose:** `scripts/tunnel.py` exposes the local API at a public URL for WhatsApp/Twilio webhooks.

**How to test:**
```bash
python scripts/tunnel.py
```
- Confirm the printed public URL routes to your local `/process-voice`.
- Send a test request through the public URL (requires a valid audio file + keys).

---

## 9. Running Automated Tests

```bash
python -m unittest discover -s tests -v
```
Current tests validate:
- Settings load correctly (`test_settings_loaded`).
- FastAPI routes `/health` and `/process-voice` are registered (`test_app_routes`).

**Expected:** `Ran 2 tests ... OK`.

> **Coverage note:** There are no automated tests yet for the services/agents. When you add some, place them under `tests/` and follow the existing `unittest` pattern.

---

## 10. End-to-End Test Checklist

Use this checklist before merging.

### Offer flow
- [ ] Dependencies installed, `.env` fully populated.
- [ ] DB schema + 6 seed buyers loaded.
- [ ] `/health` returns `200 OK`.
- [ ] Kannada **sale** audio → `type: "offer"`, `matched_buyers_count >= 1`, `buyers_alerted >= 1`.
- [ ] SMS actually delivered (check Twilio console/logs).

### Question flow
- [ ] `OPENROUTER_API_KEY` set.
- [ ] Kannada **question** audio → `type: "question"` with a synthesized `answer`.
- [ ] Answer is a single, coherent paragraph.

### Error / robustness
- [ ] No `OPENROUTER_API_KEY` → graceful degradation (no crash).
- [ ] No Twilio creds → `buyers_alerted: 0` (no crash).
- [ ] Un-geocodable location → clean error.
- [ ] Missing `file` field → HTTP 422.
- [ ] Temporary `temp_*` files cleaned up after each request.
- [ ] `python -m unittest discover -s tests -v` → `OK`.

---

## Configuration Reference (new fields)

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | *(empty)* | Authenticates the Q&A agent orchestration. |
| `OR_AGENT_MODEL` | `nvidia/nemotron-3-ultra-550b-a55b:free` | OpenRouter model used by all agents/classifier. |
| `OR_MAX_RESULTS` | `4` | Max web search results the web agent reviews. |

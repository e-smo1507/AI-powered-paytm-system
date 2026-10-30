# Paytm Voice Assistant (Build for India AI Hackathon, Track 2)

> **Voice-first loans + insurance journeys that talk back.**  
> Explain / Decide / Guide / Hand over · Spoken Hindi + Indian English · Deterministic Financial Rules Engine · RBI Digital Lending KFS · Iconic Paytm Soundbox Chime · Real-Time Two-Way Human Agent Desk.

---

## 🌟 Standout Features Added

1. **🎙️ Bulletproof Voice Engine with Live Audio Waveform:**
   - Real-time Web Audio API frequency analyser renders dynamic pulsing visualizer bars while listening.
   - Comprehensive error recovery (friendly permission guidance, network timeout recovery, clean toggle on/off).
   - Instant "Quick Voice" prompt chips allowing seamless one-click demonstration across all environments.
2. **🔔 Iconic Paytm Soundbox Audio Experience:**
   - Dual-tone synthesizer chime (740Hz $\to$ 1108Hz) on loan sanction and policy issuance, followed by official spoken voice receipt.
3. **📄 Official RBI Key Fact Statement (KFS) Modal & PDF Export:**
   - Interactive disclosure meeting RBI digital lending guidelines with APR, itemized fee/GST breakdown, 6-month amortisation preview table, statutory 3-day cooling-off notice, and printable layout.
4. **⚡ Live Interactive Re-Pricing Pills:**
   - Instant re-pricing buttons directly inside the offer card (`12m`, `24m`, `36m`, `48m`) demonstrating instantaneous deterministic calculation.
5. **👥 Two-Way Interactive Human Agent Desk (`/agent`):**
   - Real-time agent console allowing human representatives to send live messages directly into the customer's chat and authorize special 12% APR partner discounts with one click.
6. **🧘 Zen Mode (Cognitive Accessibility):**
   - Distraction-free palette, soft ambient breathing glow, slower narration playback rate (`Alt+Z`).

---

## Quick Start

```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start local server
uvicorn backend.app:app --reload --port 8000
```

- Customer Mini-App: **http://localhost:8000** (Open in Chrome or Edge for voice input)
- Two-Way Agent Desk: **http://localhost:8000/agent**

---

## Interactive Demo Journeys

1. **Sunita (Kirana Merchant, Kanpur) · Full Loan & Reprice:**
   - Click the microphone and say: `Mujhe dukaan ke liye 2 lakh ka loan chahiye` (or tap the **2L Loan** voice chip).
   - Voice assistant asks for consent $\to$ Say `haan` $\to$ Instant approved offer at 17% p.a.
   - Tap **24m Reprice** $\to$ Rules engine dynamically recalculates EMI from ₹7,131 to ₹9,888.
   - Click **📄 View Official RBI KFS** to inspect APR, fees, and amortisation preview.
   - Say `haan aage badho` $\to$ Click **e-sign se pushti karein** $\to$ Hear the **Paytm Soundbox chime** and voice approval.
2. **Rahul (Food Vendor, Noida) · Explainable Underwriting Decline:**
   - Select **Rahul** from the header dropdown.
   - Say `I need a 2 lakh loan` $\to$ `yes` $\to$ Assistant explains decline due to credit score (598 < 650 threshold).
3. **Meena (New User, Jaipur) · Missing KYC Guardrail:**
   - Select **Meena** $\to$ Say `I need a 50 thousand loan` $\to$ Declines with clear guidance to complete video KYC first.
4. **Health Insurance Q&A & Purchase:**
   - Say `waiting period kya hai?` $\to$ Cites exact policy clauses (SHB-4.1 & SHP-4.1).
   - Say `dono plan compare karo` $\to$ Renders side-by-side comparison matrix.
   - Say `Plus le lo` $\to$ Grants KYC consent $\to$ Issues policy receipt with 15-day free-look guarantee.
5. **Two-Way Agent Intervention:**
   - Say `agent se baat karo` $\to$ Handoff card links to `/agent`.
   - Open `/agent` in a new tab $\to$ Type a message or click **⚡ Offer 12% Special Partner APR**.
   - Watch the customer mini-app update in real time with the human agent's response!

---

## Architecture & Codebase Map

| Component | File Path | Architectural Responsibility |
| :--- | :--- | :--- |
| **Mini-App UI** | [`frontend/index.html`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/frontend/index.html) | Voice recognition, Web Audio visualizer, Soundbox chime, KFS modal, chat, Zen mode |
| **Agent Desk** | [`frontend/agent.html`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/frontend/agent.html) | Live two-way agent intervention, rate overrides, transcripts, audit logs |
| **Orchestrator** | [`backend/app.py`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/backend/app.py) | Multi-turn state machine, consent lifecycle, KFS generator, agent bridge |
| **Bilingual NLU**| [`backend/nlu.py`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/backend/nlu.py) | Devanagari numerals translation, colloquial Hindi number words (`do lakh`, `50k`), tenures |
| **Rules Engine** | [`backend/rules.py`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/backend/rules.py) | Reducing-balance EMI, 40% FOIR cap with binary search shrink, risk-based pricing |
| **Clause RAG** | [`backend/rag.py`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/backend/rag.py) | Pure-Python TF-IDF search over policy wording; triggers human handoff on low confidence |
| **Partner Stubs**| [`backend/partners.py`](file:///c:/Users/lenovo/Downloads/paytm-voice-assistant/paytm-voice-assistant/backend/partners.py) | Telemetry mocks: KYC verification, bureau scores, 12-month Paytm UPI inflows, e-sign |

---

## Automated Journey Tests (10/10 Passing)

```bash
python -m backend.test_journeys
```
Verifies Sunita loan happy path, 24m live repricing, Devanagari Hindi parsing, insurance comparison, subprime/KYC declines, human handoffs, low-confidence safeguards, RBI KFS generation, and two-way agent messaging.

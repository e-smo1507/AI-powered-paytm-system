# Paytm Voice Assistant (Build for India AI Hackathon, Track 2)

> **Voice-first loans + insurance journeys that talk back.**  
> Explain / Decide / Guide / Hand over · Spoken Hindi + Indian English · Deterministic Financial Rules Engine · RBI Digital Lending KFS · Iconic Paytm Soundbox Chime · Responsive customer app and staff inbox.

---

## 🌟 Standout Features Added

1. **🎙️ Responsive Voice-First Customer App:**
   - Real-time Web Audio API frequency analyser renders dynamic pulsing visualizer bars while listening.
   - Comprehensive error recovery (friendly permission guidance, network timeout recovery, clean toggle on/off).
   - Responsive desktop and mobile layouts in both standard and Zen modes.
   - Starts on a short welcome; customers select a demo account before a chat or account data is opened.
2. **🔔 Iconic Paytm Soundbox Audio Experience:**
   - Dual-tone synthesizer chime (740Hz $\to$ 1108Hz) on loan sanction and policy issuance, followed by official spoken voice receipt.
3. **📄 Official RBI Key Fact Statement (KFS) Modal & PDF Export:**
   - Interactive disclosure meeting RBI digital lending guidelines with APR, itemized fee/GST breakdown, 6-month amortisation preview table, statutory 3-day cooling-off notice, and printable layout.
4. **⚡ Live Interactive Re-Pricing Pills:**
   - Instant re-pricing buttons directly inside the offer card (`12m`, `24m`, `36m`, `48m`) demonstrating instantaneous deterministic calculation.
5. **👥 Staff Inbox (`/admin`):**
   - Staff sign in to a separate inbox, see waiting customer handoffs first, join a conversation, and reply without navigating the customer away.
   - Customers see a waiting state until staff joins; KYC declines offer a direct request for human help.
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

# 3. Start local server (macOS / Linux)
./runit.sh

# Or start it directly
uvicorn backend.app:app --reload --port 8000
```

- Customer Mini-App: **http://localhost:8000** (Open in Chrome or Edge for voice input)
- Staff Inbox: **http://localhost:8000/admin**
- Local demo staff sign-in: `admin` / `saytm-demo`

Set `SAYTM_ADMIN_USERNAME` and `SAYTM_ADMIN_PASSWORD` in the server environment to change the demo sign-in credentials. The built-in credentials are for local demos only; configure your own before exposing the app beyond localhost.

---

## Interactive Demo Journeys

1. **Sunita (Kirana Merchant, Kanpur) · Full Loan & Reprice:**
   - Open the profile menu and choose **Sunita**; the chat starts immediately.
   - Click the microphone and say: `Mujhe dukaan ke liye 2 lakh ka loan chahiye` (or tap the **2L Loan** voice chip).
   - Voice assistant asks for consent $\to$ Say `haan` $\to$ Instant approved offer at 17% p.a.
   - Tap **24m Reprice** $\to$ Rules engine dynamically recalculates EMI from ₹7,131 to ₹9,888.
   - Click **📄 View Official RBI KFS** to inspect APR, fees, and amortisation preview.
   - Say `haan aage badho` $\to$ Click **e-sign se pushti karein** $\to$ Hear the **Paytm Soundbox chime** and voice approval.
2. **Rahul (Food Vendor, Noida) · Explainable Underwriting Decline:**
   - Open the profile menu and choose **Rahul**; the chat starts immediately.
   - Say `I need a 2 lakh loan` $\to$ `yes` $\to$ Assistant explains decline due to credit score (598 < 650 threshold).
3. **Meena (New User, Jaipur) · Missing KYC Guardrail:**
   - Open the profile menu and choose **Meena** $\to$ Say `I need a 50 thousand loan` $\to$ Declines with clear guidance to complete video KYC first.
   - Choose **Talk to an agent about KYC** to wait in the customer chat while support joins.
4. **Health Insurance Q&A & Purchase:**
   - Say `waiting period kya hai?` $\to$ Cites exact policy clauses (SHB-4.1 & SHP-4.1).
   - Say `dono plan compare karo` $\to$ Renders side-by-side comparison matrix.
   - Say `Plus le lo` $\to$ Grants KYC consent $\to$ Issues policy receipt with 15-day free-look guarantee.
5. **Human Agent Handoff:**
   - Say `agent se baat karo` or choose the KYC help option $\to$ the customer stays on the chat and sees a waiting state.
   - Open `/admin` in a separate tab and sign in $\to$ the AI-requested handoff appears in the queue; click **Join conversation** to pause the AI and reply.
   - Staff can also click **Intervene in AI chat** before a handoff, which pauses the AI and enables the human reply box.
   - Customer and staff messages appear on the left for received text and on the right for the current speaker's own text. Use each speaker button to read a message aloud; human-agent replies are never spoken automatically.

---

## Architecture & Codebase Map

| Component | File Path | Architectural Responsibility |
| :--- | :--- | :--- |
| **Mini-App UI** | [`frontend/index.html`](./frontend/index.html) | Responsive welcome, account selection, voice input, chat, and Zen mode |
| **Staff Inbox** | [`frontend/admin.html`](./frontend/admin.html) | Staff login, live handoff queue, customer transcripts, and two-way replies |
| **Orchestrator** | [`backend/app.py`](./backend/app.py) | Multi-turn state machine, consent lifecycle, KFS generator, staff inbox API |
| **Bilingual NLU**| [`backend/nlu.py`](./backend/nlu.py) | Devanagari numerals translation, colloquial Hindi number words (`do lakh`, `50k`), tenures |
| **Rules Engine** | [`backend/rules.py`](./backend/rules.py) | Reducing-balance EMI, 40% FOIR cap with binary search shrink, risk-based pricing |
| **Clause RAG** | [`backend/rag.py`](./backend/rag.py) | Pure-Python TF-IDF search over policy wording; triggers human handoff on low confidence |
| **Partner Stubs**| [`backend/partners.py`](./backend/partners.py) | Telemetry mocks: KYC verification, bureau scores, 12-month Paytm UPI inflows, e-sign |

---

## Automated Journey Tests

```bash
pip install -r requirements-dev.txt
python -m pytest backend/test_journeys.py -q
```
Verifies Sunita loan happy path, live repricing, Hindi parsing, insurance flows, underwriting declines, customer handoffs, staff authentication, the waiting queue, and two-way agent messaging.

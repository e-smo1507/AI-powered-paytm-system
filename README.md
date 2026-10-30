# Paytm Voice Assistant (Build for India AI Hackathon, Track 2)

Voice-first loans + insurance assistant: **Explain / Decide / Guide / Hand over**. Hindi + English.

## Run

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

Open **http://localhost:8000** in Chrome or Edge (needed for the microphone).  
Agent desk: **http://localhost:8000/agent**

## Demo script

1. **Sunita, Hindi:** `Mujhe dukaan ke liye 2 lakh ka loan chahiye` → consent → offer → `haan, samjhao` → `haan aage badho` → e-sign. Festival working-capital suggestion appears on start.
2. At the offer, say `24 months` — the rules engine reprices live (EMI is never invented by the model).
3. **Insurance:** `waiting period kya hai?`, `dono plan compare karo`, then `Plus le lo` → KYC consent → e-sign.
4. Unsupported question twice, or `agent se baat karo` → human handoff with transcript on the agent desk.
5. Switch to **Rahul** (low score) or **Meena** (no KYC): explained decline. Use **Audit log** and **Revoke consent**.
6. **Zen mode:** tap **🧘 Zen** (or press `Alt+Z`) for a calmer, distraction-free layout — softer palette, fewer borders, breathing glow, slower narration. The choice is remembered per browser.

## Architecture

| Piece | File | Role |
| --- | --- | --- |
| Mini-app UI | `frontend/index.html` | Voice, chat, captions, chips, Key Fact Statement, e-sign |
| Agent desk | `frontend/agent.html` | Full transcript + audit on handoff |
| Orchestrator | `backend/app.py` | Session state, consent, audit log, e-sign |
| NLU | `backend/nlu.py` | Amount/tenure/intent (Hindi number words, Devanagari digits) |
| Rules engine | `backend/rules.py` | Eligibility + pricing (the model never sets numbers) |
| RAG | `backend/rag.py` | Clause retrieval; no supporting clause → handoff |
| Partner mocks | `backend/partners.py` | KYC, bureau, inflows, e-sign |
| Data | `backend/data/` | Demo users + policy/loan clauses |

## Tests

```
python -m backend.test_journeys
```

## Production swap-ins

`users.json` → KYC / bureau / transaction APIs · TF-IDF → vector DB + SLM · Web Speech → streaming STT/TTS · mock e-sign → real e-sign + RBI KFS / IRDAI review.

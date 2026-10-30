# Saytm — voice-first banking assistant

Saytm is a bilingual Hindi/English banking-assistance prototype for exploring loan and health-insurance journeys through voice or text. The demo combines mock customer data, deterministic financial rules, policy-clause retrieval, browser speech, and a separate staff inbox.

> **Prototype notice:** Customer profiles, partner integrations, underwriting, signatures, and insurance data are simulated. This project is not connected to Paytm accounts, a lender, an insurer, a credit bureau, or a government service, and it is not suitable for real financial decisions.

## What the demo includes

- A welcome-first customer app. No customer session is created until a demo profile is chosen.
- Hindi and Indian-English text and browser speech input/output.
- Purpose-specific consent before using mock financial profile data.
- Deterministic loan calculations and repricing, plus a printable Key Fact Statement preview.
- Policy explanations retrieved from the local sample clause data.
- A customer-side waiting state and a separate authenticated staff inbox.
- Staff takeover/intervention, two-way chat, and per-message speech controls.
- Responsive layouts, a persistent light/dark theme, and a distraction-reduced Zen mode.

The app uses local Python rules and sample data. Browser speech is provided by the browser's Web Speech APIs. No external AI-service API key is required to run this prototype.

## Run locally

Requirements: Python 3.11 or newer and a modern browser. Chrome or Edge is recommended for microphone speech recognition; typed input remains available elsewhere.

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell
pip install -r requirements.txt
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Open:

- Customer app: <http://127.0.0.1:8000/>
- Staff inbox: <http://127.0.0.1:8000/admin>
- Health check: <http://127.0.0.1:8000/health>

The local demo staff credentials are `admin` / `saytm-demo`. Set `SAYTM_ADMIN_USERNAME` and `SAYTM_ADMIN_PASSWORD` in the server environment to override them. The defaults are for local demonstration only; do not expose them on a public deployment.

## Try the customer and staff journeys

1. On the welcome screen, use the profile control to choose a demo customer. The chat starts immediately; there is no separate Continue step.
2. Try a loan request, for example `Mujhe dukaan ke liye 2 lakh ka loan chahiye`, or use a Quick query.
3. Review the consent prompt before the demo uses the selected profile's mock data. Explore repricing, the KFS preview, or the insurance clause questions.
4. Ask for a human agent, or open the profile menu's Staff sign in link (it opens a new tab) and sign in to `/admin`.
5. In the staff inbox, join a waiting handoff or intervene in an active AI conversation. The customer stays in their existing chat.

Staff can inspect active conversations, but the reply composer remains hidden until a human handoff or staff intervention. After takeover, the customer receives a spoken takeover notice and new customer messages no longer trigger another AI response. Human-agent replies are not spoken automatically; either side can play or stop speech for an individual message.

## Project map

| Path | Purpose |
|---|---|
| [`frontend/index.html`](./frontend/index.html) | Customer landing, profile switching, chat, voice controls, responsive themes, and Zen mode |
| [`frontend/admin.html`](./frontend/admin.html) | Staff sign-in, conversation queue, transcript, takeover controls, and replies |
| [`frontend/agent.html`](./frontend/agent.html) | Compatibility page for the staff inbox |
| [`backend/app.py`](./backend/app.py) | FastAPI routes, session orchestration, handoff state, and audit events |
| [`backend/nlu.py`](./backend/nlu.py) | Hindi/English intent and amount parsing |
| [`backend/rules.py`](./backend/rules.py) | Deterministic demo loan calculations |
| [`backend/rag.py`](./backend/rag.py) | Local policy-clause retrieval |
| [`backend/partners.py`](./backend/partners.py) | Mock KYC, bureau, inflow, and e-sign integrations |
| [`backend/data/`](./backend/data/) | Sample customer profiles and policy clauses |
| [`backend/test_journeys.py`](./backend/test_journeys.py) | Customer and staff API journey tests |
| [`docs/`](./docs/) | Product, architecture, workflow, feature, and technology documentation |
| [`design.md`](./design.md) | Detailed, reusable UI/UX design brief and implementation guide |

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q backend/test_journeys.py
```

## Prototype behavior and boundaries

- Customer sessions are held in server memory and disappear when the server restarts. `backend/audit.jsonl` is an append-only event log; it does not restore sessions.
- Customer and partner records are static demo fixtures. Do not enter real identity documents, account data, or sensitive customer information.
- Loan decisions, KFS content, e-sign references, and policy results are simulations and require domain, legal, compliance, and security review before any production use.
- Browser speech availability and voice quality vary by operating system, browser, installed voices, permissions, and locale.
- Staff authentication is intended for local demos. Configure credentials and replace the demo security/session design before deployment.

## Further reading

- [Product requirements](./docs/PRD.md)
- [Feature status](./docs/FEATURE_STATUS.md)
- [Application workflow](./docs/WORKFLOW.md)
- [System architecture](./docs/SYSTEM_ARCHITECTURE.md)
- [Technology stack](./docs/TECH_STACK.md)
- [UI/UX design specification](./design.md)

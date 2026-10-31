# Saytm feature status

This status describes the current local prototype, not a production banking or insurance service. Integrations use demo data and mock partner behavior.

## Implemented

| Area | Current behavior | Main implementation |
|---|---|---|
| Welcome and account selection | Opens directly with default merchant (Sunita) or chosen profile; immediate chat, loan status, WhatsApp alert, and persistent bottom mic/composer. | `frontend/index.html`, `backend/app.py` |
| Language and speech | Hindi and Indian English UI, browser speech input where supported, spoken greetings and assistant replies, per-message playback and stop controls. | `frontend/index.html` |
| Consent | Consent is requested before the demo uses profile data in relevant loan journeys; revocation resets the active demo decision. | `backend/app.py`, `frontend/index.html` |
| Loan journey | Local NLU, deterministic eligibility and pricing, tenure repricing, fee disclosure, and KFS preview. | `backend/nlu.py`, `backend/rules.py`, `backend/app.py` |
| Insurance journey | Local clause retrieval, clause citations, plan comparison, and simulated purchase/signature flow. | `backend/rag.py`, `backend/data/clauses.json`, `backend/app.py` |
| Human support | Customer waits in the existing chat. Staff can join a requested handoff or intervene in an active AI chat; takeover pauses AI replies. | `backend/app.py`, `frontend/admin.html`, `frontend/index.html` |
| Staff inbox | Authenticated local demo login, active/waiting queue, transcript, and two-way messages. Replies are gated until takeover. | `backend/app.py`, `frontend/admin.html` |
| Themes and layout | Responsive desktop/mobile customer and staff views; persistent light/dark preference; separate Zen mode with reduced distraction and improved contrast; viewport-aware layout with scrollable welcome panel and pinned bottom mic/input bar that prevents clipping. | `frontend/index.html`, `frontend/admin.html` |
| Audit events | Important demo events append to a local JSON Lines file. | `backend/app.py`, `backend/audit.jsonl` |
| Merchant notifications & WhatsApp reminders | Pre-due-date installment alerts (5d, 3d, 1d), WhatsApp Business API integration with realistic message previews, deep-link dispatch (`wa.me`), delivery logs, and staff trigger. | `backend/notifications.py`, `backend/app.py`, `frontend/index.html`, `frontend/admin.html` |
| Loan alternatives & criteria guidance | Stepping-stone loan advisory (e.g. ₹5L now to build CIBIL for ₹20L later), bank criteria pass blueprints (CIBIL 750+ roadmap, FOIR / QR turnover), and alternative schemes (Mudra PMMY, daily QR deduction, secured MSME credit). | `backend/alternatives.py`, `backend/app.py`, `frontend/index.html` |
| Loan protection & insurance cross-sell | Proactive recommendation of suitable health & shop shields (e.g. `SecureHealth Plus` / `Basic`) when a merchant gets a loan, protecting working capital and ensuring EMI repayment continuity. | `backend/alternatives.py`, `backend/app.py`, `frontend/index.html` |
| Cloud deployment & dynamic API base | Multi-platform deployment ready (Render, Railway, Heroku, Vercel, Docker); dynamic backend URL discovery, query-param override (`?api=...`), in-app API settings dialog, and actionable connection error cards. | `Procfile`, `Dockerfile`, `vercel.json`, `api/index.py`, `main.py`, `app.py`, `frontend/index.html` |
| Regression tests | Customer journeys, consent, rules, retrieval, staff login, waiting, intervention, and messaging. | `backend/test_journeys.py` |

## Prototype limitations

- Profiles and partner data are static fixtures. No production customer data source is connected.
- Sessions live in process memory and are lost on backend restart.
- The rules engine, clause data, signature references, and KFS are demonstrations, not official product decisions or legal disclosures.
- Browser-native speech recognition may be unavailable or permission/network-limited. Text entry remains available.
- Staff credentials and session handling are demonstration-grade. Do not expose the default credentials publicly.
- The project has no dependency on a hosted generative-AI API key. Conversation behavior is provided by local rules, parsing, and retrieval.

## Production work still required

1. Replace demo accounts and local credentials with verified identity, authorization, and session management.
2. Obtain legal, risk, compliance, accessibility, and security review for all financial and consent journeys.
3. Integrate approved partner APIs and persist sessions/audit data using production-grade storage and retention controls.
4. Replace simulated signatures and statements with approved signing and disclosure services.
5. Define deployment, observability, incident response, and speech-service privacy requirements.

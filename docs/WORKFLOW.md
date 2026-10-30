# End-to-End Application Workflow & Journey Guide
## Paytm Voice Assistant · Operational & Conversational Workflows

---

## 1. Application Initialization & Startup Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Sunita / Rahul / Meena)
    participant Browser as Browser Client (index.html)
    participant Server as FastAPI Server (backend/app.py)
    participant Storage as backend/data/users.json

    User->>Browser: Opens http://localhost:8000
    Browser->>Browser: Loads HTML, CSS, Hind fonts, initializes DOM
    Browser->>Browser: Reads localStorage('paytm-zen') -> restores Zen state
    Browser->>Server: POST /api/start {user: "sunita", lang: "hi"}
    Server->>Storage: Load user record for "sunita"
    Server->>Server: Create new session in SESSIONS[sid]
    Server->>Server: Audit event: session_start
    Server-->>Browser: JSON {sid, reply, cards: [guide], chips: [...], profile}
    Browser->>Browser: Render assistant greeting bubble
    Browser->>Browser: Render Proactive Guide Card
    Browser->>Browser: Render Quick-Reply Chips
    Browser->>Browser: SpeechSynthesis: Speak greeting aloud in Hindi
```

### Detailed Startup Steps:
1. **Client Loading:** The browser requests `GET /`, serving `frontend/index.html`.
2. **State Hydration:** JavaScript inspects `localStorage.getItem('paytm-zen')`. If set to `1`, the document body is decorated with class `.zen`, enabling calm colors and the breathing glow background.
3. **Session Genesis:** The client automatically issues `POST /api/start` with the default persona (`sunita`) and language (`hi`).
4. **Backend Orchestration:** `app.py:start()` generates a unique 8-character session ID (`sid`), allocates a fresh state dictionary in `SESSIONS[sid]`, and pulls customer telemetry from `backend/data/users.json`.
5. **Proactive Financial Guidance:** If the customer record contains a `hint` (e.g. Sunita's upcoming festival inventory requirement), a personalized greeting and a purple-accented Guide Card are generated.
6. **Vocal Greeting:** The browser invokes `say(greeting)` via the Web Speech Synthesis API, greeting the customer by name.

---

## 2. Interaction Modes & Input Processing

Users can interact through three synchronized modalities:

```mermaid
flowchart LR
    VoiceInput[1. Voice Input<br/>Mic Button Clicked] --> SpeechRec[Browser Web Speech API<br/>SpeechRecognition]
    SpeechRec --> Interim[Live Interim Text in Input Field]
    Interim --> FinalSpeech[Final Speech Recognition Event]
    
    TextInput[2. Text Input<br/>Typed into Input Field] --> EnterSubmit[Enter Key or Send Button]
    
    ChipClick[3. Contextual Chips<br/>One-Tap Quick Actions] --> DirectSend[Direct API Dispatch]
    
    FinalSpeech --> SendFunction[send Function]
    EnterSubmit --> SendFunction
    DirectSend --> SendFunction
    
    SendFunction --> LockUI[Set busy = true, Render User Bubble]
    LockUI --> APICall[POST /api/chat]
```

---

## 3. Core Journey Workflows

### Journey 1: Sunita · Complete Merchant Loan & Dynamic Repricing Flow

- **Persona Context:** Sunita, 34, Kanpur. Kirana merchant with 26-month platform vintage, ₹89,333 average monthly inflows, bureau score 724, and completed KYC.
- **Goal:** Secure ₹2,00,000 working capital before Diwali, adjust tenure from 36 to 24 months, and complete e-sign.

```mermaid
sequenceDiagram
    autonumber
    actor Sunita as Sunita (Kirana Merchant)
    participant UI as Mini-App UI
    participant Backend as FastAPI & Rules Engine

    Sunita->>UI: Voice: "Mujhe dukaan ke liye 2 lakh ka loan chahiye"
    UI->>Backend: POST /api/chat {text, lang: 'hi'}
    Backend-->>UI: Stage: consent | Consent Card (KYC, Inflows, Bureau)
    UI-->>Sunita: Speaks: "2 lakh ke loan ki patrata janchne..."

    Sunita->>UI: Voice: "Haan, sehmat hoon" (or taps 'मैं सहमत हूँ')
    UI->>Backend: POST /api/chat {text: "haan", lang: 'hi'}
    Backend->>Backend: Fetch telemetry -> Run rules.decide()
    Backend-->>UI: Stage: offer | KFS Offer Card (Amount: ₹2,00,000, 36m, EMI: ₹7,130, 17% p.a.)
    UI-->>Sunita: Speaks offer terms and asks: "Fees aur interest simple shabdon mein samjhaun?"

    Sunita->>UI: Voice: "24 mahine mein"
    UI->>Backend: POST /api/chat {text: "24 mahine mein", lang: 'hi'}
    Backend->>Backend: Reprice via rules.decide(amount=200000, tenure=24)
    Backend-->>UI: Stage: offer | Repriced KFS Card (24m, EMI: ₹9,892, 17% p.a.)
    UI-->>Sunita: Speaks: "Aap 2,00,000 tak ke liye eligible hain. 24 mahine mein EMI lagbhag 9,892..."

    Sunita->>UI: Voice: "Haan, samjhao"
    UI->>Backend: POST /api/chat {text: "haan, samjhao", lang: 'hi'}
    Backend-->>UI: Stage: fees | Fee Breakdown (Proc Fee: ₹4,000, GST: ₹720, Disbursed: ₹1,95,280)
    UI-->>Sunita: Speaks transparent net disbursement and total repayment

    Sunita->>UI: Voice: "Haan aage badho"
    UI->>Backend: POST /api/chat {text: "haan aage badho", lang: 'hi'}
    Backend-->>UI: Stage: esign | e-Sign Confirmation Card
    UI-->>Sunita: Speaks: "Badhiya. Neeche Key Fact Statement dekhein aur e-sign se pushti karein."

    Sunita->>UI: Taps "e-sign से पुष्टि करें"
    UI->>Backend: POST /api/sign {sid}
    Backend->>Backend: Generate reference: PTM-L-XXXX-XXXX
    Backend-->>UI: Stage: done | Receipt Card + 3-Day Cooling-Off Notice
    UI-->>Sunita: Speaks: "Ho gaya! ₹2,00,000 ka loan manzoor hai..."
```

---

### Journey 2: Rahul · Credit Score Decline & Explainability Flow

- **Persona Context:** Rahul, 41, Noida. Street-food vendor with verified KYC, 9-month platform vintage, but credit score of 598 (below the 650 threshold).
- **Goal:** Attempt ₹2,00,000 loan; understand why the platform cannot disburse immediately.

```mermaid
sequenceDiagram
    autonumber
    actor Rahul as Rahul (Vendor)
    participant UI as Mini-App UI
    participant Backend as FastAPI & Rules Engine

    Rahul->>UI: Voice: "I need a 2 lakh loan"
    UI->>Backend: POST /api/chat {text: "I need a 2 lakh loan", lang: 'en'}
    Backend-->>UI: Stage: consent | Consent Card
    
    Rahul->>UI: Voice: "Yes, I agree"
    UI->>Backend: POST /api/chat {text: "yes", lang: 'en'}
    Backend->>Backend: rules.decide() evaluates bureau score (598 < 650)
    Backend->>Backend: Decision: eligible=False, reasons=['score']
    Backend-->>UI: Stage: idle | Decline Card (Reason: credit score is below the limit)
    UI-->>Rahul: Speaks: "Sorry, I can't offer a loan right now. Reason: credit score is below the limit. I can connect you to an agent."
```

---

### Journey 3: Meena · Incomplete KYC Guardrail Flow

- **Persona Context:** Meena, 22, Jaipur. New user with unverified KYC, 2-month platform vintage, zero bureau history.
- **Goal:** Attempt ₹50,000 micro-loan; receive explicit guidance on prerequisites.

```mermaid
sequenceDiagram
    autonumber
    actor Meena as Meena (New User)
    participant UI as Mini-App UI
    participant Backend as FastAPI & Rules Engine

    Meena->>UI: Voice: "I need a 50 thousand loan"
    UI->>Backend: POST /api/chat {text: "I need a 50 thousand loan", lang: 'en'}
    Backend-->>UI: Stage: consent | Consent Card
    
    Meena->>UI: Voice: "Yes"
    UI->>Backend: POST /api/chat {text: "yes", lang: 'en'}
    Backend->>Backend: rules.decide() checks kyc=False, score=0, vintage=2
    Backend->>Backend: Decision: eligible=False, reasons=['kyc', 'score', 'vintage']
    Backend-->>UI: Stage: idle | Decline Card (Reasons: KYC incomplete, score below limit, vintage too short)
    UI-->>Meena: Speaks: "Sorry, I can't offer a loan right now. Reason: KYC is incomplete..."
```

---

### Journey 4: Health Insurance Clause Inquiry, Comparison & Purchase Flow

- **Goal:** Inquire about pre-existing disease waiting periods, compare Basic vs Plus plans, select Plus, and e-sign policy.

```mermaid
sequenceDiagram
    autonumber
    actor User as Insurance Customer
    participant UI as Mini-App UI
    participant Backend as FastAPI & RAG Engine

    User->>UI: Voice: "waiting period kya hai?"
    UI->>Backend: POST /api/chat {text: "waiting period kya hai?", lang: 'hi'}
    Backend->>Backend: RAG retrieve(): matches SHB-4.1 (score 0.65) and SHP-4.1 (score 0.65)
    Backend-->>UI: Clause Cards (SHB-4.1: 4 years, SHP-4.1: 2 years)
    UI-->>User: Speaks: "पहले से मौजूद बीमारियाँ Basic में 4 साल..."

    User->>UI: Voice: "dono plan compare karo"
    UI->>Backend: POST /api/chat {text: "dono plan compare karo", lang: 'hi'}
    Backend-->>UI: Comparison Table Card (Premium, Sum Insured, Waiting, Room Rent, Co-pay)
    UI-->>User: Speaks: "Plus में इंतज़ार कम (2 साल), कमरे की सीमा नहीं..."

    User->>UI: Voice: "Plus le lo"
    UI->>Backend: POST /api/chat {text: "Plus le lo", lang: 'hi'}
    Backend-->>UI: Stage: ins_consent | Consent Card (Scope: KYC name, Age)
    UI-->>User: Speaks: "SecureHealth Plus खरीदने के लिए KYC नाम और उम्र देखनी होगी..."

    User->>UI: Voice: "Haan"
    UI->>Backend: POST /api/chat {text: "haan", lang: 'hi'}
    Backend-->>UI: Stage: ins_quote | Quote Card (₹12,900/yr, ₹10 lakh cover) + e-Sign Card
    
    User->>UI: Taps "e-sign से पुष्टि करें"
    UI->>Backend: POST /api/sign {sid}
    Backend->>Backend: Generate reference: PTM-H-XXXX-XXXX
    Backend-->>UI: Stage: done | Policy Receipt Card + 15-Day Free-Look Notice
    UI-->>User: Speaks: "पॉलिसी सक्रिय है। 15 दिन फ्री-लुक में रद्द कर सकते हैं।"
```

---

### Journey 5: Fallback & Human Agent Handoff Flow

- **Trigger 1:** Explicit request: "Agent se baat karo" / "Talk to an agent".
- **Trigger 2:** Low RAG confidence: Out-of-domain questions ("are dinosaur bites covered?").
- **Trigger 3:** Repeated misunderstanding: Two consecutive unclassified queries.

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer
    participant UI as Customer Mini-App
    participant Backend as FastAPI Orchestrator
    participant AgentDesk as Agent Desk (/agent)

    User->>UI: Voice: "are dinosaur bites covered in this policy?"
    UI->>Backend: POST /api/chat {text: "...", lang: 'en'}
    Backend->>Backend: RAG search fails (score < 0.32)
    Backend->>Backend: Trigger handoff(reason='no_supporting_clause', nofound=True)
    Backend->>Backend: Audit event: handoff
    Backend-->>UI: Stage: handoff | Handoff Card ("Connecting you to a human agent now...")
    UI-->>User: Speaks handoff disclosure

    Note over AgentDesk: Agent Desk polls /api/sessions every 4s
    AgentDesk->>Backend: GET /api/sessions
    Backend-->>AgentDesk: Session list with flag: HANDOFF
    AgentDesk->>Backend: GET /api/session/{sid}
    Backend-->>AgentDesk: Full session transcript, user profile, and audit log
    Note over AgentDesk: Human agent reads context; customer never repeats themselves
```

---

## 4. Supporting Operational Workflows

### 4.1 Data Consent Revocation Workflow
1. User clicks **"Revoke consent"** link in tools bar (`frontend/index.html:213`).
2. Client calls `POST /api/consent/revoke` passing `{sid}`.
3. Backend marks `s["consent"]["revoked"] = True`, clears `s["decision"] = None`, and resets `s["stage"] = "idle"`.
4. Backend writes `audit(sid, "consent_revoked")`.
5. Frontend informs user: *"आपकी डेटा-मंज़ूरी वापस ले ली गई है।"* (Your data consent has been revoked).

### 4.2 Audit Log Inspection Workflow
1. User clicks **"Audit log"** in tools bar (`frontend/index.html:214`).
2. Client requests `GET /api/audit/{sid}`.
3. Backend returns raw array of chronological session audit records.
4. Client opens native HTML5 `<dialog id="dlg">` displaying formatted JSONL records with timestamps, events, and parameters.

### 4.3 Zen Mode (Cognitive Accessibility) Workflow
1. User clicks **"🧘 Zen"** button or presses `Alt+Z` keyboard shortcut.
2. JavaScript toggles CSS class `document.body.classList.toggle('zen')`.
3. Background ambient glow fades in with a gentle 9-second ease-in-out breathing cycle (`@keyframes breathe`).
4. Speech synthesis rate drops from `0.95` to `0.88`, ensuring clear, relaxed narration.
5. Mode preference is saved to `localStorage.setItem('paytm-zen', '1')` and restored automatically on next visit.

### 4.4 Official RBI Key Fact Statement (KFS) Inspection & Print Workflow
1. When loan offer is presented or signed, user clicks **"📄 View Official RBI KFS"**.
2. Frontend requests `GET /api/kfs/{sid}`.
3. Backend produces official disclosure payload: effective APR, 6-month amortization preview, 3-day cooling-off declarations, and nodal officer contacts.
4. Native `<dialog id="kfs_dlg">` displays the formatted KFS with a **"🖨️ Print / Save PDF"** button invoking `window.print()`.

### 4.5 Two-Way Human Agent Desk Intervention Workflow
1. When session escalates, agent opens `frontend/agent.html` and selects the flagged customer.
2. Agent reviews historical dialogue, credit telemetry, and audit trail.
3. Agent enters a reply in the live composer or clicks **"⚡ Offer 12% Special Partner APR"**.
4. Agent client posts to `POST /api/agent/message` with `{sid, text, action}`.
5. Customer mini-app polls `/api/poll/{sid}`, receives the agent's turn, renders an agent badge (`👤 Neha (Paytm Credit Specialist)`), and reads the message aloud.

### 4.6 Real-Time Audio Waveform & Iconic Paytm Soundbox Chime Workflow
1. User clicks the microphone button: `startMic()` requests audio stream via `navigator.mediaDevices.getUserMedia`.
2. Real-time `AudioContext` frequency analyser updates the heights of 7 visualizer bars, providing responsive feedback while listening.
3. If an error occurs (permission denied, network timeout), friendly guidance alerts appear with one-click quick prompt chips.
4. Upon e-signing, `playSoundbox()` synthesizes a melodic fintech chime (740Hz $\to$ 1108Hz) via Web Audio API, followed by an official spoken Paytm voice receipt.


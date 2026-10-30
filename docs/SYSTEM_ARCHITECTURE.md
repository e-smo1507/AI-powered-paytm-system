# System Architecture & Technical Specifications
## Saytm · Architecture Documentation

---

## 1. Architectural Philosophy & Core Principles

Saytm is a local demonstration of conversational financial journeys. It is not a production banking or insurance service. Its design uses three prototype principles:

1. **Separation of Explanation and Calculation:** The demo's language parsing and response flow are separate from its deterministic financial calculations. Monetary values and eligibility outcomes come from the rules engine (`backend/rules.py`), not a hosted language-model API.
2. **Clause-Grounded Retrieval:** Insurance explanations retrieve from the local sample clauses (`backend/data/clauses.json`). Low-confidence questions can be escalated rather than answered with unsupported sample policy claims.
3. **Purpose-Limited Demo Consent:** The sample flow demonstrates explicit consent before using selected mock-profile data and supports revocation. This is not a certification of legal or regulatory compliance.

---

## 2. High-Level Component Topology

```mermaid
graph TB
    subgraph ClientLayer ["Client Presentation Tier (Browser / WebView)"]
        UI["Paytm Mini-App Client<br/>(frontend/index.html)"]
        Desk["Authenticated Staff Inbox<br/>(frontend/admin.html)"]
        MicAPI["Web Speech API (SpeechRecognition)<br/>hi-IN / en-IN"]
        TTSAPI["SpeechSynthesis API<br/>Dynamic Rate / Locale Pitch"]
        Storage["Browser LocalStorage<br/>(Theme and Zen Preferences)"]
    end

    subgraph GatewayLayer ["API & Transport Tier (FastAPI + ASGI)"]
        CORS["CORSMiddleware (allow_origins='*')"]
        StaticRoute["Page Routes (/static, /, /admin, /agent alias)"]
        APIRouter["FastAPI REST Endpoints<br/>(customer APIs, authenticated /api/admin/*, /api/agent/message, /api/poll, ...)"]
        PydanticModels["Pydantic Inbound Schema Validation<br/>(StartIn, ChatIn, SidIn, AgentMsgIn, AdminLoginIn)"]
    end

    subgraph ServiceLayer ["Core Orchestration & Intelligence Services"]
        Orchestrator["Session State Machine & Turn Orchestrator<br/>(backend/app.py)"]
        NLU["Bilingual NLU & Number Normalizer<br/>(backend/nlu.py)"]
        Rules["Deterministic Financial Rules Engine<br/>(backend/rules.py)"]
        RAG["Clause Retrieval RAG Engine<br/>(backend/rag.py)"]
        Partners["Partner Connectors & Mock Telemetry<br/>(backend/partners.py)"]
        Audit["Audit Logger & Event Dispatcher<br/>(backend/app.py:audit)"]
    end

    subgraph StateLayer ["Data, Session & Persistence Tier"]
        MemorySessions["In-Memory Session Cache<br/>(SESSIONS dictionary)"]
        UserStore[("User Telemetry JSON<br/>(backend/data/users.json)")]
        ClauseStore[("Policy Clauses JSON<br/>(backend/data/clauses.json)")]
        AuditLog[("Append-Only Audit Log<br/>(backend/audit.jsonl)")]
    end

    %% Interactions
    UI -->|Spoken Voice| MicAPI
    MicAPI -->|Transcribed Text| UI
    UI -->|Spoken Response| TTSAPI
    UI <--> Storage
    UI -->|HTTP POST JSON / Poll| CORS
    Desk <-->|Authenticated Queue, Join & Replies| CORS
    CORS --> StaticRoute
    CORS --> APIRouter
    APIRouter --> PydanticModels
    PydanticModels --> Orchestrator

    Orchestrator <--> MemorySessions
    Orchestrator --> NLU
    Orchestrator --> Rules
    Orchestrator --> RAG
    Orchestrator --> Partners
    Orchestrator --> Audit

    Partners <--> UserStore
    RAG <--> ClauseStore
    Audit --> AuditLog
```

---

## 3. Subsystem Breakdown

### 3.1 Client Tier (`frontend/index.html`, `frontend/admin.html`)
The frontend is a zero-dependency HTML/CSS/JavaScript demo for modern desktop and mobile browsers. It has not been validated as a production Paytm Super-App integration.

- **Audio Engine:** 
  - `window.SpeechRecognition` / `window.webkitSpeechRecognition` captures continuous voice streams. Interim transcripts are rendered live into input field `$('t')`. Final transcript submission directly invokes `send()`.
  - `window.speechSynthesis` speaks responses. The voice matching the chosen language (`hi-IN` or `en-IN`) is selected automatically.
- **Dynamic Renderers:**
  - `cards()` evaluates card schemas (`consent`, `guide`, `offer`, `ins_quote`, `clause`, `compare`, `esign`, `receipt`, `decline`, `handoff`).
  - `chips()` creates quick-reply pills based on current conversation context.
- **Zen Mode Engine:**
  - Reduces visual distractions while keeping essential account, language, theme, speech, and chat actions available. It supports both light and dark themes and persists independently from the theme selection.
- **Welcome & Account Selection:**
  - Opens without a selected customer session and speaks one short welcome line. Choosing a profile starts that customer's chat immediately; there is no Continue step.
- **Staff Inbox:**
  - `/admin` presents a sign-in screen and live queue. Authenticated staff can join a requested handoff or intervene in an active AI chat. The reply composer is gated until takeover; the customer remains on the original page. `/agent` is a compatibility alias.
- **Speech Controls:**
  - Message playback is manually controllable and can be stopped from the same speaker button. Human replies are not auto-spoken; the customer receives a spoken takeover notice.

---

### 3.2 Orchestrator & State Machine (`backend/app.py`)
The orchestrator maintains multi-turn conversation states inside memory dictionary `SESSIONS`.

- Staff credentials are configurable with `SAYTM_ADMIN_USERNAME` and `SAYTM_ADMIN_PASSWORD`; the local demo defaults are not for public deployment.
- Successful staff login creates an eight-hour HttpOnly, SameSite=Strict cookie. Queue, session detail, connect, and staff-message endpoints validate this cookie.
- Handoff state is returned to the customer poller so the customer remains in a waiting state until staff joins. An authenticated intervention can also connect an active AI session and pause subsequent AI replies.

```mermaid
stateDiagram-v2
    [*] --> idle: POST /api/start
    
    idle --> amount: Loan intent without amount
    idle --> consent: Loan intent with amount
    idle --> ins: Insurance query
    idle --> ins_consent: Insurance buy intent ("Plus le lo")
    
    amount --> consent: Amount parsed
    
    consent --> idle: User declines ("nahi")
    consent --> offer: User accepts ("haan") -> Rules Engine runs
    
    offer --> offer: Tenure reprice ("24 months") / Amount change
    offer --> fees: User asks for fees ("haan, samjhao")
    
    fees --> esign: User confirms ("haan aage badho")
    fees --> offer: User asks to re-adjust
    
    esign --> done: e-Sign confirmed (POST /api/sign)
    
    ins --> ins_quote: User chooses plan
    ins_quote --> ins_consent: User agrees to purchase
    ins_consent --> done: Insurance e-Sign confirmed
    
    idle --> handoff: User says "talk to agent" OR RAG low confidence OR 2x unknown
    amount --> handoff: Escalation
    consent --> handoff: Escalation
    offer --> handoff: Escalation
    ins --> handoff: Escalation
    
    done --> [*]
    handoff --> [*]
```

#### Session Schema
Each active session in `SESSIONS[sid]` holds:
```python
{
    "user": str,               # Key mapping into USERS ('sunita', 'rahul', 'meena')
    "lang": str,               # 'hi' or 'en'
    "stage": str,              # Current state machine node
    "amount": int | None,      # Active requested loan principal
    "tenure": int,             # Active loan tenure in months (default: 36)
    "consent": dict | None,    # Authorization scope and grant timestamp
    "decision": dict | None,   # Serialized dataclass output of rules.decide()
    "unknown": int,            # Counter tracking unrecognized turns
    "transcript": list[dict],  # Chronological conversation turn logs
    "audit": list[dict],       # Chronological session audit records
    "handoff": bool,           # Flag determining agent desk escalation
    "plan": str | None,        # Selected insurance plan ('basic' | 'plus')
    "product": str | None,     # 'loan' or 'insurance'
    "ref": str | None          # Transaction reference generated upon e-signing
}
```

---

### 3.3 Natural Language Understanding Service (`backend/nlu.py`)
The NLU service provides specialized parsing for Indian colloquial speech patterns:
- **Character Translation:** Converts Devanagari numerals (`०१२३४५६७८९`) into standard ASCII digits.
- **Colloquial Hindi Number Normalization:** Recognizes numeric words across Hindi and English (`ek`, `do`, `teen`, `ek lakh`, `do lakh`, `pachas hazaar`, `50k`, `2.5 lakh`).
- **Tenure Parser:** Resolves mixed phrase structures (`36 mahine`, `2 saal`, `24 months`, `1.5 years`) into standardized integer months.
- **Phrase Matchers:** Token-level and boundary-delimited phrase sets for:
  - `YES`: `["haan", "han", "yes", "ok", "theek", "sure", "agree", "हाँ", "कर दो", "आगे बढ़ो", ...]`
  - `NO`: `["nahi", "nahin", "no", "नहीं", "mat", "decline", "refuse"]`
  - `HUMAN`: `["human", "agent", "insaan", "इंसान", "executive", "बात करनी", "talk to", ...]`
  - `LOAN`: `["loan", "लोन", "udhaar", "कर्ज", "karz", "working capital"]`
  - `INS`: `["insurance", "bima", "बीमा", "policy", "cover", "waiting", "exclusion", ...]`
  - `CMP`: `["compare", "तुलना", "vs", "dono", "दोनों", "difference"]`

---

### 3.4 Deterministic Financial Rules Engine (`backend/rules.py`)
The rules engine implements mathematically sound credit decisioning.

```mermaid
flowchart TD
    In[Input: User Profile, Requested Amount, Requested Tenure] --> Gate1{KYC complete?}
    Gate1 -- No --> FailKYC[Decline: reason = 'kyc']
    Gate1 -- Yes --> Gate2{Bureau score >= 650?}
    Gate2 -- No --> FailBureau[Decline: reason = 'score']
    Gate2 -- Yes --> Gate3{Vintage >= 6 months?}
    Gate3 -- No --> FailVintage[Decline: reason = 'vintage']
    Gate3 -- Yes --> Gate4{Amount >= ₹10,000?}
    Gate4 -- No --> FailMin[Decline: reason = 'min_amount']
    
    Gate4 -- Yes --> CapEval[Cap Principal = min ₹500,000, 2.5 * avg_monthly_inflow]
    CapEval --> RateEval[Rate Tier: >=750 -> 14%, >=700 -> 17%, >=650 -> 21%]
    RateEval --> EMICalc[Calculate Monthly Reducing Balance EMI]
    
    EMICalc --> FOIRCheck{EMI <= 40% of Inflow?}
    FOIRCheck -- Yes --> Finalize[Compute 2% Fee, 18% GST, Disbursed, Total Repayment]
    FOIRCheck -- No --> BinarySearch[Binary Search: Shrink principal until EMI <= 0.40 * Inflow]
    BinarySearch --> ShrunkCheck{Shrunk Principal >= ₹10,000?}
    ShrunkCheck -- No --> FailFOIR[Decline: reason = 'foir']
    ShrunkCheck -- Yes --> Finalize
    
    Finalize --> ReturnDecision[Return Decision Dataclass: eligible = True]
```

#### Financial Formulae
- **Monthly Reducing-Balance EMI:**
  $$r_{monthly} = \frac{\text{Annual Rate}}{12 \times 100}$$
  $$\text{EMI} = P \cdot r_{monthly} \cdot \frac{(1 + r_{monthly})^n}{(1 + r_{monthly})^n - 1}$$
- **Processing Fee & Taxes:**
  $$\text{Processing Fee} = \text{round}(P \times 0.02)$$
  $$\text{GST} = \text{round}(\text{Processing Fee} \times 0.18)$$
  $$\text{Net Disbursed Amount} = P - \text{Processing Fee} - \text{GST}$$
  $$\text{Total Repayment} = \text{round}(\text{EMI} \times n)$$
  $$\text{Total Interest} = \text{Total Repayment} - P$$

---

### 3.5 Clause-Grounded RAG Engine (`backend/rag.py`)
Answers insurance policy and loan term inquiries without hallucination risk.

- **Corpus:** 14 structured clauses across `SecureHealth Basic` (SHB), `SecureHealth Plus` (SHP), and `Paytm Merchant Loan` (LN).
- **Indexing:** Bilingual stopword removal (`STOP` set contains English and Hindi conversational tokens), term-frequency extraction, and document frequency indexing (`DF`).
- **Scoring Function:**
  $$\text{IDF}(t) = \ln\left(\frac{N + 1}{\text{DF}(t) + 1}\right) + 1$$
  $$\text{Score}(q, d) = \frac{\sum_{t \in q \cap d} \text{IDF}(t) \cdot (1 + \ln(c(t, d)))}{\sqrt{|d|}}$$
- **Confidence Bounding:** Returns top-$k$ matches ($k=2$) only when $\text{Score} \ge \text{threshold}$ (default: 0.35). If no clauses meet threshold, triggers immediate fallback.

---

### 3.6 Partner Interfaces & Mock Connectors (`backend/partners.py`)
Simulates external institutional integrations:
- `fetch_kyc(user_id)`: Fetches verification status, name, city, and age.
- `fetch_bureau(user_id)`: Fetches credit bureau score.
- `fetch_inflows(user_id)`: Provides 12-month array of merchant UPI collections, average monthly inflow, platform vintage, and contextual life-event triggers.
- `esign(kind, amount)`: Generates digitally verifiable transaction identifier (`PTM-L-...` / `PTM-H-...`).

---

## 4. End-to-End Sequence Diagram (Loan Journey)

```mermaid
sequenceDiagram
    autonumber
    actor User as Sunita (Customer)
    participant UI as Browser / Mini-App
    participant API as FastAPI Orchestrator
    participant NLU as NLU Module
    participant Partners as Partner Connectors
    participant Rules as Rules Engine
    participant Audit as Audit Log

    User->>UI: Speaks: "Mujhe dukaan ke liye 2 lakh ka loan chahiye"
    UI->>API: POST /api/chat {sid, text, lang: 'hi'}
    API->>Audit: Log user_turn
    API->>NLU: parse_amount("... 2 lakh ..."), parse_tenure(...)
    NLU-->>API: amount=200000, tenure=None, intent=loan
    API-->>UI: Reply with consent request + Consent Card
    UI-->>User: Speaks: "2 lakh ke loan ki patrata janchne..."

    User->>UI: Speaks: "Haan, sehmat hoon"
    UI->>API: POST /api/chat {sid, text: "haan", lang: 'hi'}
    API->>Audit: Log consent_granted
    API->>Partners: fetch_kyc(), fetch_bureau(), fetch_inflows()
    Partners-->>API: kyc=True, bureau=724, avg_inflow=89333
    API->>Rules: decide(profile, amount=200000, tenure=36)
    Rules-->>API: Decision(eligible=True, rate=17.0, emi=7130, fee=4000, gst=720, ...)
    API->>Audit: Log decision
    API-->>UI: Reply with offer text + KFS Card
    UI-->>User: Displays Key Fact Statement & speaks offer terms

    User->>UI: Speaks: "24 mahine mein kitna hoga?"
    UI->>API: POST /api/chat {sid, text: "24 mahine mein", lang: 'hi'}
    API->>NLU: parse_tenure("24 mahine") -> 24
    API->>Rules: decide(profile, amount=200000, tenure=24)
    Rules-->>API: Decision(eligible=True, rate=17.0, emi=9892, ...)
    API-->>UI: Reply with re-priced offer & updated KFS Card
    UI-->>User: Speaks updated terms

    User->>UI: Speaks: "Haan, aage badho"
    UI->>API: POST /api/chat {sid, text: "haan aage badho", lang: 'hi'}
    API-->>UI: Reply with e-Sign confirmation prompt + e-Sign Card

    User->>UI: Clicks "e-sign से पुष्टि करें"
    UI->>API: POST /api/sign {sid}
    API->>Partners: esign(kind='loan', amount=200000)
    Partners-->>API: ref="PTM-L-7FA1-8902"
    API->>Audit: Log esigned (kind='loan', ref=ref)
    API-->>UI: Return Receipt Card + 3-day cooling-off disclosure
    UI-->>User: Speaks: "Ho gaya! Loan manzoor hai..."
```

---

## 5. Security & Regulatory Compliance Architecture

### 5.1 DPDP Act (Data Protection) Architecture
- **Purpose Limitation:** Consent is tied to explicit operational scopes (`kyc`, `txn_12m`, `bureau`).
- **Revocability:** `/api/consent/revoke` sets `consent.revoked = True`, nullifies cached decision objects, resets stage to `idle`, and writes a persistent audit entry.

### 5.2 RBI Digital Lending Alignment
- **Key Fact Statement (KFS):** Automatically produced prior to agreement execution, revealing APR, loan amount, repayment frequency, processing fee, and taxes.
- **Cooling-Off Window:** All loan sanction receipts explicitly mandate and inform borrowers of their 3-day penalty-free statutory cooling-off window.

### 5.3 IRDAI Disclosure Alignment
- **Contractual Clause Attribution:** Every insurance claim regarding exclusions, waiting periods, or room rent limits is cited directly from standard policy wording, including clause reference IDs.
- **Free-Look Cancellation:** All insurance confirmation receipts communicate the 15-day free-look cancellation window.

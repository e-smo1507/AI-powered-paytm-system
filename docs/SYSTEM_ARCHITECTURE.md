# System Architecture & Technical Specifications
## Paytm Voice Assistant · Architecture Documentation

---

## 1. Architectural Philosophy & Core Principles

The Paytm Voice Assistant is architected specifically for high-stakes fintech domains where hallucinations, non-transparent decisions, and compliance violations cannot be tolerated. The architecture is governed by three non-negotiable principles:

1. **Separation of Explanation and Calculation:** Generative or statistical language components are restricted to conversational dialogue and intent mapping. All monetary values, fees, EMIs, interest rates, eligibility criteria, and repayments are strictly governed by a deterministic, transparent rules engine (`backend/rules.py`).
2. **Clause-Grounded Knowledge (Zero Hallucination RAG):** The assistant cannot invent coverage details, room rent caps, or exclusion clauses. Queries are checked against the codified contract clauses (`backend/data/clauses.json`). When no clause confidently supports an answer, the system immediately triggers a human handoff.
3. **Purpose-Limited, Revocable Consent Lifecycle:** Conforming to India's Digital Personal Data Protection (DPDP) Act and RBI digital lending norms, partner financial data (KYC, credit scores, transaction inflows) is accessed only after explicit customer authorization. Revoking consent immediately evicts calculations and active offers from memory.

---

## 2. High-Level Component Topology

```mermaid
graph TB
    subgraph ClientLayer ["Client Presentation Tier (Browser / WebView)"]
        UI["Paytm Mini-App Client<br/>(frontend/index.html)"]
        Desk["Human Agent Escalation Desk<br/>(frontend/agent.html)"]
        MicAPI["Web Speech API (SpeechRecognition)<br/>hi-IN / en-IN"]
        TTSAPI["SpeechSynthesis API<br/>Dynamic Rate / Locale Pitch"]
        Storage["Browser LocalStorage<br/>(Zen Mode State)"]
    end

    subgraph GatewayLayer ["API & Transport Tier (FastAPI + ASGI)"]
        CORS["CORSMiddleware (allow_origins='*')"]
        StaticRoute["StaticFiles Mount (/static, /, /agent)"]
        APIRouter["FastAPI REST Endpoints<br/>(/api/start, /api/chat, /api/sign, /api/kfs, /api/agent/message, /api/poll, ...)"]
        PydanticModels["Pydantic Inbound Schema Validation<br/>(StartIn, ChatIn, SidIn, AgentMsgIn)"]
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
    Desk <-->|Two-Way Live Messaging & Poll| CORS
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

### 3.1 Client Tier (`frontend/index.html`, `frontend/agent.html`)
The frontend is built as a zero-dependency, ultra-lightweight client suitable for embedding inside the Paytm Super-App WebView or standard desktop/mobile browsers.

- **Audio Engine:** 
  - `window.SpeechRecognition` / `window.webkitSpeechRecognition` captures continuous voice streams. Interim transcripts are rendered live into input field `$('t')`. Final transcript submission directly invokes `send()`.
  - `window.speechSynthesis` speaks responses. The voice matching the chosen language (`hi-IN` or `en-IN`) is selected automatically.
- **Dynamic Renderers:**
  - `cards()` evaluates card schemas (`consent`, `guide`, `offer`, `ins_quote`, `clause`, `compare`, `esign`, `receipt`, `decline`, `handoff`).
  - `chips()` creates quick-reply pills based on current conversation context.
- **Zen Mode Engine:**
  - Injected via CSS variables on `.zen`. Modulates palette, suppresses sharp rectangular borders, triggers CSS keyframe breathing glow (`@keyframes breathe`), and slows voice playback rate from 0.95x to 0.88x.
- **Agent Desk:**
  - Minimalist operations dashboard (`frontend/agent.html`) polling `/api/sessions` every 4,000ms. Renders real-time transcripts, raw rule decision outputs, and audit trail for handed-off sessions.

---

### 3.2 Orchestrator & State Machine (`backend/app.py`)
The orchestrator maintains multi-turn conversation states inside memory dictionary `SESSIONS`.

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


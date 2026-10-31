"""Saytm Voice Assistant orchestrator. Run: uvicorn backend.app:app --reload"""
import json
import os
import secrets
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import nlu
from .partners import PLANS, USERS, decide_plan, fetch_bureau, fetch_inflows, fetch_kyc
from .rag import retrieve, CL
from .rules import decide
from . import llm_agent
from . import notifications
from . import alternatives

ROOT = Path(__file__).parent
FRONT = ROOT.parent / "frontend"
AUDIT_FILE = ROOT / "audit.jsonl"
SESSIONS: dict = {}
ADMIN_SESSIONS: dict[str, float] = {}
ADMIN_USERNAME = os.getenv("SAYTM_ADMIN_USERNAME") or "admin"
ADMIN_PASSWORD = os.getenv("SAYTM_ADMIN_PASSWORD") or "saytm-demo"
ADMIN_SESSION_TTL = 8 * 60 * 60

app = FastAPI(title="Saytm Voice Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def inr(n):
    n = int(round(n or 0))
    s = str(abs(n))
    if len(s) <= 3:
        body = s
    else:
        last3, rest, parts = s[-3:], s[:-3], []
        while rest:
            parts.append(rest[-2:])
            rest = rest[:-2]
        body = ",".join(reversed(parts)) + "," + last3
    return ("-" if n < 0 else "") + "₹" + body


def audit(sid, event, **data):
    if sid not in SESSIONS:
        return
    rec = {"t": time.strftime("%H:%M:%S"), "sid": sid, "event": event, **data}
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


C = {
    "greet": {
        "hi": "नमस्ते {n} जी! मैं Saytm Assistant हूँ। लोन चाहिए या स्वास्थ्य बीमा समझना है? बोलिए।",
        "en": "Hello {n}! I'm Saytm Assistant. Need a loan, or want a health plan explained? Just say it.",
    },
    "guide": {
        "hi": " आपका Saytm इतिहास देखकर लग रहा है: {h}। क्या अभी इसी पर बात करें?",
        "en": " From your Saytm history it looks like: {h}. Shall we talk about that now?",
    },
    "ask_amt": {
        "hi": "कितने रुपये का लोन चाहिए? जैसे: \"2 लाख\"।",
        "en": "How much would you like to borrow? For example: \"2 lakh\".",
    },
    "consent": {
        "hi": "{a} के लोन की पात्रता जाँचने के लिए मुझे आपका KYC और Saytm लेन-देन डेटा देखना होगा। सिर्फ़ इसी काम के लिए, और आप कभी भी मंज़ूरी वापस ले सकते हैं। क्या आप सहमत हैं?",
        "en": "To check eligibility for {a}, I need to read your KYC and Saytm transaction data, only for this purpose, and you can revoke consent anytime. Do you agree?",
    },
    "declined": {
        "hi": "ठीक है, मैंने आपका कोई डेटा नहीं देखा। आप चाहें तो फ़ॉर्म से आवेदन कर सकते हैं या किसी एजेंट से बात कर सकते हैं।",
        "en": "No problem. I haven't accessed any of your data. You can apply via the form or talk to an agent.",
    },
    "checking": {
        "hi": "आपके Saytm बिज़नेस डेटा से पात्रता जाँच रहा हूँ…",
        "en": "Checking eligibility from your Saytm business data…",
    },
    "offer": {
        "hi": "आप {a} तक के लिए पात्र हैं। {t} महीने में EMI लगभग {e} (ब्याज {r}% सालाना)। फ़ीस और ब्याज सरल शब्दों में समझाऊँ?",
        "en": "You're eligible for {a}. Over {t} months the EMI is about {e} (interest {r}% a year). Shall I explain the fees and interest simply?",
    },
    "reduced": {
        "hi": "आपकी आय के हिसाब से मैं {a} तक की ही पेशकश कर सकता हूँ। ",
        "en": "Based on your inflows, the most I can offer is {a}. ",
    },
    "fees": {
        "hi": "सीधे शब्दों में: प्रोसेसिंग फ़ीस {f} + GST {g}, यानी खाते में आएँगे {d}। कुल ब्याज {i} लगेगा और कुल वापसी {p}। समय से पहले चुकाने पर कोई छिपा शुल्क नहीं। आगे बढ़ें?",
        "en": "In plain words: processing fee {f} + GST {g}, so you receive {d}. Total interest is {i} and you repay {p} in all. No hidden foreclosure fee. Shall we go ahead?",
    },
    "esign": {
        "hi": "नीचे Key Fact Statement देखें। e-sign अनुरोध भेजने पर मानव एजेंट इसकी समीक्षा करेगा; अभी लोन मंज़ूर या सक्रिय नहीं होगा।",
        "en": "Review the Key Fact Statement below. Sending an e-sign request asks a human agent to review it; the loan is not approved or active yet.",
    },
    "kyc_review_pending": {
        "hi": "आपका KYC अनुरोध मानव एजेंट की मंज़ूरी के लिए भेज दिया गया है। एजेंट सुरक्षित KYC प्रक्रिया के लिए आपका मार्गदर्शन करेगा। कृपया पहचान दस्तावेज़ इस चैट में न भेजें।",
        "en": "Your KYC request is waiting for human-agent approval. An agent will guide you through the secure KYC process; please don't send identity documents in this chat.",
    },
    "signature_review_pending": {
        "hi": "आपका e-sign अनुरोध मानव एजेंट की मंज़ूरी के लिए भेज दिया गया है। एजेंट समीक्षा पूरी होने तक लोन या पॉलिसी सक्रिय नहीं होगी।",
        "en": "Your e-sign request is waiting for human-agent approval. The loan or policy will not be activated until an agent completes the review.",
    },
    "inelig": {
        "hi": "माफ़ कीजिए, अभी मैं लोन नहीं दे पा रहा। कारण: {r}। मैं आपको एजेंट से जोड़ सकता हूँ।",
        "en": "Sorry, I can't offer a loan right now. Reason: {r}. I can connect you to an agent.",
    },
    "r": {
        "kyc": {"hi": "KYC पूरा नहीं है", "en": "KYC is incomplete"},
        "score": {"hi": "क्रेडिट स्कोर सीमा से कम है", "en": "credit score is below the limit"},
        "vintage": {"hi": "कारोबार/खाता बहुत नया है", "en": "account history is too short"},
        "min_amount": {"hi": "राशि न्यूनतम ₹10,000 से कम है", "en": "amount is below the ₹10,000 minimum"},
        "foir": {"hi": "EMI आपकी आय के 40% से अधिक बैठती", "en": "EMI would exceed 40% of inflows"},
    },
    "ins_hi": {
        "hi": "मैं दो हेल्थ प्लान समझा सकता हूँ: SecureHealth Basic (₹8,400/साल, ₹5 लाख) और Plus (₹12,900/साल, ₹10 लाख)। पूछें: \"वेटिंग पीरियड क्या है?\" या \"दोनों की तुलना करो\"। खरीदना हो तो \"Plus ले लो\" कहें।",
        "en": "I can explain two health plans: SecureHealth Basic (₹8,400/yr, ₹5 lakh) and Plus (₹12,900/yr, ₹10 lakh). Ask \"what is the waiting period?\" or \"compare both\". To buy, say \"take Plus\".",
    },
    "ins_consent": {
        "hi": "{p} खरीदने के लिए KYC नाम और उम्र देखनी होगी — सिर्फ़ पॉलिसी जारी करने के लिए। सहमत हैं?",
        "en": "To issue {p} I need to read your KYC name and age, only for this policy. Do you agree?",
    },
    "ins_quote": {
        "hi": "{p}: सालाना प्रीमियम {pr}, बीमा राशि {s}। क्लेम नियम नीचे धाराओं में हैं। e-sign करें?",
        "en": "{p}: annual premium {pr}, sum insured {s}. Claim rules are cited below. e-sign?",
    },
    "ins_done": {
        "hi": "पॉलिसी सक्रिय है। 15 दिन फ्री-लुक में रद्द कर सकते हैं। संदर्भ: {ref}",
        "en": "Policy is active. You may cancel in the 15-day free-look window. Ref: {ref}",
    },
    "nofound": {
        "hi": "इस बारे में दस्तावेज़ में मुझे कोई स्पष्ट धारा नहीं मिली, इसलिए मैं अंदाज़ा नहीं लगाऊँगा। एजेंट आपसे जुड़ेगा।",
        "en": "I couldn't find a clause that supports an answer, so I won't guess. Connecting you to an agent.",
    },
    "handoff": {
        "hi": "मैं आपको अभी एजेंट से जोड़ रहा हूँ। पूरी बातचीत उनके सामने होगी, दोबारा बताने की ज़रूरत नहीं।",
        "en": "Connecting you to a human agent now. They'll see the whole conversation, so you won't need to repeat anything.",
    },
    "unk": {
        "hi": "माफ़ कीजिए, समझ नहीं पाया। \"लोन चाहिए\" या \"बीमा समझाओ\" बोलकर देखें।",
        "en": "Sorry, I didn't catch that. Try \"I need a loan\" or \"explain health insurance\".",
    },
    "repeat_consent": {
        "hi": "पात्रता जाँचने के लिए हाँ या नहीं कहें। डेटा बिना मंज़ूरी नहीं खोलूँगा।",
        "en": "Please say yes or no to data consent. I won't open your data without it.",
    },
}


def T(k, lang, **kw):
    return C[k][lang].format(**kw)


class ChatIn(BaseModel):
    sid: str
    text: str
    lang: str = "hi"


class StartIn(BaseModel):
    user: str = "sunita"
    lang: str = "hi"


class SidIn(BaseModel):
    sid: str


class AgentMsgIn(BaseModel):
    sid: str
    text: str
    agent_name: str = "Neha (Saytm Agent)"
    action: str | None = None


class AdminLoginIn(BaseModel):
    username: str
    password: str


def require_admin(request: Request):
    token = request.cookies.get("saytm_admin")
    expires_at = ADMIN_SESSIONS.get(token or "")
    if not expires_at or expires_at <= time.time():
        ADMIN_SESSIONS.pop(token or "", None)
        raise HTTPException(401, "Admin login required")


def S(sid):
    if sid not in SESSIONS:
        raise HTTPException(404, "unknown session")
    return SESSIONS[sid]


import datetime

HINDI_MONTHS = {
    1: "जनवरी", 2: "फ़रवरी", 3: "मार्च", 4: "अप्रैल",
    5: "मई", 6: "जून", 7: "जुलाई", 8: "अगस्त",
    9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर"
}

def get_emi_reminder(user_data: dict, lang: str = "hi") -> dict | None:
    loan = user_data.get("active_loan")
    if not loan:
        return None
    offset = loan.get("due_day_offset", 3)
    due_dt = datetime.date.today() + datetime.timedelta(days=offset)
    if lang == "hi":
        month_name = HINDI_MONTHS.get(due_dt.month, due_dt.strftime("%B"))
        due_date_str = f"{due_dt.day} {month_name} {due_dt.year}"
    else:
        due_date_str = due_dt.strftime("%d %b %Y")
    return {
        "type": "emi_reminder",
        "loan_id": loan.get("loan_id", "LN-8821"),
        "purpose": loan.get("purpose", "Merchant Loan"),
        "amount": loan.get("emi_amount", 4850),
        "due_date": due_date_str,
        "days_left": offset,
        "auto_debit": loan.get("auto_debit", True),
        "account": loan.get("account", "Paytm Payments Bank ...5019"),
        "status": "upcoming",
        "phone": user_data.get("phone", "+919876543210"),
        "merchant_name": user_data.get("name", "Merchant"),
        "whatsapp_enabled": True,
    }


def chips(stage, lang, has_emi=False):
    h = lang == "hi"
    idle_chips = (["दुकान लोन ₹2 लाख", "मेरी EMI कब है?", "WhatsApp रिमाइंडर", "बीमा समझाओ"] if h else ["I need a 2 lakh loan", "When is my EMI due?", "WhatsApp Reminder", "Explain health insurance"]) if has_emi else (["मुझे 2 लाख का लोन चाहिए", "CIBIL कैसे सुधारें?", "20 लाख का लोन विकल्प", "बीमा समझाओ"] if h else ["I need a 2 lakh loan", "How to boost CIBIL?", "20 Lakh loan options", "Explain health insurance"])
    return {
        "idle": idle_chips,
        "amount": ["2 लाख", "5 लाख", "20 लाख"] if h else ["2 lakh", "5 lakh", "20 lakh"],
        "consent": ["हाँ, सहमत हूँ", "नहीं"] if h else ["Yes, I agree", "No thanks"],
        "offer": ["हाँ, समझाओ", "बीमा सुरक्षा जोड़ें", "24 महीने में", "एजेंट से बात करो"] if h else ["Yes, explain", "Add Insurance Shield", "Use 24 months", "Talk to an agent"],
        "fees": ["हाँ, आगे बढ़ो", "एजेंट से बात करो"] if h else ["Yes, go ahead", "Talk to an agent"],
        "esign": ["e-sign अनुरोध भेजें"] if h else ["Send e-sign request"],
        "ins": ["वेटिंग पीरियड क्या है?", "कमरे के किराये की सीमा?", "Plus ले लो"] if h else ["What is the waiting period?", "Room rent limit?", "Take Plus"],
        "ins_consent": ["हाँ", "नहीं"] if h else ["Yes", "No"],
        "ins_quote": ["e-sign अनुरोध भेजें", "Basic बताओ"] if h else ["Send e-sign request", "Tell me about Basic"],
    }.get(stage, [])


def reply(s, sid, lang, text, cards=None, chip_key=None, has_emi=False):
    s["transcript"].append({"role": "assistant", "text": text, "ts": time.strftime("%H:%M:%S"), "lang": lang})
    u = USERS.get(s.get("user"), {})
    has_active_emi = has_emi or bool(u.get("active_loan"))
    return {
        "reply": text,
        "cards": cards or [],
        "chips": chips(chip_key or s["stage"], lang, has_emi=has_active_emi),
        "stage": s["stage"],
        "lang": lang,
        "handoff": s["handoff"],
        "agent_connected": s["agent_connected"],
        "consent_active": bool(s.get("consent") and not s["consent"].get("revoked")),
        "sid": sid,
    }


def offer_card(s):
    return {"type": "offer", **s["decision"], "inflow_basis": "12-month Saytm inflows"}


def offer_text(s, lang):
    d = s["decision"]
    req = s.get("amount") or 0
    pre = ""
    if req >= 1_000_000 and d["amount"] < req:
        if lang == "hi":
            pre = f"आपने {inr(req)} के लोन का अनुरोध किया था। वर्तमान में बिना गारंटी डिजिटल लोन की स्वीकृत सीमा {inr(d['amount'])} है। सुझाव: आप अभी यह {inr(d['amount'])} का स्टार्टर लोन लेकर समय पर चुकाएँ ताकि CIBIL 750+ बने और बाद में 20 लाख के बड़े लोन की पात्रता मिल सके।\n\n"
        else:
            pre = f"You requested {inr(req)}. Instant collateral-free digital merchant loans are currently capped at {inr(d['amount'])}. Recommendation: Start with this {inr(d['amount'])} loan to build a 750+ CIBIL score, which qualifies you for the full {inr(req)} loan subsequently.\n\n"
    elif d["amount"] < req or "foir" in d["reasons"]:
        pre = T("reduced", lang, a=inr(d["amount"]))

    base_offer = T("offer", lang, a=inr(d["amount"]), t=d["tenure"], e=inr(d["emi"]), r=d["rate"])

    if lang == "hi":
        ins_tip = f"\n\n🛡️ सुरक्षा सुझाव: इस लोन के साथ अपनी दुकान और परिवार को सुरक्षित रखने के लिए हमने 'Paytm SecureHealth Plus' (₹10 लाख स्वास्थ्य व EMI सुरक्षा) का सुझाव दिया है।"
    else:
        ins_tip = f"\n\n🛡️ Protection Tip: To safeguard your business working capital & loan EMIs against unexpected illness or shop disruption, we recommend pairing this loan with 'Paytm SecureHealth Plus'."

    return pre + base_offer + ins_tip


def run_decision(s, sid):
    d = decide(USERS[s["user"]], s["amount"], s["tenure"])
    s["decision"] = d.dict()
    audit(sid, "decision", amount=s["amount"], eligible=d.eligible, reasons=d.reasons, emi=d.emi)
    return d


def after_decision(s, sid, lang, d):
    user_prof = USERS[s["user"]]
    req_amt = s.get("amount") or 0
    if not d.eligible:
        s["stage"] = "idle"
        why = ", ".join(C["r"][r][lang] for r in d.reasons)
        cards = [{"type": "decline", "reasons": d.reasons}]

        # 1. Bank Criteria Pass Guidance
        criteria_card = alternatives.get_criteria_pass_guidance(user_prof, d.reasons, lang)
        cards.append(criteria_card)

        # 2. Alternative Loans & Stepping Stone options
        alt_card = alternatives.get_loan_alternatives(user_prof, req_amt, d.dict(), lang)
        cards.append(alt_card)

        msg = T("inelig", lang, r=why)
        if lang == "hi":
            msg += "\n\n💡 बैंक मापदंड (Criteria) पास करने और वैकल्पिक लोन रास्ते के उपाय नीचे दिए गए हैं।"
        else:
            msg += "\n\n💡 Check below for actionable ways to clear bank criteria and explore alternative financing routes."

        audit(sid, "loan_declined_alternatives_suggested", reasons=d.reasons)
        return reply(s, sid, lang, msg, cards, "idle")

    s["stage"] = "offer"
    cards = [offer_card(s)]

    # If requested amount was high (e.g. 20 lakhs), add loan alternatives card
    if req_amt >= 1_000_000 and req_amt > d.amount:
        alt_card = alternatives.get_loan_alternatives(user_prof, req_amt, d.dict(), lang)
        cards.append(alt_card)

    # Proactively suggest suitable future protection insurance when merchant gets a loan
    ins_rec = alternatives.get_loan_insurance_recommendation(d.dict(), user_prof, lang)
    cards.append(ins_rec)
    s["loan_insurance_rec"] = ins_rec

    return reply(s, sid, lang, offer_text(s, lang), cards)


def grant(s, sid, lang):
    kyc, bur, inf = fetch_kyc(s["user"]), fetch_bureau(s["user"]), fetch_inflows(s["user"])
    s["consent"] = {
        "purpose": "loan_eligibility",
        "scope": ["kyc", "txn_12m", "bureau"],
        "granted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "revoked": False,
        "snapshot": {"kyc": kyc["complete"], "bureau": bur["score"], "avg_inflow": inf["avg"]},
    }
    audit(sid, "consent_granted", **{k: s["consent"][k] for k in ("purpose", "scope", "granted_at")})
    d = run_decision(s, sid)
    return after_decision(s, sid, lang, d)


def begin_loan(s, sid, lang):
    if not s["amount"]:
        s["stage"] = "amount"
        return reply(s, sid, lang, T("ask_amt", lang))
    if s.get("consent") and not s["consent"].get("revoked"):
        d = run_decision(s, sid)
        return after_decision(s, sid, lang, d)
    s["stage"] = "consent"
    return reply(
        s, sid, lang, T("consent", lang, a=inr(s["amount"])),
        [{"type": "consent", "scope": ["KYC status", "12-month Saytm inflows", "Credit bureau score"]}],
    )


def compare_card(lang):
    rows = [
        ("Premium / year", "₹8,400", "₹12,900"),
        ("Sum insured", "₹5 lakh", "₹10 lakh"),
    ]
    for title, kid in (("Waiting (existing illness)", "4.1"), ("Room rent", "5.2"), ("Co-pay at 60+", "7.3"), ("Maternity", "6.1")):
        a = next(c for c in CL if c["id"] == "SHB-" + kid)
        p = next(c for c in CL if c["id"] == "SHP-" + kid)
        rows.append((title, a[lang], p[lang]))
    return {"type": "compare", "rows": rows}


def ins_quote_cards(plan_key, lang):
    p = PLANS[plan_key]
    hits = [c for c in CL if c["id"].startswith(p["id"] + "-")][:4]
    cards = [{
        "type": "ins_quote",
        "plan": p["name"],
        "premium": p["premium"],
        "sum_insured": p["sum_insured"],
    }]
    cards += [{"type": "clause", "id": h["id"], "plan": h["plan"], "title": h["title"], "text": h["en"], "hi": h["hi"]} for h in hits]
    return cards


def handoff(s, sid, lang, reason, nofound=False):
    s["handoff"] = True
    s["stage"] = "handoff"
    audit(sid, "handoff", reason=reason)
    msg = T("nofound", lang) if nofound else T("handoff", lang)
    return reply(s, sid, lang, msg, [{"type": "handoff", "reason": reason, "context": s["transcript"][-12:]}], "none")


@app.post("/api/start")
def start(b: StartIn):
    if b.user not in USERS:
        raise HTTPException(400, "unknown user")
    u = USERS[b.user]
    sid = uuid.uuid4().hex[:8]
    SESSIONS[sid] = dict(
        user=b.user, lang=b.lang, created_at_ns=time.time_ns(), stage="idle", amount=None, tenure=36, consent=None,
        decision=None, unknown=0, transcript=[], audit=[], handoff=False, agent_connected=False,
        plan=None, product=None, review_type=None,
    )
    audit(sid, "session_start", user=b.user)
    msg = T("greet", b.lang, n=u["name"])
    cards = []
    if u.get("hint"):
        msg += T("guide", b.lang, h=u["hint"])
        cards.append({"type": "guide", "event": u.get("life_event"), "hint": u["hint"]})

    # Proactive merchant EMI reminder (3 and 5 days before due date)
    emi_rem = get_emi_reminder(u, b.lang)
    if emi_rem and emi_rem.get("days_left") in (1, 2, 3, 5):
        if b.lang == "hi":
            msg += f"\n\n🔔 ज़रूरी EMI रिमाइंडर: आपके {emi_rem['purpose']} की {inr(emi_rem['amount'])} की EMI {emi_rem['days_left']} दिन बाद ({emi_rem['due_date']}) को देय है। कृपया ऑटो-डेबिट के लिए बैंक खाते में पर्याप्त राशि रखें।"
        else:
            msg += f"\n\n🔔 Important EMI Reminder: Your {emi_rem['purpose']} EMI of {inr(emi_rem['amount'])} is due in {emi_rem['days_left']} days on {emi_rem['due_date']}. Please maintain sufficient balance for auto-debit."
        cards.append(emi_rem)
        audit(sid, "emi_reminder_displayed", loan_id=emi_rem["loan_id"], amount=emi_rem["amount"], days_left=emi_rem["days_left"])

    SESSIONS[sid]["transcript"].append({"role": "assistant", "text": msg, "ts": time.strftime("%H:%M:%S"), "lang": b.lang})
    return {
        "sid": sid,
        "reply": msg,
        "cards": cards,
        "chips": chips("idle", b.lang, has_emi=bool(emi_rem)),
        "lang": b.lang,
        "profile": {"name": u["name"], "kind": u["kind"], "city": u["city"], "age": u.get("age")},
    }


class EmiPayIn(BaseModel):
    sid: str
    loan_id: str | None = None


@app.post("/api/emi/pay")
def pay_emi(b: EmiPayIn):
    s = S(b.sid)
    lang = s.get("lang", "hi")
    u = USERS.get(s["user"], {})
    reminder = get_emi_reminder(u, lang)
    if not reminder:
        raise HTTPException(400, "No active loan found")
    reminder["status"] = "paid"
    s["emi_paid"] = True
    audit(b.sid, "emi_paid", loan_id=reminder["loan_id"], amount=reminder["amount"])
    ref = "PPB-EMI-" + uuid.uuid4().hex[:6].upper()
    if lang == "hi":
        msg = f"धन्यवाद! {inr(reminder['amount'])} की EMI का भुगतान सफलतापूर्वक प्राप्त हो गया है। रसीद संदर्भ: {ref}। आपके लोन का स्टेटस अपडेट कर दिया गया है।"
    else:
        msg = f"Thank you! Your EMI payment of {inr(reminder['amount'])} has been successfully processed. Receipt Ref: {ref}. Your loan record is up to date."
    return reply(s, b.sid, lang, msg, [reminder], "idle")


class WhatsAppSendIn(BaseModel):
    user_id: str = "sunita"
    phone: str | None = None
    lang: str = "hi"
    custom_message: str | None = None
    sid: str | None = None


@app.get("/api/notifications/merchant/{user_id}")
def get_merchant_notifications(user_id: str, lang: str = "hi"):
    if user_id not in USERS:
        raise HTTPException(404, f"User '{user_id}' not found")
    u = USERS[user_id]
    due_info = notifications.get_merchant_due_info(u, lang)
    if not due_info:
        return {
            "has_loan": False,
            "user_id": user_id,
            "merchant_name": u.get("name", user_id),
            "phone": u.get("phone", ""),
            "message": "No active loan found for this merchant",
            "history": [h for h in notifications.NOTIFICATION_HISTORY if h.get("recipient_name") == u.get("name")],
        }

    phone = u.get("phone", "+919876543210")
    due_hi = notifications.get_merchant_due_info(u, "hi")
    due_en = notifications.get_merchant_due_info(u, "en")
    msg_hi = notifications.format_whatsapp_reminder(u.get("name", "Merchant"), due_hi, "hi")
    msg_en = notifications.format_whatsapp_reminder(u.get("name", "Merchant"), due_en, "en")
    link_hi = notifications.generate_whatsapp_deep_link(phone, msg_hi)
    link_en = notifications.generate_whatsapp_deep_link(phone, msg_en)

    return {
        "has_loan": True,
        "user_id": user_id,
        "merchant_name": u.get("name", user_id),
        "phone": phone,
        "due_info": due_info,
        "preview": {
            "hi": {"message": msg_hi, "wa_link": link_hi},
            "en": {"message": msg_en, "wa_link": link_en},
        },
        "history": [h for h in notifications.NOTIFICATION_HISTORY if h.get("recipient_name") == u.get("name")],
    }


@app.post("/api/notifications/whatsapp/send")
def send_whatsapp(b: WhatsAppSendIn):
    if b.user_id not in USERS:
        raise HTTPException(404, f"User '{b.user_id}' not found")
    u = USERS[b.user_id]
    due_info = notifications.get_merchant_due_info(u, b.lang)
    if not due_info:
        raise HTTPException(400, "Merchant does not have an active loan installment to remind.")

    phone = b.phone or u.get("phone", "+919876543210")
    record = notifications.send_whatsapp_notification(
        merchant_name=u.get("name", b.user_id),
        phone=phone,
        due_info=due_info,
        lang=b.lang,
        custom_message=b.custom_message,
    )

    if b.sid and b.sid in SESSIONS:
        audit(
            b.sid,
            "whatsapp_notification_sent",
            phone=phone,
            loan_id=due_info.get("loan_id"),
            amount=due_info.get("amount"),
            days_left=due_info.get("days_left"),
            msg_id=record["id"],
        )

    return {
        "ok": True,
        "record": record,
        "notification": {
            "id": record["id"],
            "status": "delivered",
            "phone": record["phone"],
            "recipient_name": record["recipient_name"],
            "due_date": record["due_date"],
            "amount": record["amount"],
            "days_left": record["days_left"],
            "wa_link": record["wa_link"],
            "message": record["message"],
            "sent_at": record["sent_at"],
        },
    }


@app.get("/api/notifications/history")
def get_notification_history():
    return {
        "count": len(notifications.NOTIFICATION_HISTORY),
        "notifications": notifications.NOTIFICATION_HISTORY,
    }


@app.post("/api/chat")
def chat(b: ChatIn):
    if b.sid not in SESSIONS:
        SESSIONS[b.sid] = dict(
            user="sunita", lang=b.lang, created_at_ns=time.time_ns(), stage="idle", amount=None, tenure=36, consent=None,
            decision=None, unknown=0, transcript=[], audit=[], handoff=False, agent_connected=False,
            plan=None, product=None, review_type=None,
        )
        audit(b.sid, "session_auto_revived", user="sunita")
    s, sid, lang, t = S(b.sid), b.sid, b.lang, (b.text or "").strip()
    if not t:
        return reply(s, sid, lang, T("unk", lang), [], "idle")
    s["lang"] = lang
    s["transcript"].append({"role": "user", "text": t, "ts": time.strftime("%H:%M:%S"), "lang": lang})
    audit(sid, "user_turn", text=t)
    if s["agent_connected"]:
        return {
            "reply": "",
            "cards": [],
            "chips": [],
            "stage": s["stage"],
            "lang": lang,
            "handoff": s["handoff"],
            "agent_connected": True,
            "consent_active": bool(s.get("consent") and not s["consent"].get("revoked")),
            "sid": sid,
        }
    if s["handoff"] or nlu.has_phrase(t, nlu.HUMAN):
        return handoff(s, sid, lang, "user_request")

    amt, ten = nlu.parse_amount(t), nlu.parse_tenure(t)
    st = s["stage"]
    yes, no = nlu.has_phrase(t, nlu.YES), nlu.has_phrase(t, nlu.NO)

    if st == "consent":
        if no and not yes:
            s["stage"] = "idle"
            audit(sid, "consent_declined")
            return reply(s, sid, lang, T("declined", lang))
        if yes:
            return grant(s, sid, lang)
        return reply(s, sid, lang, T("repeat_consent", lang), [{"type": "consent", "scope": ["KYC status", "12-month Saytm inflows", "Credit bureau score"]}])

    if st == "ins_consent":
        if no and not yes:
            s["stage"] = "idle"
            return reply(s, sid, lang, T("declined", lang), [], "ins")
        if yes:
            s["consent"] = s.get("consent") or {"purpose": "insurance_issue", "scope": ["kyc"], "granted_at": time.strftime("%Y-%m-%d %H:%M:%S"), "revoked": False}
            audit(sid, "ins_consent_granted")
            p = PLANS[s["plan"]]
            s["stage"] = "ins_quote"
            return reply(s, sid, lang, T("ins_quote", lang, p=p["name"], pr=inr(p["premium"]), s=inr(p["sum_insured"])), ins_quote_cards(s["plan"], lang) + [{"type": "esign", "kind": "insurance"}])
        return reply(s, sid, lang, T("repeat_consent", lang))

    if st in ("offer", "fees"):
        if ten or (amt and not nlu.has_phrase(t, nlu.FEES)):
            if ten:
                s["tenure"] = ten
            if amt:
                s["amount"] = amt
            run_decision(s, sid)
            s["stage"] = "offer"
            return reply(s, sid, lang, offer_text(s, lang), [offer_card(s)])
        if nlu.has_phrase(t, nlu.FEES) or (st == "offer" and yes):
            d = s["decision"]
            s["stage"] = "fees"
            audit(sid, "fees_explained")
            hits = retrieve("processing fee foreclosure cooling off", k=2, threshold=0.2)
            cards = [offer_card(s)] + [{"type": "clause", "id": h["id"], "plan": h["plan"], "title": h["title"], "text": h["en"], "hi": h["hi"]} for h in hits]
            return reply(s, sid, lang, T("fees", lang, f=inr(d["fee"]), g=inr(d["gst"]), d=inr(d["disbursed"]), i=inr(d["total_interest"]), p=inr(d["total_payable"])), cards)
        if st == "fees" and yes:
            s["stage"] = "esign"
            audit(sid, "esign_requested")
            return reply(s, sid, lang, T("esign", lang), [offer_card(s), {"type": "esign", "kind": "loan"}])

    if st == "esign" and (yes or nlu.has_phrase(t, ["esign", "e-sign", "sign", "साइन"])):
        return submit_signature_for_review(s, sid, lang, "loan")

    if st in ("ins_quote", "ins_esign") and (yes or nlu.has_phrase(t, ["esign", "e-sign", "sign", "साइन"])):
        return submit_signature_for_review(s, sid, lang, "insurance")

    if nlu.has_phrase(t, nlu.BUY) or decide_plan(t):
        plan = decide_plan(t) or s.get("plan") or "plus"
        s["plan"] = plan
        s["product"] = "insurance"
        s["stage"] = "ins_consent"
        return reply(s, sid, lang, T("ins_consent", lang, p=PLANS[plan]["name"]), [{"type": "consent", "scope": ["KYC name", "Age"]}])

    # Check EMI reminder query
    is_emi_query = (
        nlu.has_phrase(t, ["emi", "ईएमआई", "installment", "किस्त", "kist"]) and (
            nlu.has_phrase(t, ["reminder", "रिमाइंडर", "due", "देय", "date", "तारीख", "kab", "कब", "next", "अगली", "agla", "agli", "kitna", "कितना", "pay", "bharna", "payment", "status", "बकाया", "aaj", "kya"])
            or len(nlu.tokens(t)) <= 3
        )
    ) or nlu.has_phrase(t, ["due date", "देय तिथि", "emi reminder", "next emi", "अगली emi", "मेरी emi", "meri emi", "my emi", "kab hai"])

    if is_emi_query and st in ("idle", "amount"):
        u = USERS.get(s["user"], {})
        reminder = get_emi_reminder(u, lang)
        if reminder:
            if s.get("emi_paid"):
                reminder["status"] = "paid"
            audit(sid, "emi_inquiry", loan_id=reminder["loan_id"])
            if reminder.get("status") == "paid":
                msg = (
                    f"आपकी {inr(reminder['amount'])} की EMI का भुगतान पहले ही सफलतापूर्वक हो चुका है। संदर्भ संख्या: PPB-EMI-PAID।"
                    if lang == "hi" else
                    f"Your EMI of {inr(reminder['amount'])} for this cycle has already been paid successfully. Ref: PPB-EMI-PAID."
                )
            elif lang == "hi":
                msg = (
                    f"आपकी अगली EMI {inr(reminder['amount'])} की है, जो {reminder['days_left']} दिन बाद ({reminder['due_date']}) को देय है। "
                    f"आपके बैंक खाते ({reminder['account']}) से ऑटो-डेबिट सक्रिय है। कृपया खाते में पर्याप्त बैलेंस रखें।"
                )
            else:
                msg = (
                    f"Your next EMI of {inr(reminder['amount'])} is due in {reminder['days_left']} days on {reminder['due_date']}. "
                    f"Auto-debit is active on {reminder['account']}. Please ensure sufficient balance."
                )
            return reply(s, sid, lang, msg, [reminder], "idle")
        else:
            msg = (
                "आपके खाते में अभी कोई सक्रिय लोन या बकाया EMI नहीं है। क्या आप नए दुकान लोन के लिए पात्रता जाँचना चाहते हैं?"
                if lang == "hi" else
                "You do not have any active loan or pending EMI on file. Would you like to check eligibility for a new business loan?"
            )
            return reply(s, sid, lang, msg, [], "idle")

    if nlu.has_phrase(t, ["pay emi", "pay now", "emi bharo", "emi bharna hai", "emi chukao", "bhugtan karo", "पे ईएमआई"]) and st in ("idle", "amount"):
        u = USERS.get(s["user"], {})
        reminder = get_emi_reminder(u, lang)
        if reminder:
            reminder["status"] = "paid"
            s["emi_paid"] = True
            audit(sid, "emi_paid", loan_id=reminder["loan_id"], amount=reminder["amount"])
            ref = "PPB-EMI-" + uuid.uuid4().hex[:6].upper()
            msg = (
                f"धन्यवाद! {inr(reminder['amount'])} की EMI का भुगतान सफलतापूर्वक प्राप्त हो गया है। रसीद संदर्भ: {ref}।"
                if lang == "hi" else
                f"Thank you! Your EMI payment of {inr(reminder['amount'])} has been successfully processed. Receipt Ref: {ref}."
            )
            return reply(s, sid, lang, msg, [reminder], "idle")

    if nlu.has_phrase(t, ["remind tomorrow", "remind me tomorrow", "kal yaad dilao", "kal yaad dilana", "reminder set", "रिमाइंडर सेट"]) and st == "idle":
        audit(sid, "emi_reminder_scheduled")
        msg = (
            "रिमाइंडर सेट कर दिया गया है! हम देय तिथि से 1 दिन पहले सुबह 9 बजे आपको SMS और WhatsApp पर दोबारा सूचित करेंगे ताकि समय पर ऑटो-डेबिट हो सके।"
            if lang == "hi" else
            "Reminder scheduled! We will notify you again via SMS and WhatsApp 1 day prior to the due date so auto-debit succeeds."
        )
        return reply(s, sid, lang, msg, [], "idle")

    is_whatsapp_reminder = (
        nlu.has_phrase(t, ["whatsapp", "व्हाट्सएप", "व्हाट्सऐप", "वाट्सएप", "वाट्सऐप"]) and (
            nlu.has_phrase(t, ["reminder", "रिमाइंडर", "send", "भेजो", "bhejo", "alert", "अलर्ट", "message", "मैसेज", "notification", "सूचना", "notify", "bhej", "dila"])
            or len(nlu.tokens(t)) <= 3
        )
    ) or nlu.has_phrase(t, ["whatsapp reminder", "व्हाट्सएप रिमाइंडर", "send whatsapp", "whatsapp pe bhejo"])

    if is_whatsapp_reminder and st in ("idle", "amount"):
        u = USERS.get(s["user"], {})
        due_info = notifications.get_merchant_due_info(u, lang)
        if not due_info or s.get("emi_paid"):
            msg = (
                "आपके खाते में अभी कोई सक्रिय या बकाया लोन EMI नहीं है, इसलिए WhatsApp रिमाइंडर की आवश्यकता नहीं है।"
                if lang == "hi" else
                "You do not have any active loan or pending EMI on file to send a WhatsApp reminder for."
            )
            return reply(s, sid, lang, msg, [], "idle")

        phone = u.get("phone", "+919876543210")
        record = notifications.send_whatsapp_notification(
            merchant_name=u.get("name", "Merchant"),
            phone=phone,
            due_info=due_info,
            lang=lang
        )
        audit(sid, "whatsapp_notification_sent", phone=phone, loan_id=due_info["loan_id"], amount=due_info["amount"])
        card = {
            "type": "whatsapp_reminder_sent",
            "status": "delivered",
            "recipient_name": u.get("name", "Merchant"),
            "phone": record["phone"],
            "loan_id": due_info["loan_id"],
            "amount": due_info["amount"],
            "due_date": due_info["due_date"],
            "days_left": due_info["days_left"],
            "wa_link": record["wa_link"],
            "message": record["message"],
            "sent_at": record["sent_at"],
        }
        msg = (
            f"✅ {u['name']} जी के WhatsApp ({record['phone']}) पर {inr(due_info['amount'])} की EMI का रिमाइंडर भेज दिया गया है!\n\n"
            f"अंतिम तारीख: {due_info['due_date']} ({due_info['days_left']} दिन बाकी)। "
            f"मर्चेंट नीचे दिए गए लिंक से सीधे संदेश खोल सकते हैं।"
            if lang == "hi" else
            f"✅ WhatsApp installment reminder has been sent to {u['name']} ({record['phone']}) for EMI of {inr(due_info['amount'])}!\n\n"
            f"Due date: {due_info['due_date']} ({due_info['days_left']} days remaining). "
            f"You can also open this message directly in WhatsApp below."
        )
        return reply(s, sid, lang, msg, [card], "idle")

    if nlu.has_phrase(t, nlu.CRITERIA):
        u = USERS.get(s["user"], {})
        reasons = ["score"] if u.get("bureau", 0) < 650 else (["kyc"] if not u.get("kyc") else ["foir"])
        guidance = alternatives.get_criteria_pass_guidance(u, reasons, lang)
        audit(sid, "criteria_guidance_inquiry")
        msg = (
            "💡 बैंक लोन पात्रता और CIBIL स्कोर सुधारने के प्रमुख नियम नीचे दिए गए हैं। इनका पालन करके आप आसानी से लोन के लिए पात्र हो सकते हैं:"
            if lang == "hi" else
            "💡 Here is your strategic guide to elevate your CIBIL score and comfortably clear bank lending criteria:"
        )
        return reply(s, sid, lang, msg, [guidance], "idle")

    if nlu.has_phrase(t, nlu.ALTERNATIVES):
        u = USERS.get(s["user"], {})
        req = s.get("amount") or 2_000_000
        dec_data = s.get("decision") or {"eligible": True, "amount": 500_000}
        alt_card = alternatives.get_loan_alternatives(u, req, dec_data, lang)
        audit(sid, "loan_alternatives_inquiry")
        msg = (
            alt_card["stepping_stone_text"] + "\n\nनीचे दिए गए विकल्पों से आप अपनी ज़रूरत अनुसार लोन प्राप्त कर सकते हैं:"
            if lang == "hi" else
            alt_card["stepping_stone_text"] + "\n\nReview the alternative funding avenues outlined below:"
        )
        return reply(s, sid, lang, msg, [alt_card], "idle")

    if nlu.has_phrase(t, nlu.INS_PROTECT) and st in ("offer", "fees", "esign", "idle"):
        s["plan"] = "plus"
        s["product"] = "insurance"
        s["stage"] = "ins_consent"
        p = PLANS["plus"]
        audit(sid, "loan_insurance_protection_selected")
        msg = (
            f"उत्तम निर्णय! हमने आपके लोन के साथ '{p['name']}' (₹10 लाख स्वास्थ्य व लोन सुरक्षा, ₹12,900/साल) जोड़ दिया है। "
            f"पॉलिसी जारी करने के लिए आपका KYC नाम व उम्र देखना होगा। क्या आप सहमत हैं?"
            if lang == "hi" else
            f"Great choice! We have paired your loan with '{p['name']}' (₹10 Lakh Cover at ₹12,900/yr). "
            f"To issue the policy, I need to read your KYC name and age. Do you agree?"
        )
        return reply(s, sid, lang, msg, [{"type": "consent", "scope": ["KYC name", "Age"]}])

    if nlu.has_phrase(t, nlu.LOAN) or nlu.has_phrase(t, nlu.DUKAAN) or (amt and nlu.has_phrase(t, nlu.NEED)):
        if amt:
            s["amount"] = amt
        if ten:
            s["tenure"] = ten
        s["product"] = "loan"
        return begin_loan(s, sid, lang)

    if st == "amount" and amt:
        s["amount"] = amt
        return begin_loan(s, sid, lang)

    if nlu.has_phrase(t, nlu.CMP):
        s["stage"] = "idle"
        audit(sid, "compare_plans")
        msg = "Plus में इंतज़ार कम (2 साल), कमरे की सीमा नहीं और को-पेमेंट नहीं है; Basic सस्ता है पर इनमें सीमाएँ हैं।" if lang == "hi" else "Plus has a shorter wait (2 yrs), no room cap and no co-pay. Basic is cheaper but carries those limits."
        return reply(s, sid, lang, msg, [compare_card(lang)], "ins")

    if nlu.has_phrase(t, nlu.INS) or retrieve(t, k=1, threshold=0.85):
        hits = retrieve(t, k=2, threshold=0.32)
        intro_only = nlu.has_phrase(t, ["insurance", "बीमा", "bima", "health", "health plan"]) and not nlu.has_phrase(
            t, ["waiting", "room", "claim", "cover", "exclusion", "copay", "premium", "इंतज़ार", "कमरा", "क्लेम"]
        )
        if not hits and intro_only:
            s["stage"] = "idle"
            return reply(s, sid, lang, T("ins_hi", lang), [], "ins")
        if not hits:
            return handoff(s, sid, lang, "no_supporting_clause", nofound=True)
        s["stage"] = "idle"
        audit(sid, "rag_answer", clauses=[h["id"] for h in hits])
        txt = " ".join(h[lang] for h in hits)
        cards = [{"type": "clause", "id": h["id"], "plan": h["plan"], "title": h["title"], "text": h["en"], "hi": h["hi"]} for h in hits]
        return reply(s, sid, lang, txt, cards, "ins")

    # LLM Agent Fallback for natural conversational queries and unparsed voice queries
    u = USERS.get(s["user"], {})
    llm_text, llm_cards, llm_stage, _ = llm_agent.generate_llm_response(s, t, lang, u)
    if llm_text:
        s["unknown"] = 0
        s["stage"] = llm_stage
        audit(sid, "llm_agent_reply", query=t)
        return reply(s, sid, lang, llm_text, llm_cards, chip_key=llm_stage)

    s["unknown"] += 1
    if s["unknown"] >= 2:
        return handoff(s, sid, lang, "repeated_misunderstanding")
    return reply(s, sid, lang, T("unk", lang), [], "idle")


def create_human_review(s, sid, lang, review_type):
    s["handoff"] = True
    s["stage"] = f"{review_type}_review"
    s["review_type"] = review_type
    audit(sid, "human_review_requested", review_type=review_type)
    message = T(f"{review_type}_review_pending", lang)
    return reply(
        s,
        sid,
        lang,
        message,
        [{"type": "review_pending", "review_type": review_type}],
        "none",
    )


def submit_signature_for_review(s, sid, lang, kind):
    if kind == "loan":
        if s.get("stage") != "esign" or not s.get("decision") or not s["decision"].get("eligible"):
            raise HTTPException(409, "nothing to sign")
    elif s.get("stage") not in ("ins_quote", "ins_esign") or not s.get("plan"):
        raise HTTPException(409, "nothing to sign")
    return create_human_review(s, sid, lang, "signature")


@app.post("/api/consent/revoke")
def revoke(b: SidIn):
    s = S(b.sid)
    if s["consent"]:
        s["consent"]["revoked"] = True
        s["decision"] = None
        s["stage"] = "idle"
        audit(b.sid, "consent_revoked")
    return {"ok": True}


@app.post("/api/sign")
def sign(b: SidIn):
    s = S(b.sid)
    lang = s.get("lang") or "hi"
    if s["stage"] not in ("esign", "ins_quote", "ins_esign"):
        raise HTTPException(409, "nothing to sign")
    kind = "insurance" if s["stage"] in ("ins_quote", "ins_esign") else "loan"
    return submit_signature_for_review(s, b.sid, lang, kind)


@app.post("/api/kyc/review")
def request_kyc_review(b: SidIn):
    s = S(b.sid)
    lang = s.get("lang") or "hi"
    consent = s.get("consent")
    if not consent or consent.get("revoked") or consent.get("snapshot", {}).get("kyc") is not False:
        raise HTTPException(409, "KYC review requires active consent and an incomplete KYC record")
    decision = s.get("decision") or {}
    if s.get("stage") != "idle" or "kyc" not in decision.get("reasons", []):
        raise HTTPException(409, "KYC review is only available after an incomplete-KYC eligibility result")
    if s.get("review_type"):
        raise HTTPException(409, "A human review is already pending")
    return create_human_review(s, b.sid, lang, "kyc")


@app.get("/api/audit/{sid}")
def get_audit(sid: str):
    return S(sid)["audit"]


@app.get("/api/session/{sid}")
def get_session(sid: str, request: Request):
    require_admin(request)
    s = S(sid)
    u = USERS[s["user"]]
    return {
        "sid": sid,
        "user": s["user"],
        "profile": {"name": u["name"], "kind": u["kind"], "city": u["city"]},
        "stage": s["stage"],
        "lang": s.get("lang", "en"),
        "handoff": s["handoff"],
        "agent_connected": s["agent_connected"],
        "transcript": s["transcript"],
        "decision": s["decision"],
        "consent": s["consent"],
        "audit": s["audit"],
    }


@app.get("/api/sessions")
def list_sessions(request: Request):
    require_admin(request)
    return list_sessions_data()


@app.post("/api/agent/message")
def agent_message(b: AgentMsgIn, request: Request):
    require_admin(request)
    s = S(b.sid)
    t = (b.text or "").strip()
    if not t:
        raise HTTPException(400, "Message cannot be empty")
    if not s["handoff"] and not s["agent_connected"]:
        raise HTTPException(409, "Wait for the AI handoff prompt or intervene before replying")
    turn = {
        "role": "agent",
        "agent_name": b.agent_name,
        "text": t,
        "ts": time.strftime("%H:%M:%S"),
        "lang": s.get("lang", "en"),
    }
    if s["handoff"]:
        s["agent_connected"] = True
    s["transcript"].append(turn)
    audit(b.sid, "agent_turn", agent=b.agent_name, text=t, action=b.action)

    if b.action == "special_rate" and s.get("decision"):
        d = s["decision"]
        amt = d["amount"]
        ten = d["tenure"]
        d["rate"] = 12.0
        from .rules import emi
        new_emi = round(emi(amt, 12.0, ten))
        tp = round(new_emi * ten)
        d["emi"] = new_emi
        d["total_payable"] = tp
        d["total_interest"] = tp - amt
        s["decision"] = d
        turn["text"] += f" (Special Approved Rate: 12.0% p.a., New EMI: {inr(new_emi)})"
        audit(b.sid, "special_rate_applied", new_rate=12.0, emi=new_emi)

    return {"ok": True, "turn": turn, "stage": s["stage"], "decision": s["decision"]}


@app.post("/api/admin/login")
def admin_login(b: AdminLoginIn, request: Request, response: Response):
    if not (
        secrets.compare_digest(b.username, ADMIN_USERNAME)
        and secrets.compare_digest(b.password, ADMIN_PASSWORD)
    ):
        raise HTTPException(401, "Incorrect admin username or password")

    now = time.time()
    for token, expires_at in list(ADMIN_SESSIONS.items()):
        if expires_at <= now:
            ADMIN_SESSIONS.pop(token, None)
    token = secrets.token_urlsafe(32)
    ADMIN_SESSIONS[token] = now + ADMIN_SESSION_TTL
    response.set_cookie(
        "saytm_admin",
        token,
        max_age=ADMIN_SESSION_TTL,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"ok": True, "username": ADMIN_USERNAME}


@app.post("/api/admin/logout")
def admin_logout(request: Request, response: Response):
    token = request.cookies.get("saytm_admin")
    ADMIN_SESSIONS.pop(token or "", None)
    response.delete_cookie("saytm_admin", path="/", httponly=True, samesite="strict")
    return {"ok": True}


@app.get("/api/admin/me")
def admin_me(request: Request):
    require_admin(request)
    return {"username": ADMIN_USERNAME}


@app.get("/api/admin/sessions")
def admin_sessions(request: Request):
    require_admin(request)
    return list_sessions_data()


def list_sessions_data():
    out = []
    for sid, s in SESSIONS.items():
        u = USERS[s["user"]]
        out.append({
            "sid": sid,
            "created_at_ns": s["created_at_ns"],
            "name": u["name"],
            "stage": s["stage"],
            "review_type": s.get("review_type"),
            "handoff": s["handoff"],
            "agent_connected": s["agent_connected"],
            "status": "connected" if s["agent_connected"] else "waiting" if s["handoff"] else "active",
            "turns": len(s["transcript"]),
        })
    return sorted(out, key=lambda session: session["created_at_ns"], reverse=True)


@app.get("/api/admin/session/{sid}")
def admin_session(sid: str, request: Request):
    require_admin(request)
    s = S(sid)
    u = USERS[s["user"]]
    return {
        "sid": sid,
        "user": s["user"],
        "profile": {"name": u["name"], "kind": u["kind"], "city": u["city"]},
        "stage": s["stage"],
        "review_type": s.get("review_type"),
        "lang": s.get("lang", "en"),
        "handoff": s["handoff"],
        "agent_connected": s["agent_connected"],
        "transcript": s["transcript"],
        "decision": s["decision"],
        "consent": s["consent"],
        "audit": s["audit"],
    }


@app.post("/api/admin/session/{sid}/connect")
def admin_connect(sid: str, request: Request):
    require_admin(request)
    s = S(sid)
    if not s["handoff"]:
        raise HTTPException(409, "This customer has not requested a human agent")
    if not s["agent_connected"]:
        s["agent_connected"] = True
        turn = {
            "role": "agent",
            "agent_name": "Saytm Support",
            "text": "A human agent has joined the conversation.",
            "ts": time.strftime("%H:%M:%S"),
            "review_type": s.get("review_type"),
            "lang": s.get("lang", "en"),
        }
        s["transcript"].append(turn)
        audit(sid, "agent_connected")
    return {"ok": True, "agent_connected": True}


@app.post("/api/admin/session/{sid}/intervene")
def admin_intervene(sid: str, request: Request):
    require_admin(request)
    s = S(sid)
    if not s["agent_connected"]:
        s["handoff"] = True
        s["agent_connected"] = True
        s["stage"] = "handoff"
        language = s.get("lang", "en")
        s["transcript"].append({
            "role": "agent",
            "agent_name": "Saytm Support",
            "text": (
                "एक मानव एजेंट ने बातचीत संभाल ली है। AI सहायक अभी रुका हुआ है।"
                if language == "hi"
                else "A human agent has taken over the conversation. The AI assistant is paused."
            ),
            "ts": time.strftime("%H:%M:%S"),
            "lang": language,
            "system_event": "agent_takeover",
        })
        audit(sid, "agent_intervened")
    return {"ok": True, "agent_connected": True}


@app.get("/api/kfs/{sid}")
def get_kfs(sid: str):
    import hashlib
    s = S(sid)
    u = USERS[s["user"]]
    d = s.get("decision")
    if not d or not d.get("eligible"):
        raise HTTPException(404, "No active loan decision found for this session")

    amt = d["amount"]
    rate = d["rate"]
    ten = d["tenure"]
    monthly_rate = rate / 12 / 100
    emi_val = d["emi"]
    schedule = []
    bal = float(amt)
    for m in range(1, min(ten + 1, 7)):
        interest_comp = round(bal * monthly_rate)
        princ_comp = emi_val - interest_comp
        bal = max(0.0, bal - princ_comp)
        schedule.append({
            "month": m,
            "emi": emi_val,
            "principal": princ_comp,
            "interest": interest_comp,
            "balance": round(bal),
        })

    kfs_hash = hashlib.sha256(f"{sid}-{amt}-{ten}-{rate}-{d.get('disbursed')}".encode()).hexdigest()[:16].upper()

    return {
        "kfs_reference": f"KFS-PTM-{sid.upper()}-{int(time.time()) % 10000}",
        "kfs_hash": kfs_hash,
        "sanction_date": time.strftime("%d %b %Y"),
        "borrower": {
            "name": u["name"],
            "city": u["city"],
            "kind": u["kind"],
            "kyc_status": "Verified (Aadhaar / CKYC)",
            "credit_score": u["bureau"],
        },
        "lender": {
            "name": "Saytm Payments Bank / Partner NBFC",
            "registration": "RBI CoR: B-14.00281",
            "grievance_officer": "Ramesh Kumar Sharma (nodal.officer@saytm.com / 1800-120-130)",
        },
        "loan_terms": {
            "sanctioned_amount": d["amount"],
            "tenure_months": d["tenure"],
            "interest_rate_pct": d["rate"],
            "interest_type": "Reducing Balance (Fixed)",
            "apr_effective": round(d["rate"] + (d["fee"] / max(d["amount"], 1) * 12 / max(d["tenure"], 1) * 100), 2),
            "emi_monthly": d["emi"],
            "processing_fee": d["fee"],
            "gst": d["gst"],
            "net_disbursed": d["disbursed"],
            "total_interest": d["total_interest"],
            "total_payable": d["total_payable"],
            "foreclosure_charges": "NIL (Zero prepayment penalty)",
            "cooling_off_period": "3 Business Days (Full cancellation with zero penalty per RBI Digital Lending Norms)",
        },
        "amortization_preview": schedule,
    }


@app.get("/api/poll/{sid}")
def poll_session(sid: str, turns: str | int = 0):
    try:
        t_int = int(turns) if turns and str(turns).lower() not in ("undefined", "null", "") else 0
    except (ValueError, TypeError):
        t_int = 0
    if sid not in SESSIONS:
        return {
            "sid": sid,
            "session_expired": True,
            "stage": "idle",
            "handoff": False,
            "agent_connected": False,
            "total_turns": 0,
            "new_turns": [],
            "decision": None,
            "ref": None,
        }
    s = SESSIONS[sid]
    transcript = s.get("transcript", [])
    new_turns = transcript[t_int:] if t_int < len(transcript) else []
    return {
        "sid": sid,
        "stage": s["stage"],
        "handoff": s["handoff"],
        "agent_connected": s["agent_connected"],
        "total_turns": len(transcript),
        "new_turns": new_turns,
        "decision": s.get("decision"),
        "ref": s.get("ref"),
    }


@app.get("/v1/models")
def v1_models():
    return {"object": "list", "data": [{"id": "saytm-voice-agent", "object": "model", "owned_by": "saytm"}]}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" fill="#00baf2"/><text x="50" y="68" font-size="52" text-anchor="middle" fill="#002e6e" font-family="sans-serif" font-weight="bold">₹</text></svg>'
    return Response(content=svg, media_type="image/svg+xml")


app.mount("/static", StaticFiles(directory=FRONT), name="static")


@app.get("/")
def index():
    return FileResponse(FRONT / "index.html")


@app.get("/agent")
def agent_page():
    return FileResponse(FRONT / "admin.html")


@app.get("/admin")
def admin_page():
    return FileResponse(FRONT / "admin.html")

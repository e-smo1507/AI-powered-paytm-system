"""Saytm Voice Assistant orchestrator. Run: uvicorn backend.app:app --reload"""
import json
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import nlu
from .partners import PLANS, USERS, decide_plan, esign, fetch_bureau, fetch_inflows, fetch_kyc
from .rag import retrieve, CL
from .rules import decide

ROOT = Path(__file__).parent
FRONT = ROOT.parent / "frontend"
AUDIT_FILE = ROOT / "audit.jsonl"
SESSIONS: dict = {}

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
        "hi": "बढ़िया। नीचे Key Fact Statement देखें और e-sign से पुष्टि करें।",
        "en": "Great. Review the Key Fact Statement below and confirm with e-sign.",
    },
    "done": {
        "hi": "हो गया! {a} का लोन मंज़ूर है। 3 दिन की कूलिंग-ऑफ अवधि में आप बिना जुर्माने के रद्द कर सकते हैं। संदर्भ: {ref}",
        "en": "Done! Your {a} loan is approved. You can cancel within a 3-day cooling-off period without penalty. Ref: {ref}",
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


def S(sid):
    if sid not in SESSIONS:
        raise HTTPException(404, "unknown session")
    return SESSIONS[sid]


def chips(stage, lang):
    h = lang == "hi"
    return {
        "idle": ["मुझे 2 लाख का लोन चाहिए", "बीमा समझाओ", "दोनों प्लान की तुलना करो"] if h else ["I need a 2 lakh loan", "Explain health insurance", "Compare both plans"],
        "amount": ["2 लाख", "50 हज़ार", "1 लाख"] if h else ["2 lakh", "50 thousand", "1 lakh"],
        "consent": ["हाँ, सहमत हूँ", "नहीं"] if h else ["Yes, I agree", "No thanks"],
        "offer": ["हाँ, समझाओ", "24 महीने में", "एजेंट से बात करो"] if h else ["Yes, explain", "Use 24 months", "Talk to an agent"],
        "fees": ["हाँ, आगे बढ़ो", "एजेंट से बात करो"] if h else ["Yes, go ahead", "Talk to an agent"],
        "esign": ["e-sign करो"] if h else ["e-sign now"],
        "ins": ["वेटिंग पीरियड क्या है?", "कमरे के किराये की सीमा?", "Plus ले लो"] if h else ["What is the waiting period?", "Room rent limit?", "Take Plus"],
        "ins_consent": ["हाँ", "नहीं"] if h else ["Yes", "No"],
        "ins_quote": ["e-sign करो", "Basic बताओ"] if h else ["e-sign now", "Tell me about Basic"],
    }.get(stage, [])


def reply(s, sid, lang, text, cards=None, chip_key=None):
    s["transcript"].append({"role": "assistant", "text": text, "ts": time.strftime("%H:%M:%S")})
    return {
        "reply": text,
        "cards": cards or [],
        "chips": chips(chip_key or s["stage"], lang),
        "stage": s["stage"],
        "handoff": s["handoff"],
        "sid": sid,
    }


def offer_card(s):
    return {"type": "offer", **s["decision"], "inflow_basis": "12-month Saytm inflows"}


def offer_text(s, lang):
    d = s["decision"]
    pre = T("reduced", lang, a=inr(d["amount"])) if d["amount"] < (s["amount"] or 0) or "foir" in d["reasons"] else ""
    return pre + T("offer", lang, a=inr(d["amount"]), t=d["tenure"], e=inr(d["emi"]), r=d["rate"])


def run_decision(s, sid):
    d = decide(USERS[s["user"]], s["amount"], s["tenure"])
    s["decision"] = d.dict()
    audit(sid, "decision", amount=s["amount"], eligible=d.eligible, reasons=d.reasons, emi=d.emi)
    return d


def after_decision(s, sid, lang, d):
    if not d.eligible:
        s["stage"] = "idle"
        why = ", ".join(C["r"][r][lang] for r in d.reasons)
        return reply(s, sid, lang, T("inelig", lang, r=why), [{"type": "decline", "reasons": d.reasons}], "idle")
    s["stage"] = "offer"
    return reply(s, sid, lang, offer_text(s, lang), [offer_card(s)])


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
        user=b.user, lang=b.lang, stage="idle", amount=None, tenure=36, consent=None,
        decision=None, unknown=0, transcript=[], audit=[], handoff=False, plan=None, product=None,
    )
    audit(sid, "session_start", user=b.user)
    msg = T("greet", b.lang, n=u["name"])
    cards = []
    if u.get("hint"):
        msg += T("guide", b.lang, h=u["hint"])
        cards.append({"type": "guide", "event": u.get("life_event"), "hint": u["hint"]})
    SESSIONS[sid]["transcript"].append({"role": "assistant", "text": msg, "ts": time.strftime("%H:%M:%S")})
    return {
        "sid": sid,
        "reply": msg,
        "cards": cards,
        "chips": chips("idle", b.lang),
        "profile": {"name": u["name"], "kind": u["kind"], "city": u["city"], "age": u.get("age")},
    }


@app.post("/api/chat")
def chat(b: ChatIn):
    s, sid, lang, t = S(b.sid), b.sid, b.lang, (b.text or "").strip()
    if not t:
        return reply(s, sid, lang, T("unk", lang), [], "idle")
    s["lang"] = lang
    s["transcript"].append({"role": "user", "text": t, "ts": time.strftime("%H:%M:%S")})
    audit(sid, "user_turn", text=t)
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
        return do_sign(s, sid, lang, "loan")

    if st in ("ins_quote", "ins_esign") and (yes or nlu.has_phrase(t, ["esign", "e-sign", "sign", "साइन"])):
        return do_sign(s, sid, lang, "insurance")

    if nlu.has_phrase(t, nlu.BUY) or decide_plan(t):
        plan = decide_plan(t) or s.get("plan") or "plus"
        s["plan"] = plan
        s["product"] = "insurance"
        s["stage"] = "ins_consent"
        return reply(s, sid, lang, T("ins_consent", lang, p=PLANS[plan]["name"]), [{"type": "consent", "scope": ["KYC name", "Age"]}])

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

    s["unknown"] += 1
    if s["unknown"] >= 2:
        return handoff(s, sid, lang, "repeated_misunderstanding")
    return reply(s, sid, lang, T("unk", lang), [], "idle")


def do_sign(s, sid, lang, kind):
    if kind == "loan":
        if not s.get("decision") or not s["decision"].get("eligible"):
            raise HTTPException(409, "nothing to sign")
        d = s["decision"]
        ref = esign("loan", d["amount"])
        s["stage"] = "done"
        s["ref"] = ref
        audit(sid, "esigned", kind="loan", ref=ref, amount=d["amount"], emi=d["emi"])
        return reply(s, sid, lang, T("done", lang, a=inr(d["amount"]), ref=ref), [{"type": "receipt", "ref": ref, "kind": "loan", "amount": d["amount"]}], "none")
    p = PLANS[s.get("plan") or "plus"]
    ref = esign("insurance", p["premium"])
    s["stage"] = "done"
    s["ref"] = ref
    audit(sid, "esigned", kind="insurance", ref=ref, plan=p["name"])
    return reply(s, sid, lang, T("ins_done", lang, ref=ref), [{"type": "receipt", "ref": ref, "kind": "insurance", "amount": p["premium"]}], "none")


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
    if s["stage"] not in ("offer", "fees", "esign", "ins_quote", "ins_esign"):
        raise HTTPException(409, "nothing to sign")
    kind = "insurance" if s["stage"] in ("ins_quote", "ins_esign") else "loan"
    return do_sign(s, b.sid, lang, kind)


@app.get("/api/audit/{sid}")
def get_audit(sid: str):
    return S(sid)["audit"]


@app.get("/api/session/{sid}")
def get_session(sid: str):
    s = S(sid)
    u = USERS[s["user"]]
    return {
        "sid": sid,
        "user": s["user"],
        "profile": {"name": u["name"], "kind": u["kind"], "city": u["city"]},
        "stage": s["stage"],
        "handoff": s["handoff"],
        "transcript": s["transcript"],
        "decision": s["decision"],
        "consent": s["consent"],
        "audit": s["audit"],
    }


@app.get("/api/sessions")
def list_sessions():
    out = []
    for sid, s in SESSIONS.items():
        u = USERS[s["user"]]
        out.append({
            "sid": sid,
            "name": u["name"],
            "stage": s["stage"],
            "handoff": s["handoff"],
            "turns": len(s["transcript"]),
        })
    return list(reversed(out))


@app.post("/api/agent/message")
def agent_message(b: AgentMsgIn):
    s = S(b.sid)
    t = (b.text or "").strip()
    if not t:
        raise HTTPException(400, "Message cannot be empty")
    turn = {
        "role": "agent",
        "agent_name": b.agent_name,
        "text": t,
        "ts": time.strftime("%H:%M:%S"),
    }
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
def poll_session(sid: str, turns: int = 0):
    s = S(sid)
    transcript = s.get("transcript", [])
    new_turns = transcript[turns:] if turns < len(transcript) else []
    return {
        "sid": sid,
        "stage": s["stage"],
        "handoff": s["handoff"],
        "total_turns": len(transcript),
        "new_turns": new_turns,
        "decision": s.get("decision"),
        "ref": s.get("ref"),
    }


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
    return FileResponse(FRONT / "agent.html")

"""End-to-end demo journeys. Run: python -m backend.test_journeys"""
from fastapi.testclient import TestClient
from backend.app import app, SESSIONS

c = TestClient(app)


def start(user="sunita", lang="hi"):
    SESSIONS.clear()
    r = c.post("/api/start", json={"user": user, "lang": lang}).json()
    return r["sid"], r


def say(sid, text, lang="hi"):
    r = c.post("/api/chat", json={"sid": sid, "text": text, "lang": lang})
    assert r.status_code == 200, r.text
    return r.json()


def test_sunita_loan_esign():
    sid, r = start()
    assert "Sunita" in r["reply"]
    r = say(sid, "Mujhe dukaan ke liye 2 lakh ka loan chahiye")
    assert r["stage"] == "consent"
    r = say(sid, "haan")
    assert r["stage"] == "offer"
    assert any(x["type"] == "offer" for x in r["cards"])
    offer = next(x for x in r["cards"] if x["type"] == "offer")
    assert offer["eligible"] and offer["amount"] == 200000
    r = say(sid, "haan, samjhao")
    assert r["stage"] == "fees"
    r = say(sid, "haan aage badho")
    assert r["stage"] == "esign"
    r = c.post("/api/sign", json={"sid": sid}).json()
    assert r["stage"] == "done"
    assert "PTM-L" in r["reply"]


def test_reprice_24_months():
    sid, _ = start(lang="en")
    say(sid, "I need a 2 lakh loan", "en")
    say(sid, "yes", "en")
    r = say(sid, "24 months", "en")
    offer = next(x for x in r["cards"] if x["type"] == "offer")
    assert offer["tenure"] == 24
    assert offer["emi"] > 0


def test_do_lakh_hindi():
    sid, _ = start()
    r = say(sid, "do lakh ka loan chahiye")
    assert r["stage"] == "consent"
    assert "2,00,000" in r["reply"] or "Rs 2" in r["reply"]


def test_insurance_clause_and_buy():
    sid, _ = start(lang="en")
    r = say(sid, "what is the waiting period?", "en")
    assert any(x["type"] == "clause" for x in r["cards"])
    r = say(sid, "compare both plans", "en")
    assert any(x["type"] == "compare" for x in r["cards"])
    r = say(sid, "take Plus", "en")
    assert r["stage"] == "ins_consent"
    r = say(sid, "yes", "en")
    assert r["stage"] == "ins_quote"
    r = c.post("/api/sign", json={"sid": sid}).json()
    assert r["stage"] == "done"
    assert "PTM-H" in r["reply"]


def test_rahul_declined():
    sid, _ = start("rahul", "en")
    say(sid, "I need a 2 lakh loan", "en")
    r = say(sid, "yes", "en")
    assert "credit score" in r["reply"].lower()


def test_meena_kyc():
    sid, _ = start("meena", "en")
    say(sid, "I need a 50 thousand loan", "en")
    r = say(sid, "yes", "en")
    assert "kyc" in r["reply"].lower()


def test_handoff_and_agent():
    sid, _ = start("sunita", "en")
    r = say(sid, "talk to an agent", "en")
    assert r["handoff"] is True
    sess = c.get(f"/api/session/{sid}").json()
    assert sess["handoff"] is True
    assert c.get("/api/sessions").json()[0]["sid"] == sid


def test_low_confidence():
    sid, _ = start("sunita", "en")
    r1 = say(sid, "are dinosaur bites covered in this policy?", "en")
    r2 = say(sid, "what about unicorn fever treatment", "en")
    assert r1["handoff"] or r2["handoff"]


def test_kfs_generation():
    sid, _ = start("sunita", "en")
    say(sid, "I need a 2 lakh loan", "en")
    say(sid, "yes", "en")
    r = c.get(f"/api/kfs/{sid}")
    assert r.status_code == 200, r.text
    kfs = r.json()
    assert kfs["borrower"]["name"] == "Sunita"
    assert kfs["loan_terms"]["sanctioned_amount"] == 200000
    assert kfs["loan_terms"]["interest_rate_pct"] == 17.0
    assert len(kfs["amortization_preview"]) > 0
    assert "cooling_off_period" in kfs["loan_terms"]


def test_two_way_agent_message():
    sid, _ = start("sunita", "en")
    say(sid, "I need a 2 lakh loan", "en")
    say(sid, "yes", "en")
    say(sid, "talk to an agent", "en")
    # Agent sends message and special rate override
    r = c.post(
        "/api/agent/message",
        json={
            "sid": sid,
            "text": "Hello Sunita, I am offering you an exclusive 12% partner rate.",
            "action": "special_rate",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["decision"]["rate"] == 12.0
    # Customer polls and receives agent message
    poll = c.get(f"/api/poll/{sid}?turns=0").json()
    assert any(turn.get("role") == "agent" for turn in poll["new_turns"])


def test_empty_request_does_not_create_handoff():
    sid, r = start()
    r = c.post("/api/chat", json={"sid":sid,'text':"","lang":"hi"})
    assert r.json()["stage"] == "idle"

def test_invalid_user_start():
    r = c.post("/api/start", json={"user":"unknown","lang":"hi"})
    assert r.status_code == 400
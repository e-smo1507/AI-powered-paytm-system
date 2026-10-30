"""End-to-end demo journeys. Run: python -m backend.test_journeys"""
from fastapi.testclient import TestClient
from .app import app, SESSIONS

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
    assert "2,00,000" in r["reply"] or "₹2" in r["reply"]


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


def run():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print("OK", t.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", t.__name__, type(e).__name__, e)
    if failed:
        raise SystemExit(1)
    print(f"{len(tests)} journeys passed")


if __name__ == "__main__":
    run()

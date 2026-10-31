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
    assert c.post("/api/sign", json={"sid": sid}).status_code == 409
    r = say(sid, "haan, samjhao")
    assert r["stage"] == "fees"
    r = say(sid, "haan aage badho")
    assert r["stage"] == "esign"
    response = c.post("/api/sign", json={"sid": sid})
    assert response.status_code == 200, response.text
    r = response.json()
    assert r["stage"] == "signature_review"
    assert r["handoff"] is True
    assert any(card == {"type": "review_pending", "review_type": "signature"} for card in r["cards"])
    assert "मानव एजेंट की मंज़ूरी" in r["reply"]


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
    response = c.post("/api/sign", json={"sid": sid})
    assert response.status_code == 200, response.text
    r = response.json()
    assert r["stage"] == "signature_review"
    assert r["handoff"] is True
    assert any(card == {"type": "review_pending", "review_type": "signature"} for card in r["cards"])
    assert "human-agent approval" in r["reply"]


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
    assert any(card["type"] == "handoff" for card in r["cards"])
    assert c.post("/api/admin/login", json={"username": "admin", "password": "saytm-demo"}).status_code == 200
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
    assert c.post("/api/admin/login", json={"username": "admin", "password": "saytm-demo"}).status_code == 200
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


def test_agent_can_intervene_before_handoff_and_pause_ai():
    sid, _ = start("sunita", "hi")
    assert c.post("/api/admin/login", json={"username": "admin", "password": "saytm-demo"}).status_code == 200
    assert c.get("/api/admin/sessions").json()[0]["status"] == "active"
    premature = c.post("/api/agent/message", json={"sid": sid, "text": "Hello", "agent_name": "Support"})
    assert premature.status_code == 409

    intervened = c.post(f"/api/admin/session/{sid}/intervene", json={})
    assert intervened.status_code == 200
    details = c.get(f"/api/admin/session/{sid}").json()
    assert details["handoff"] is True
    assert details["agent_connected"] is True
    takeover = details["transcript"][-1]
    assert takeover["text"] == "एक मानव एजेंट ने बातचीत संभाल ली है। AI सहायक अभी रुका हुआ है।"
    assert takeover["lang"] == "hi"
    assert takeover["system_event"] == "agent_takeover"

    before = len(details["transcript"])
    customer_message = c.post("/api/chat", json={"sid": sid, "text": "I still need help", "lang": "en"}).json()
    assert customer_message["reply"] == ""
    after = c.get(f"/api/admin/session/{sid}").json()["transcript"]
    assert len(after) == before + 1
    assert after[-1]["role"] == "user"

    agent_message = c.post("/api/agent/message", json={"sid": sid, "text": "I can help with that", "agent_name": "Support"})
    assert agent_message.status_code == 200


def test_admin_login_and_waiting_queue():
    sid, _ = start("meena", "en")
    say(sid, "talk to an agent", "en")
    unauthenticated = TestClient(app)
    assert unauthenticated.get("/api/admin/sessions").status_code == 401
    assert c.post("/api/admin/login", json={"username": "admin", "password": "wrong"}).status_code == 401
    assert c.post("/api/admin/login", json={"username": "admin", "password": "saytm-demo"}).status_code == 200
    queue = c.get("/api/admin/sessions")
    assert queue.status_code == 200
    assert queue.json()[0]["sid"] == sid
    assert queue.json()[0]["status"] == "waiting"
    details = c.get(f"/api/admin/session/{sid}").json()
    assert details["handoff"] is True
    assert c.post(f"/api/admin/session/{sid}/connect").json()["agent_connected"] is True
    poll = c.get(f"/api/poll/{sid}?turns=0").json()
    assert poll["agent_connected"] is True


def test_admin_queue_shows_newest_chat_first():
    SESSIONS.clear()
    first = c.post("/api/start", json={"user": "sunita", "lang": "en"}).json()
    second = c.post("/api/start", json={"user": "rahul", "lang": "en"}).json()
    assert c.post("/api/admin/login", json={"username": "admin", "password": "saytm-demo"}).status_code == 200

    queue = c.get("/api/admin/sessions")
    assert queue.status_code == 200
    sessions = queue.json()
    assert [session["sid"] for session in sessions] == [second["sid"], first["sid"]]
    assert sessions[0]["created_at_ns"] > sessions[1]["created_at_ns"]


def test_admin_page_is_available():
    assert c.get("/admin").status_code == 200


def test_customer_app_starts_with_welcome_and_no_chat():
    response = c.get("/")
    assert response.status_code == 200
    assert 'id="chat-area" hidden' in response.text
    assert 'data-user="sunita"' in response.text
    assert 'data-user="rahul"' in response.text
    assert 'data-user="meena"' in response.text
    assert 'id="user"' not in response.text
    assert 'id="login"' not in response.text
    assert 'href="/admin" target="_blank"' in response.text


def test_kyc_help_enters_waiting_handoff():
    sid, _ = start("meena", "en")
    say(sid, "I need a 2 lakh loan", "en")
    say(sid, "yes", "en")
    r = say(sid, "talk to an agent for KYC help", "en")
    assert r["handoff"] is True
    assert r["stage"] == "handoff"
    assert any(card["type"] == "handoff" for card in r["cards"])
    poll = c.get(f"/api/poll/{sid}").json()
    assert poll["agent_connected"] is False


def test_kyc_review_waits_for_human_approval():
    sid, _ = start("meena", "en")
    assert c.post("/api/kyc/review", json={"sid": sid}).status_code == 409
    say(sid, "I need a 2 lakh loan", "en")
    decline = say(sid, "yes", "en")
    assert "kyc" in decline["cards"][0]["reasons"]

    response = c.post("/api/kyc/review", json={"sid": sid})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["stage"] == "kyc_review"
    assert result["handoff"] is True
    assert any(card == {"type": "review_pending", "review_type": "kyc"} for card in result["cards"])
    assert "human-agent approval" in result["reply"]
    assert c.post("/api/kyc/review", json={"sid": sid}).status_code == 409

    assert c.post("/api/admin/login", json={"username": "admin", "password": "saytm-demo"}).status_code == 200
    queued = next(item for item in c.get("/api/admin/sessions").json() if item["sid"] == sid)
    assert queued["review_type"] == "kyc"
    details = c.get(f"/api/admin/session/{sid}").json()
    assert details["review_type"] == "kyc"


def test_empty_request_does_not_create_handoff():
    sid, r = start()
    r = c.post("/api/chat", json={"sid":sid,'text':"","lang":"hi"})
    assert r.json()["stage"] == "idle"

def test_invalid_user_start():
    r = c.post("/api/start", json={"user":"unknown","lang":"hi"})
    assert r.status_code == 400


def test_merchant_emi_reminder_proactive():
    sid, r = start("sunita", "hi")
    assert "EMI रिमाइंडर" in r["reply"]
    assert any(card.get("type") == "emi_reminder" for card in r["cards"])
    emi_card = next(card for card in r["cards"] if card.get("type") == "emi_reminder")
    assert emi_card["amount"] == 4850
    assert emi_card["days_left"] == 3
    assert emi_card["status"] == "upcoming"


def test_merchant_emi_reminder_5day():
    from backend.app import USERS
    original = USERS["sunita"]["active_loan"]["due_day_offset"]
    try:
        USERS["sunita"]["active_loan"]["due_day_offset"] = 5
        sid, r = start("sunita", "hi")
        assert "EMI रिमाइंडर" in r["reply"]
        assert any(card.get("type") == "emi_reminder" for card in r["cards"])
        emi_card = next(card for card in r["cards"] if card.get("type") == "emi_reminder")
        assert emi_card["amount"] == 4850
        assert emi_card["days_left"] == 5
        assert emi_card["status"] == "upcoming"
    finally:
        USERS["sunita"]["active_loan"]["due_day_offset"] = original


def test_merchant_emi_query_and_payment():
    sid, r = start("sunita", "hi")
    r = say(sid, "meri agli EMI kab hai?", "hi")
    assert any(card.get("type") == "emi_reminder" for card in r["cards"])
    assert "4,850" in r["reply"] or "4850" in r["reply"]

    rem = say(sid, "kal yaad dilana", "hi")
    assert "रिमाइंडर सेट" in rem["reply"]

    pay_res = c.post("/api/emi/pay", json={"sid": sid, "loan_id": "LN-KIRANA-8821"})
    assert pay_res.status_code == 200
    res_data = pay_res.json()
    assert "सफलतापूर्वक" in res_data["reply"]
    paid_card = next(card for card in res_data["cards"] if card.get("type") == "emi_reminder")
    assert paid_card["status"] == "paid"


def test_merchant_without_loan_emi_query():
    sid, r = start("meena", "en")
    r = say(sid, "when is my next EMI due?", "en")
    assert "do not have any active loan" in r["reply"]


def test_poll_session_not_found_recovery():
    SESSIONS.clear()
    r = c.get("/api/poll/9985b0f6?turns=undefined")
    assert r.status_code == 200
    data = r.json()
    assert data["session_expired"] is True
    assert data["sid"] == "9985b0f6"


def test_chat_auto_revives_expired_session():
    SESSIONS.clear()
    r = c.post("/api/chat", json={"sid": "deadbeef", "text": "namaste", "lang": "hi"})
    assert r.status_code == 200
    data = r.json()
    assert "नमस्ते" in data["reply"] or "पेटीएम" in data["reply"]


def test_llm_agent_conversational_queries():
    SESSIONS.clear()
    sid, r = start("sunita", "hi")
    r1 = say(sid, "loan ke baare me batao", "hi")
    assert "2,00,000" in r1["reply"] or "लोन" in r1["reply"]
    r2 = say(sid, "interest kitna lagega", "hi")
    assert "14%" in r2["reply"]
    r3 = say(sid, "mera credit score kaisa hai", "hi")
    assert "740" in r3["reply"]


def test_merchant_whatsapp_notification_endpoints():
    r = c.get("/api/notifications/merchant/sunita")
    assert r.status_code == 200
    data = r.json()
    assert data["has_loan"] is True
    assert data["merchant_name"] == "Sunita"
    assert "4,850" in data["due_info"]["amount_inr"] or data["due_info"]["amount"] == 4850
    assert "wa_link" in data["preview"]["hi"]
    assert "https://wa.me/" in data["preview"]["hi"]["wa_link"]

    send_res = c.post("/api/notifications/whatsapp/send", json={"user_id": "sunita", "lang": "hi"})
    assert send_res.status_code == 200
    res_data = send_res.json()
    assert res_data["ok"] is True
    assert res_data["notification"]["status"] == "delivered"
    assert "wa.me" in res_data["notification"]["wa_link"]

    hist_res = c.get("/api/notifications/history")
    assert hist_res.status_code == 200
    assert hist_res.json()["count"] >= 1


def test_merchant_whatsapp_reminder_via_chat():
    SESSIONS.clear()
    sid, r = start("sunita", "hi")
    chat_res = say(sid, "WhatsApp par reminder bhejo", "hi")
    assert any(card.get("type") == "whatsapp_reminder_sent" for card in chat_res["cards"])
    wa_card = next(card for card in chat_res["cards"] if card.get("type") == "whatsapp_reminder_sent")
    assert wa_card["status"] == "delivered"
    assert "wa.me" in wa_card["wa_link"]
    assert wa_card["amount"] == 4850
    assert "WhatsApp" in chat_res["reply"]


def test_merchant_without_loan_whatsapp_reminder():
    SESSIONS.clear()
    sid, r = start("meena", "en")
    chat_res = say(sid, "send whatsapp reminder", "en")
    assert "do not have any active loan" in chat_res["reply"]


def test_twenty_lakh_loan_alternatives_and_insurance_recommendation():
    SESSIONS.clear()
    sid, r = start("sunita", "hi")
    r1 = say(sid, "Mujhe 20 lakh ka loan chahiye", "hi")
    assert r1["stage"] == "consent"
    r2 = say(sid, "haan", "hi")
    assert r2["stage"] == "offer"
    assert any(card.get("type") == "offer" for card in r2["cards"])
    assert any(card.get("type") == "loan_alternatives" for card in r2["cards"])
    alt_card = next(c for c in r2["cards"] if c.get("type") == "loan_alternatives")
    assert alt_card["requested_amount"] == 2_000_000
    assert "CIBIL" in alt_card["stepping_stone_text"] or "CIBIL" in r2["reply"]
    assert any(card.get("type") == "loan_insurance_rec" for card in r2["cards"])
    ins_card = next(c for c in r2["cards"] if c.get("type") == "loan_insurance_rec")
    assert "SecureHealth" in ins_card["plan_name"]
    assert "🛡️" in r2["reply"] or "सुरक्षा" in r2["reply"]


def test_declined_merchant_receives_criteria_pass_guidance():
    SESSIONS.clear()
    sid, r = start("rahul", "hi")
    r1 = say(sid, "Mujhe dukaan ke liye loan chahiye", "hi")
    assert r1["stage"] == "amount"
    r2 = say(sid, "1 lakh", "hi")
    assert r2["stage"] == "consent"
    r3 = say(sid, "haan", "hi")
    assert r3["stage"] == "idle"
    assert any(card.get("type") == "decline" for card in r3["cards"])
    assert any(card.get("type") == "criteria_tips" for card in r3["cards"])
    crit_card = next(c for c in r3["cards"] if c.get("type") == "criteria_tips")
    assert any("CIBIL" in step["category"] for step in crit_card["steps"])
    assert any(card.get("type") == "loan_alternatives" for card in r3["cards"])


def test_merchant_adds_insurance_protection_to_loan():
    SESSIONS.clear()
    sid, r = start("sunita", "hi")
    say(sid, "2 lakh ka loan", "hi")
    say(sid, "haan", "hi")
    ins_reply = say(sid, "बीमा सुरक्षा जोड़ें", "hi")
    assert ins_reply["stage"] == "ins_consent"
    assert "SecureHealth" in ins_reply["reply"] or "सुरक्षा" in ins_reply["reply"]





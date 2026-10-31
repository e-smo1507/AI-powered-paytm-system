"""Merchant loan alternatives, bank criteria guidance, and loan protection insurance engine.
Provides actionable advice for non-eligible merchants (CIBIL building stepping stones),
bank criteria-passing blueprints, and post-loan insurance recommendations.
"""
from typing import Any, Dict, List, Optional


def inr_fmt(n: int | float) -> str:
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


def get_loan_alternatives(
    profile: dict,
    requested_amount: int,
    decision: dict,
    lang: str = "hi"
) -> Dict[str, Any]:
    """Generates stepping-stone loans (e.g. ₹5 Lakhs now to build CIBIL for ₹20 Lakhs later)

    and alternative merchant financing schemes.
    """
    req_amt = int(requested_amount or 0)
    eligible = decision.get("eligible", False)
    approved_amt = decision.get("amount", 0)
    max_cap = 500_000  # Instant digital unsecured cap is 5 Lakhs
    suggested_starter = min(max_cap, max(approved_amt, 200_000 if eligible else 100_000))

    if lang == "hi":
        stepping_stone_text = (
            f"💡 **बड़ा लोन पाने का सर्वोत्तम रास्ता (Stepping-Stone Strategy):**\n"
            f"आपने {inr_fmt(req_amt)} के लोन के लिए पूछा है, लेकिन वर्तमान में डिजिटल अनसिक्योर्ड लोन की तत्काल सीमा {inr_fmt(max_cap)} है।\n"
            f"हमारा सुझाव है कि आप अभी **{inr_fmt(suggested_starter)} का लोन** लें। अगले 6 से 12 महीने समय पर EMI भरकर अपना CIBIL स्कोर 750+ मजबूत करें। "
            f"इसके बाद बैंक आपको {inr_fmt(req_amt)} या उससे भी अधिक का बड़ा लोन आसानी से और कम ब्याज पर स्वीकृत कर देंगे।"
        )
        schemes = [
            {
                "title": f"1. {inr_fmt(suggested_starter)} का स्टार्टर बिज़नेस लोन (CIBIL बिल्डर)",
                "desc": "अभी छोटा लोन लेकर समय पर चुकाएँ ताकि CIBIL स्कोर 750+ बने और भविष्य में 20 लाख के बड़े लोन का रास्ता खुले।",
                "tag": "सर्वोत्तम विकल्प",
                "action": f"{inr_fmt(suggested_starter)} के लिए आवेदन करें",
            },
            {
                "title": "2. प्रधानमंत्री मुद्रा योजना (PMMY - तरुण लोन)",
                "desc": f"साझेदार सरकारी बैंकों के माध्यम से ₹10 लाख से ₹20 लाख तक का एमएसएमई लोन (CGTMSE सरकारी गारंटी के साथ)।",
                "tag": "सरकारी योजना",
                "action": "मुद्रा लोन विवरण",
            },
            {
                "title": "3. Paytm साउंडबॉक्स डेली डिडक्शन लोन (Daily EDC/QR Loan)",
                "desc": "दुकान के दैनिक UPI/QR कलेक्शन से प्रतिदिन छोटी किस्त कटेगी। मासिक EMI का बोझ नहीं रहता और कम सिबिल पर भी उपलब्ध।",
                "tag": "दैनिक कटौती",
                "action": "QR लोन समझें",
            },
            {
                "title": "4. सिक्योर्ड लोन / गोल्ड लोन (Secured Business Credit)",
                "desc": f"दुकान या सोने की सुरक्षा पर तुरंत ₹20 लाख तक का लोन, 9% से 11% की बहुत कम ब्याज दर पर।",
                "tag": "कम ब्याज दर",
                "action": "सिक्योर्ड लोन देखें",
            },
        ]
    else:
        stepping_stone_text = (
            f"💡 **Recommended Stepping-Stone Pathway to Secure {inr_fmt(req_amt)}:**\n"
            f"You requested {inr_fmt(req_amt)}, but instant collateral-free digital merchant loans are currently capped at {inr_fmt(max_cap)}.\n"
            f"**Recommendation:** Take a **{inr_fmt(suggested_starter)} stepping-stone loan** now. By servicing EMIs on time for 6-12 months, "
            f"you elevate your CIBIL score to 750+ and establish a rock-solid repayment pedigree, unlocking your full {inr_fmt(req_amt)} loan with lower interest rates thereafter."
        )
        schemes = [
            {
                "title": f"1. {inr_fmt(suggested_starter)} Starter Working Capital (CIBIL Builder)",
                "desc": "Start with this approved credit line to build a 750+ score and qualify for ₹20 Lakhs in 6-12 months.",
                "tag": "Recommended",
                "action": f"Apply for {inr_fmt(suggested_starter)}",
            },
            {
                "title": "2. Pradhan Mantri Mudra Yojana (PMMY - Tarun Category)",
                "desc": "Government-backed credit guarantee (CGTMSE) for ₹10 Lakh to ₹20 Lakh loans through partner banks.",
                "tag": "Govt Scheme",
                "action": "Explore Mudra Loan",
            },
            {
                "title": "3. Paytm Soundbox Daily Collection Loan (EDC/QR Swipes)",
                "desc": "Micro-deductions from daily shop customer UPI payments. Flexible repayment with relaxed credit score criteria.",
                "tag": "Daily Deduction",
                "action": "Explore QR Loan",
            },
            {
                "title": "4. Secured MSME / Gold Loan for Working Capital",
                "desc": f"Instant sanction up to {inr_fmt(req_amt)} against business assets or gold at attractive 9-11% p.a. rates.",
                "tag": "Low Interest",
                "action": "View Secured Options",
            },
        ]

    return {
        "type": "loan_alternatives",
        "requested_amount": req_amt,
        "max_digital_cap": max_cap,
        "suggested_starter": suggested_starter,
        "stepping_stone_text": stepping_stone_text,
        "schemes": schemes,
    }


def get_criteria_pass_guidance(
    profile: dict,
    reasons: list[str],
    lang: str = "hi"
) -> Dict[str, Any]:
    """Generates practical, actionable steps for a merchant to pass bank lending criteria."""
    score = profile.get("bureau", 0)
    vintage = profile.get("vintage_months", 0)
    kyc_status = profile.get("kyc", False)

    steps = []

    # 1. CIBIL score improvement advice
    if "score" in reasons or score < 650:
        if lang == "hi":
            steps.append({
                "category": "CIBIL स्कोर (क्रेडिट स्कोर) कैसे 750+ करें",
                "current": f"वर्तमान स्कोर: {score} (बैंक न्यूनतम 650 मांगते हैं)",
                "actions": [
                    "✓ **100% समय पर भुगतान:** बिजली बिल, मोबाइल पोस्टपेड, या मौजूदा किस्तों का देय तिथि से 2 दिन पहले भुगतान करें। 6 महीने में स्कोर 40-70 अंक बढ़ जाएगा।",
                    "✓ **क्रेडिट लिमिट का 30% से कम उपयोग:** यदि क्रेडिट कार्ड या ओवरड्राफ्ट है, तो कभी भी सीमा का 30% से अधिक खर्च न करें।",
                    "✓ **बार-बार आवेदन न करें:** एक साथ कई लोन ऐप्स या बैंकों में आवेदन करने से CIBIL में 'हार्ड इन्क्वायरी' दर्ज होती है और स्कोर गिरता है।",
                    "✓ **FD-समर्थित सुरक्षित कार्ड:** ₹10,000 की छोटी FD पर क्रेडिट कार्ड लेकर महीने का छोटा खर्च समय पर भरें, इससे तेजी से क्रेडिट इतिहास बनता है।",
                ],
            })
        else:
            steps.append({
                "category": "How to Elevate CIBIL Score to 750+",
                "current": f"Current Score: {score} (Banks require minimum 650)",
                "actions": [
                    "✓ **Zero-Delay Repayments:** Clear all credit card bills, utility payments, and existing dues 2 days prior to due dates. This boosts score by 40-70 points in 3-6 months.",
                    "✓ **Keep Credit Utilization Below 30%:** Never exhaust more than 30% of your sanction limit on credit cards or overdraft lines.",
                    "✓ **Stop Multiple Simultaneous Inquiries:** Avoid applying across multiple loan apps in the same month to prevent hard inquiry score penalties.",
                    "✓ **Build Clean History via Secured Credit:** Use an FD-backed starter credit line (₹10k-₹20k) to record continuous positive on-time payment track records.",
                ],
            })

    # 2. Inflows & FOIR advice
    if "foir" in reasons or profile.get("monthly_inflow"):
        if lang == "hi":
            steps.append({
                "category": "मासिक आय एवं बैंकिंग टर्नओवर (FOIR) कैसे बढ़ाएँ",
                "current": "बैंक नियम: मासिक EMI आपकी औसत आय के 40% से अधिक नहीं होनी चाहिए",
                "actions": [
                    "✓ **Paytm QR / साउंडबॉक्स से 100% कलेक्शन:** दुकान की सभी नकद बिक्री को Paytm QR कोड से बैंक खाते में लें ताकि बैंक को प्रमाणित आय दिखे।",
                    "✓ **सह-आवेदक (Co-Applicant) जोड़ें:** परिवार के कमाऊ सदस्य या जीवनसाथी को सह-आवेदक बनाकर लोन पात्रता 50% तक बढ़ाएँ।",
                    "✓ **लंबी अवधि (Tenure) चुनें:** 24 महीने के बजाय 36 या 48 महीने की अवधि चुनने से मासिक EMI घटती है और बैंक आसानी से पास कर देते हैं।",
                ],
            })
        else:
            steps.append({
                "category": "How to Boost Digital Inflows & Clear FOIR Norms",
                "current": "Bank Benchmark: Monthly EMI must not exceed 40% of verified business inflows",
                "actions": [
                    "✓ **Route 100% Store Collections via Paytm QR:** Shift cash collections to your Paytm QR & Soundbox to establish higher verified digital turnover.",
                    "✓ **Add an Earning Co-Borrower:** Adding a working spouse or family member as co-applicant increases eligibility by up to 50%.",
                    "✓ **Opt for Longer Tenure (36-48 Months):** Spreading repayments across longer tenures lowers monthly EMI, keeping it well within the 40% FOIR limit.",
                ],
            })

    # 3. KYC and Vintage advice
    if "kyc" in reasons or not kyc_status:
        if lang == "hi":
            steps.append({
                "category": "डिजिटल KYC तुरंत पूरा करने का तरीका",
                "current": "KYC स्थिति: अपूर्ण (Incomplete)",
                "actions": [
                    "✓ **3 मिनट में वीडियो KYC:** आधार नंबर और पैन कार्ड के साथ तुरंत ऑनलाइन वीडियो KYC पूरा करें।",
                    "✓ **CKYC सत्यापन:** आधार से लिंक मोबाइल नंबर पर OTP प्राप्त कर बैंक सत्यापन पूरा करें।",
                ],
            })
        else:
            steps.append({
                "category": "Complete Paperless Video KYC",
                "current": "KYC Status: Pending / Incomplete",
                "actions": [
                    "✓ **Instant Video KYC in 3 Minutes:** Complete one-time paperless video verification with your Aadhaar and PAN card.",
                    "✓ **Aadhaar CKYC Authentication:** Authenticate via OTP on your Aadhaar-linked mobile number for instant verification.",
                ],
            })

    if "vintage" in reasons or vintage < 6:
        if lang == "hi":
            steps.append({
                "category": "बिज़नेस विंटेज (खाता इतिहास) पूरा करना",
                "current": f"वर्तमान विंटेज: {vintage} महीने (बैंक 6+ महीने मांगते हैं)",
                "actions": [
                    "✓ **नियमित UPI लेन-देन:** अगले कुछ महीने रोज़ाना कम से कम 5-10 UPI ग्राहक लेन-देन जारी रखें। 6 महीने पूरे होते ही लोन स्वतः स्वीकृत हो जाएगा।",
                ],
            })
        else:
            steps.append({
                "category": "Establish 6-Month Business Vintage",
                "current": f"Current History: {vintage} months (Banks require 6+ months)",
                "actions": [
                    "✓ **Active UPI Transaction History:** Maintain regular daily UPI merchant transactions. Once 6 months vintage is logged, pre-approved offers unlock automatically.",
                ],
            })

    return {
        "type": "criteria_tips",
        "merchant_name": profile.get("name", "Merchant"),
        "steps": steps,
    }


def get_loan_insurance_recommendation(
    decision: dict,
    profile: dict,
    lang: str = "hi"
) -> Dict[str, Any]:
    """Recommends suitable insurance (health & shop shield) when a merchant gets a loan,

    safeguarding their working capital and ensuring repayment continuity.
    """
    amt = decision.get("amount", 200_000)
    emi_val = decision.get("emi", 4850)

    # We recommend SecureHealth Plus (₹10 Lakh sum insured, ₹12,900/year, ~₹35/day)
    # or SecureHealth Basic (₹5 Lakh, ₹8,400/year, ~₹23/day)
    plan_key = "plus" if amt >= 150_000 else "basic"
    plan_name = "Paytm SecureHealth Plus (व्यापारी सुरक्षा शील्ड)" if plan_key == "plus" else "Paytm SecureHealth Basic"
    sum_insured_str = "₹10 लाख" if plan_key == "plus" else "₹5 लाख"
    premium_str = "₹12,900/साल (मात्र ₹35/दिन)" if plan_key == "plus" else "₹8,400/साल (मात्र ₹23/दिन)"

    if lang == "hi":
        rationale = (
            f"🛡️ **लोन के साथ बीमा क्यों आवश्यक है?**\n"
            f"अकस्मात बीमारी या दुकान में अप्रत्याशित क्षति (आग, चोरी, जल भराव) छोटे व्यापारियों के लोन डिफ़ॉल्ट का मुख्य कारण बनती है। "
            f"**{plan_name}** लेने से अस्पताल का सारा खर्च बीमा कंपनी सीधे (कैशलेस) वहन करेगी, जिससे आपकी दुकान की कार्यशील पूंजी "
            f"और लोन की मासिक EMI ({inr_fmt(emi_val)}) दोनों पूरी तरह सुरक्षित रहेंगी।"
        )
        highlights = [
            f"✓ {sum_insured_str} का 100% कैशलेस अस्पताल कवर (10,000+ नेटवर्क अस्पताल)",
            "✓ कमरे के किराये (Room Rent) पर कोई कैपिंग नहीं",
            "✓ पहले से मौजूद बीमारियों पर केवल 2 वर्ष का न्यूनतम वेटिंग पीरियड",
            "✓ लोन सुरक्षा शील्ड: आपात स्थिति में दुकान और परिवार पर कर्ज का बोझ नहीं पड़ेगा",
        ]
        cta_text = "🛡️ इस लोन के साथ बीमा सुरक्षा जोड़ें"
        decline_text = "अभी केवल लोन आगे बढ़ाएँ"
    else:
        plan_name = "Paytm SecureHealth Plus (Merchant Shield)" if plan_key == "plus" else "Paytm SecureHealth Basic"
        sum_insured_str = "₹10 Lakh" if plan_key == "plus" else "₹5 Lakh"
        premium_str = "₹12,900/yr (~₹35/day)" if plan_key == "plus" else "₹8,400/yr (~₹23/day)"
        rationale = (
            f"🛡️ **Why Pair Your Loan with Insurance Protection?**\n"
            f"Medical emergencies or unforeseen shop damage are the #1 reason merchant loans turn overdue. "
            f"Pairing your loan with **{plan_name}** ensures 100% cashless hospitalization, safeguarding your working capital "
            f"so your monthly installment ({inr_fmt(emi_val)}) continues uninterrupted without straining your family or store."
        )
        highlights = [
            f"✓ {sum_insured_str} comprehensive cashless coverage across 10,000+ partner hospitals",
            "✓ Zero Room Rent capping or proportionate deduction",
            "✓ Short 2-year waiting period for pre-existing ailments",
            "✓ Debt-free safety net protecting family and business livelihood",
        ]
        cta_text = "🛡️ Add Insurance Protection to Loan"
        decline_text = "Proceed with loan only"

    return {
        "type": "loan_insurance_rec",
        "plan_key": plan_key,
        "plan_name": plan_name,
        "sum_insured": sum_insured_str,
        "premium": premium_str,
        "rationale": rationale,
        "highlights": highlights,
        "cta_text": cta_text,
        "decline_text": decline_text,
    }


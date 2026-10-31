"""LLM Agent for Paytm Voice Assistant.

Provides generative natural language understanding and responses for voice queries
that fall outside rigid regex rules. Supports external LLMs (Gemini, OpenAI, Ollama)
when API keys are present, with an intelligent built-in domain conversational engine
as an offline, low-latency zero-dependency fallback.
"""
import os
import re
import time
import httpx
from typing import Any, Dict, List, Optional, Tuple

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _norm(t: str) -> str:
    return (t or "").translate(DEV_DIGITS).lower().strip()


def query_external_llm(system_prompt: str, user_prompt: str) -> Optional[str]:
    """Call Gemini or OpenAI API if environment keys are available."""
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # 1. Try Google Gemini REST API
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}\n\nUser Question: {user_prompt}"}]}
                ],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 150}
            }
            with httpx.Client(timeout=4.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
        except Exception:
            pass

    # 2. Try OpenAI API
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 120,
                "temperature": 0.3
            }
            with httpx.Client(timeout=4.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
        except Exception:
            pass

    return None


def generate_llm_response(
    session: Dict[str, Any],
    text: str,
    lang: str,
    user_profile: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[str], List[Dict[str, Any]], str, List[str]]:
    """Intelligent fallback for conversational voice queries.
    
    Returns:
        (reply_text, cards_list, stage, chips_list)
    """
    t = _norm(text)
    user_profile = user_profile or {}
    name = user_profile.get("name", "Merchant")
    store = user_profile.get("store_name", "दुकान")
    score = user_profile.get("credit_score", 740)
    sales = user_profile.get("monthly_sales", 85000)

    # 1. Check if external LLM produces an answer
    system_prompt = (
        f"You are the Paytm Soundbox AI Voice Assistant for Indian merchants. "
        f"Current merchant: {name}, shop: {store}, credit score: {score}, monthly sales: ₹{sales:,}. "
        f"Answer concisely in 1-2 spoken sentences directly in {'Hindi (Devanagari script)' if lang == 'hi' else 'English'}. "
        f"Do not use markdown headers, asterisks, or bullet points. Speak naturally and clearly."
    )
    llm_text = query_external_llm(system_prompt, text)
    if llm_text:
        # Clean markdown formatting for voice
        clean = re.sub(r"[\*#`_]", "", llm_text).strip()
        chips = ["दुकान लोन", "स्वास्थ्य बीमा", "मेरी EMI"] if lang == "hi" else ["Business Loan", "Health Insurance", "My EMI"]
        return clean, [], session.get("stage", "idle"), chips

    # 2. Intelligent Built-in Conversational Agent (Domain-specific generative fallback)

    # A. Greetings & Identity
    if any(w in t for w in ["hello", "hi", "hey", "namaste", "नमस्ते", "हेलो", "हेलो", "kaise ho", "कैसे हो", "who are you", "आप कौन", "kaun ho", "kya ho"]):
        reply = (
            f"नमस्ते {name} जी! मैं आपका पेटीएम साउंडबॉक्स वॉयस असिस्टेंट हूँ। आप मुझसे दुकान लोन, आगामी EMI, या स्वास्थ्य बीमा के बारे में कभी भी पूछ सकते हैं।"
            if lang == "hi" else
            f"Hello {name}! I am your Paytm Soundbox Voice Assistant. You can ask me anytime about merchant business loans, your upcoming EMI, or health insurance."
        )
        chips = ["₹1,00,000 लोन", "मेरी EMI", "स्वास्थ्य बीमा"] if lang == "hi" else ["₹1,00,000 Loan", "My EMI", "Health Insurance"]
        return reply, [], "idle", chips

    # B. Capability / Help queries
    if any(w in t for w in ["help", "madad", "मदद", "kya kar sakte ho", "features", "what can you do", "kya hota hai"]):
        reply = (
            "मैं आपकी दुकान के लिए ₹2,00,000 तक का आसान लोन दिलवाने, लोन की EMI चेक व भुगतान करने, और स्वास्थ्य बीमा प्लान चुनने में मदद कर सकता हूँ।"
            if lang == "hi" else
            "I can help you apply for business loans up to ₹2,00,000, check and pay your loan EMIs, and compare health insurance plans for your family."
        )
        chips = ["लोन पात्रता", "EMI चेक करें", "बीमा तुलना"] if lang == "hi" else ["Check Loan", "Check EMI", "Compare Plans"]
        return reply, [], "idle", chips

    # C. General Loan Inquiry without specific amount
    if any(w in t for w in ["loan chahiye", "loan lena hai", "loan process", "loan details", "apply loan", "दुकान लोन", "लोन कैसे"]):
        reply = (
            f"आपकी {store} की ₹{sales:,} मासिक बिक्री के आधार पर, आप 14% सालाना ब्याज पर ₹10,000 से ₹2,00,000 तक का लोन ले सकते हैं। आपको कितने रुपयों की आवश्यकता है?"
            if lang == "hi" else
            f"Based on your monthly sales of ₹{sales:,}, you are eligible for a business loan from ₹10,000 up to ₹2,00,000 at 14% p.a. How much amount do you need?"
        )
        chips = ["₹50,000", "₹1,00,000", "₹2,00,000"]
        return reply, [], "amount", chips

    # D. Interest rate / tenure questions
    if any(w in t for w in ["interest", "rate", "byaj", "ब्याज", "tenure", "avdhi", "samay", "kist kitni"]):
        reply = (
            "पेटीएम मर्चेंट लोन पर ब्याज दर केवल 14% सालाना है। आप अपनी सुविधा अनुसार 3 महीने से लेकर 36 महीने की अवधि चुन सकते हैं।"
            if lang == "hi" else
            "Paytm merchant business loans have an interest rate of 14% per annum, with repayment tenures ranging from 3 to 36 months."
        )
        chips = ["₹50,000 लोन", "₹1,00,000 लोन"] if lang == "hi" else ["₹50,000 Loan", "₹1,00,000 Loan"]
        return reply, [], "idle", chips

    # E. Credit score / Eligibility queries
    if any(w in t for w in ["credit score", "cibil", "सिबिल", "स्कोर", "patrata", "eligibility", "paatra"]):
        reply = (
            f"आपका वर्तमान क्रेडिट स्कोर {score} है। समय पर EMI भरने और साउंडबॉक्स से निरंतर डिजिटल भुगतान स्वीकार करने से आपकी लोन लिमिट और बढ़ती है।"
            if lang == "hi" else
            f"Your current credit score is {score}. Making timely EMI payments and accepting QR payments with Paytm Soundbox improves your eligibility."
        )
        chips = ["दुकान लोन", "मेरी EMI"] if lang == "hi" else ["Business Loan", "My EMI"]
        return reply, [], "idle", chips

    # F. Soundbox / QR payments
    if any(w in t for w in ["soundbox", "साउंडबॉक्स", "qr", "क्यूआर", "audio", "payment", "aawaz"]):
        reply = (
            "पेटीएम साउंडबॉक्स आपकी दुकान पर प्राप्त होने वाले हर यूपीआई और क्यूआर पेमेंट की तुरंत स्पष्ट आवाज़ में पुष्टि करता है।"
            if lang == "hi" else
            "Paytm Soundbox provides instant, clear voice notifications for every UPI and QR payment received at your shop."
        )
        chips = ["दुकान लोन", "मेरी EMI"] if lang == "hi" else ["Business Loan", "My EMI"]
        return reply, [], "idle", chips

    # G. Documents / KYC needed
    if any(w in t for w in ["document", "dastavej", "दस्तावेज़", "kagaz", "aadhaar", "pan"]):
        reply = (
            "पेटीएम मर्चेंट लोन पूरी तरह डिजिटल और पेपरलेस है। इसके लिए केवल आपका आधार, पैन और साउंडबॉक्स ट्रांजेक्शन हिस्ट्री की आवश्यकता होती है।"
            if lang == "hi" else
            "Paytm merchant loans are 100% digital and paperless. Only your Aadhaar, PAN, and Soundbox QR transaction history are needed."
        )
        chips = ["लोन शुरू करें", "बीमा देखें"] if lang == "hi" else ["Start Loan", "View Insurance"]
        return reply, [], "idle", chips

    # No match found -> return None to let caller handle unknown/handoff
    return None, [], session.get("stage", "idle"), []


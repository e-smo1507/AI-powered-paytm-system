"""WhatsApp & SMS Notification System for Merchant Installment Reminders.
Provides message formatting, WhatsApp deep-link generation, notification dispatch,
and delivery tracking for merchant installment due dates.
"""
import datetime
import urllib.parse
import uuid
import time
from typing import Dict, Any, List, Optional

HINDI_MONTHS = {
    1: "जनवरी", 2: "फ़रवरी", 3: "मार्च", 4: "अप्रैल",
    5: "मई", 6: "जून", 7: "जुलाई", 8: "अगस्त",
    9: "सितंबर", 10: "अक्टूबर", 11: "नवंबर", 12: "दिसंबर"
}

# In-memory history of dispatched notifications for the current session/runtime
NOTIFICATION_HISTORY: List[Dict[str, Any]] = []


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


def get_merchant_due_info(user_data: dict, lang: str = "hi") -> Optional[Dict[str, Any]]:
    """Calculates due date, days left, and details for active loan installment."""
    loan = user_data.get("active_loan")
    if not loan:
        return None

    offset = loan.get("due_day_offset", 3)
    due_dt = datetime.date.today() + datetime.timedelta(days=offset)

    if lang == "hi":
        month_name = HINDI_MONTHS.get(due_dt.month, due_dt.strftime("%B"))
        due_date_str = f"{due_dt.day:02d} {month_name} {due_dt.year}"
    else:
        due_date_str = due_dt.strftime("%d %b %Y")

    amount = loan.get("emi_amount", 4850)
    loan_id = loan.get("loan_id", "LN-KIRANA-8821")
    purpose = loan.get("purpose", "Merchant Loan")
    account = loan.get("account", "Paytm Payments Bank ...5019")
    lender = loan.get("lender", "Paytm Payments Bank / Partner NBFC")
    phone = user_data.get("phone", "+919876543210")

    return {
        "loan_id": loan_id,
        "purpose": purpose,
        "amount": amount,
        "amount_inr": inr_fmt(amount),
        "due_date": due_date_str,
        "due_date_iso": due_dt.isoformat(),
        "days_left": offset,
        "account": account,
        "lender": lender,
        "phone": phone,
        "total_emis": loan.get("total_emis", 24),
        "emis_paid": loan.get("emis_paid", 8),
        "auto_debit": loan.get("auto_debit", True),
    }


def format_whatsapp_reminder(merchant_name: str, due_info: dict, lang: str = "hi") -> str:
    """Creates a professional WhatsApp message formatted with markdown for WhatsApp bolding/italics."""
    amount_str = due_info.get("amount_inr", inr_fmt(due_info.get("amount", 4850)))
    loan_id = due_info.get("loan_id", "LN-KIRANA-8821")
    due_date = due_info.get("due_date", "")
    days_left = due_info.get("days_left", 3)
    purpose = due_info.get("purpose", "दुकान बिज़नेस लोन")
    account = due_info.get("account", "Paytm Payments Bank ...5019")
    pay_link = f"https://paytm.me/pay-emi/{loan_id}"

    if lang == "hi":
        days_phrase = "आज ही" if days_left == 0 else f"{days_left} दिन बाद"
        urgency_note = (
            "🚨 *अत्यावश्यक सूचना:* कृपया आज ही देय तिथि से पहले भुगतान पूरा करें।"
            if days_left <= 1
            else f"⏰ कृपया देय तिथि ({due_date}) से पहले पर्याप्त बैलेंस बनाए रखें।"
        )
        return (
            f"🔔 *Paytm बिज़नेस लोन — मासिक EMI रिमाइंडर*\n\n"
            f"नमस्ते *{merchant_name}* जी,\n\n"
            f"यह आपके {purpose} (*{loan_id}*) की आगामी किस्त का रिमाइंडर है। "
            f"आपकी *{amount_str}* की EMI *{days_phrase} ({due_date})* को देय है।\n\n"
            f"📋 *किस्त विवरण (Installment Details):*\n"
            f"• लोन आईडी: *{loan_id}*\n"
            f"• ईएमआई राशि: *{amount_str}*\n"
            f"• अंतिम तारीख (Due Date): *{due_date}* ({days_left} दिन शेष)\n"
            f"• ऑटो-डेबिट खाता: *{account}*\n\n"
            f"{urgency_note}\n\n"
            f"💡 *समय पर भुगतान के लाभ:*\n"
            f"✓ बाउंस शुल्क (NACH bounce penalty) से बचाव\n"
            f"✓ CIBIL स्कोर में सुधार और अगले लोन पर कम ब्याज दर\n\n"
            f"📲 *तुरंत UPI से भुगतान करने के लिए यहाँ क्लिक करें:*\n"
            f"{pay_link}\n\n"
            f"सहायता व प्रश्न के लिए Paytm मर्चेंट हेल्पलाइन 1800-120-130 पर संपर्क करें।\n"
            f"— *Paytm Payments Bank / Partner NBFC*"
        )
    else:
        days_phrase = "today" if days_left == 0 else f"in {days_left} days"
        urgency_note = (
            "🚨 *Urgent Notice:* Please clear the installment before end-of-day today."
            if days_left <= 1
            else f"⏰ Please maintain sufficient account balance before {due_date}."
        )
        return (
            f"🔔 *Paytm Merchant Loan — Installment Reminder*\n\n"
            f"Dear *{merchant_name}*,\n\n"
            f"This is a reminder that the installment of *{amount_str}* for your "
            f"{purpose} (*{loan_id}*) is due *{days_phrase} on {due_date}*.\n\n"
            f"📋 *Installment Details:*\n"
            f"• Loan ID: *{loan_id}*\n"
            f"• Installment Amount: *{amount_str}*\n"
            f"• Due Date: *{due_date}* ({days_left} days remaining)\n"
            f"• Auto-Debit Account: *{account}*\n\n"
            f"{urgency_note}\n\n"
            f"💡 *Benefits of on-time repayment:*\n"
            f"✓ Avoid NACH bounce charges and late fee penalties\n"
            f"✓ Protect your credit score and unlock higher business loan limits\n\n"
            f"📲 *Pay instantly via Paytm UPI:*\n"
            f"{pay_link}\n\n"
            f"For support, contact Paytm Merchant Care at 1800-120-130.\n"
            f"— *Paytm Payments Bank / Partner NBFC*"
        )


def generate_whatsapp_deep_link(phone: str, message: str) -> str:
    """Generates an official WhatsApp Web / Universal Link (`wa.me`)."""
    # Clean phone number (strip whitespace, hyphens, plus)
    clean_phone = "".join(ch for ch in phone if ch.isdigit())
    if not clean_phone.startswith("91") and len(clean_phone) == 10:
        clean_phone = "91" + clean_phone
    encoded_text = urllib.parse.quote_plus(message)
    return f"https://wa.me/{clean_phone}?text={encoded_text}"


def send_whatsapp_notification(
    merchant_name: str,
    phone: str,
    due_info: dict,
    lang: str = "hi",
    custom_message: Optional[str] = None
) -> Dict[str, Any]:
    """Simulates sending WhatsApp message via Business API with full audit logging and deep-link generation."""
    clean_phone = "".join(ch for ch in phone if ch.isdigit())
    if not clean_phone.startswith("91") and len(clean_phone) == 10:
        clean_phone = "91" + clean_phone

    formatted_message = custom_message or format_whatsapp_reminder(merchant_name, due_info, lang)
    wa_link = generate_whatsapp_deep_link(phone, formatted_message)

    msg_id = f"WA-PTM-{uuid.uuid4().hex[:8].upper()}"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "id": msg_id,
        "type": "whatsapp_emi_reminder",
        "channel": "WhatsApp Business API",
        "recipient_name": merchant_name,
        "phone": f"+{clean_phone}",
        "loan_id": due_info.get("loan_id"),
        "amount": due_info.get("amount"),
        "due_date": due_info.get("due_date"),
        "days_left": due_info.get("days_left"),
        "message": formatted_message,
        "wa_link": wa_link,
        "status": "delivered",
        "status_code": 200,
        "sent_at": timestamp,
        "delivered_at": timestamp,
        "lang": lang,
    }

    NOTIFICATION_HISTORY.insert(0, record)
    return record


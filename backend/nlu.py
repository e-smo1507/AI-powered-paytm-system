"""Intent, amount and tenure parsing for Hindi + English (incl. Devanagari digits)."""
import re

DEV = str.maketrans("०१२३४५६७८९", "0123456789")
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

WORDS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "panch": 5, "paanch": 5, "chhe": 6, "che": 6,
    "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "barah": 12, "pandrah": 15,
    "bees": 20, "tees": 30, "chalis": 40, "pachas": 50,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छे": 6,
    "सात": 7, "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12, "पंद्रह": 15,
    "बीस": 20, "तीस": 30, "चालीस": 40, "पचास": 50,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "twelve": 12, "fifteen": 15, "twenty": 20,
    "thirty": 30, "thirty-six": 36, "thirtysix": 36,
}


def norm(t: str) -> str:
    return (t or "").translate(DEVANAGARI_DIGITS).lower().replace("-", " ")


def tokens(t: str) -> list[str]:
    return re.findall(r"[\w\u0900-\u097F]+", norm(t))


def has_phrase(t: str, phrases: list[str]) -> bool:
    n = " " + re.sub(r"\s+", " ", norm(t)) + " "
    toks = set(tokens(t))
    for raw in phrases:
        p = norm(raw).strip()
        if not p:
            continue
        if " " in p:
            if f" {p} " in n:
                return True
        elif len(p) <= 3:
            if p in toks:
                return True
        else:
            if p in toks or p in n:
                return True
    return False


def parse_amount(t: str):
    n = norm(t).replace(",", "")
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(lakh|lac|laakh|लाख|hazaar|hazar|हज़ार|हजार|k|thousand|हजार)?",
        n,
    )
    if m:
        val, unit = float(m.group(1)), m.group(2)
        if unit in ("lakh", "lac", "laakh", "लाख"):
            val *= 100_000
        elif unit in ("hazaar", "hazar", "हज़ार", "हजार", "k", "thousand"):
            val *= 1_000
        return int(val) if val >= 1_000 else None
    m = re.search(
        r"(ek|do|teen|char|panch|paanch|chhe|che|saat|aath|nau|das|one|two|three|four|five|"
        r"एक|दो|तीन|चार|पांच|पाँच|छह|सात|आठ|नौ|दस)\s*(lakh|lac|laakh|लाख)",
        n,
    )
    if m:
        return int(WORDS[m.group(1)] * 100_000)
    return None


def parse_tenure(t: str):
    n = norm(t)
    m = re.search(
        r"(\d+|ek|do|teen|char|panch|paanch|chhe|che|saat|aath|nau|das|gyarah|barah|pandrah|"
        r"bees|tees|chalis|pachas|one|two|three|four|five|six|twelve|fifteen|twenty|thirty|"
        r"एक|दो|तीन|चार|पांच|पाँच|छह|सात|आठ|नौ|दस|ग्यारह|बारह|पंद्रह|बीस|तीस)"
        r"\s*(mahine|mahina|month|months|महीने|महीना|saal|year|years|साल)",
        n,
    )
    if not m:
        m = re.search(r"(\d+)\s*(m|mo)\b", n)
        if not m:
            return None
        return int(m.group(1))
    raw, unit = m.group(1), m.group(2)
    num = int(raw) if raw.isdigit() else WORDS.get(raw)
    if not num:
        return None
    return num * 12 if unit in ("saal", "year", "years", "साल") else num


YES = [
    "haan", "han", "ha", "yes", "ok", "okay", "theek", "sure", "agree", "agreed",
    "हाँ", "हां", "जी", "ठीक", "सहमत", "confirm", "kar do", "कर दो", "aage badho",
    "आगे बढ़ो", "aage badhao", "go ahead", "i agree",
]
NO = ["nahi", "nahin", "no", "नहीं", "nahin", "mat", "decline", "refuse"]
HUMAN = ["human", "agent", "insaan", "इंसान", "executive", "बात करनी", "बात करो", "talk to", "person", "एजेंट", "agent se"]
LOAN = ["loan", "लोन", "udhaar", "कर्ज", "karz", "business loan", "working capital"]
NEED = ["chahiye", "चाहिए", "need", "want", "lena", "लेना", "apply", "आवेदन"]
INS = [
    "insurance", "bima", "बीमा", "policy", "पॉलिसी", "health", "cover", "कवर",
    "waiting", "इंतज़ार", "intezaar", "exclusion", "claim", "क्लेम", "room",
    "copay", "premium", "प्रीमियम", "plan", "प्लान",
]
FEES = ["fee", "fees", "interest", "charge", "byaj", "ब्याज", "शुल्क", "samjha", "समझ", "explain", "kitna", "total", "kfs"]
CMP = ["compare", "तुलना", "comparison", "konsa", "कौन सा", "vs", "difference", "dono", "दोनों"]
BUY = ["buy", "kharid", "खरीद", "purchase", "lena hai", "लेना है", "le lo", "ले लो", "subscribe"]
PLUS = ["plus"]
BASIC = ["basic", "बेसिक"]
DUKAAN = ["dukaan", "दुकान", "kirana", "merchant", "dukan"]

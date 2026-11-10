"""
rules.py - Core decision engine for ShieldPay.
Single source of truth for points, confidence rules, outcome grid, and wait times (§3, §6).
"""

from typing import List, Dict, Any, Optional, Tuple
import unicodedata

DEFAULT_WAIT_SECONDS = 30
RULE_VERSION = "1.0.0"

SCAM_QUESTIONS = [
    {
        "id": 1,
        "question": "Is someone on a call or chat with you right now telling you to make this payment?",
        "explanation": "Scammers use live pressure so you do not stop to think. Hang up and contact the company yourself."
    },
    {
        "id": 2,
        "question": "Has anyone claiming to be the police, a bank, PayPal or customs mentioned a fine, an account problem or an arrest?",
        "explanation": "Real officials do not demand payment through a shop checkout. This is a common fake-authority script."
    },
    {
        "id": 3,
        "question": "Were you promised a refund, prize, job, loan or investment return if you pay?",
        "explanation": "Being asked to pay first to receive something is a classic advance-fee scam."
    }
]

ALLOWED_CATEGORIES = {
    "urgency": "The message creates artificial urgency to rush payment.",
    "threat": "The message threatens legal, financial, or personal consequences.",
    "fake_support": "The sender impersonates support staff or security personnel.",
    "credential_request": "The message asks for passwords, PINs, or one-time codes.",
    "advance_fee": "The message promises future payouts in exchange for an upfront payment.",
    "pay_outside_checkout": "The seller asks to take payment off-platform or via unverified methods.",
    "odd_refund": "The message claims an accidental overpayment or refund requiring payback."
}

KNOWN_BRANDS = {
    "paypal": "paypal.com",
    "amazon": "amazon.com",
    "apple": "apple.com",
    "microsoft": "microsoft.com",
    "google": "google.com",
    "netflix": "netflix.com",
    "ebay": "ebay.com",
    "dhl": "dhl.com",
    "fedex": "fedex.com"
}

HOMOGLYPH_MAP = {
    "0": "o", "1": "l", "3": "e", "5": "s", "8": "b", "@": "a",
    "а": "a", "с": "c", "е": "e", "о": "o", "р": "p", "х": "x", "у": "y"
}


def normalize_seller_id(email: str) -> str:
    """ID Normalisation (§6, B5)."""
    if not email:
        return ""
    clean = email.strip().lower()
    if "@" not in clean:
        return clean
    user, domain = clean.split("@", 1)
    if domain in ("gmail.com", "googlemail.com"):
        user = user.split("+")[0]
        user = user.replace(".", "")
    return f"{user}@{domain}"


def validate_script_consistency(text: str) -> bool:
    """Reject report IDs that mix alphabets (§6, B5)."""
    scripts = set()
    for char in text:
        if char.isalpha():
            scripts.add(unicodedata.name(char, "").split()[0])
    if "LATIN" in scripts and "CYRILLIC" in scripts:
        return False
    return True


def check_brand_lookalike(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Brand lookalike check (§6, B5)."""
    if not email or "@" not in email:
        return False, None, None

    norm = email.strip().lower()
    user_part, domain_part = norm.split("@", 1)

    homo_user = "".join(HOMOGLYPH_MAP.get(c, c) for c in user_part)
    homo_domain = "".join(HOMOGLYPH_MAP.get(c, c) for c in domain_part)

    for brand, real_domain in KNOWN_BRANDS.items():
        if domain_part == real_domain:
            continue
        if brand in homo_user or brand in homo_domain:
            msg = (
                "This seller's email contains a well-known brand name but is not from that "
                "company's website. Check you are paying the real company."
            )
            return True, brand, msg

    return False, None, None


def calculate_score(
    confirmed_reports: int = 0,
    scam_question_yes: bool = False,
    unverified_reports: int = 0,
    is_brand_lookalike: bool = False,
    scam_wording_categories: Optional[List[str]] = None
) -> Tuple[int, Dict[str, int]]:
    """Calculate score with soft signals strictly capped at 49 (§3, L1)."""
    breakdown: Dict[str, int] = {}
    hard_points = 0

    if confirmed_reports > 0:
        pts = min(60, confirmed_reports * 60)
        breakdown["confirmed_report"] = pts
        hard_points += pts

    if scam_question_yes:
        breakdown["scam_question_yes"] = 50
        hard_points += 50

    unverified_pts = min(40, unverified_reports * 20)
    lookalike_pts = 40 if is_brand_lookalike else 0
    wording_count = len(set(scam_wording_categories or []))
    wording_pts = min(30, wording_count * 10)

    raw_soft = unverified_pts + lookalike_pts + wording_pts
    capped_soft = min(49, raw_soft)
    breakdown["soft_capped"] = capped_soft

    total_score = hard_points + capped_soft
    breakdown["total_score"] = total_score
    return total_score, breakdown


def determine_confidence(
    order_checked: bool,
    message_checked: bool,
    questions_answered: bool,
    brand_or_report_hit: bool,
    confirmed_report_found: bool
) -> str:
    """Confidence rule (§3, L2)."""
    if confirmed_report_found or (message_checked and questions_answered):
        return "High"
    if message_checked or questions_answered or brand_or_report_hit:
        return "Medium"
    return "Low"


def determine_outcome(score: int, confidence: str) -> Tuple[str, str]:
    """Outcome grid (§3, L2, L3)."""
    if score < 20:
        if confidence == "Low":
            return "Unknown", "Warn, ask to confirm"
        return "Low risk", "Allow"
    elif score <= 49:
        if confidence == "Low":
            return "Unknown", "Warn, ask to confirm"
        return "Suspicious", "Warn, 30-second wait, confirm"
    else:
        return "High risk", "Stop capture"

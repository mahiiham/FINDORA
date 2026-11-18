"""Small, dependency-light AI/ML helpers used across Findora.

These are intentionally built on the stack already declared in requirements.txt
(scikit-learn, PIL, stdlib) so the whole app keeps running with zero external
API calls and zero extra network dependencies — important for a
privacy-sensitive, offline-capable lost & found platform.
"""
import re
from difflib import SequenceMatcher
from app.utils.textsim import text_cosine

# --- Claim verification confidence -----------------------------------------

def verification_confidence(claim_response: str, private_details: str) -> dict:
    """Compares what a claimant typed against the report owner's private
    verification details and returns an explainable confidence score for the
    admin reviewer. This NEVER auto-approves a claim — a human always decides —
    it only summarizes evidence so review is faster and more consistent."""
    a = (claim_response or '').strip()
    b = (private_details or '').strip()
    if not a or not b:
        return {'score': 0.0, 'label': 'Insufficient data', 'level': 'low'}
    ratio = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    cosine = text_cosine(a, b, (1, 1))
    score = round((0.5 * ratio + 0.5 * cosine) * 100, 1)
    if score >= 65:
        level, label = 'high', 'Strong overlap with protected details'
    elif score >= 35:
        level, label = 'medium', 'Partial overlap — review carefully'
    else:
        level, label = 'low', 'Little overlap — high fraud risk'
    return {'score': score, 'label': label, 'level': level}


# --- Personal-information redaction for the anonymized chat -----------------

_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(r'(\+?\d[\d\-\s()]{7,}\d)')
_SOCIAL_RE = re.compile(r'\b(instagram|insta|whatsapp|wa\.me|snapchat|telegram|t\.me)\b\s*[:@]?\s*[\w.]*', re.I)


def redact_personal_info(text: str):
    """Findora's chat is designed for anonymized coordination between a
    claimant and a report owner — no phone numbers, emails, or social handles
    are meant to change hands until the platform's own verification/return flow
    completes. This is a defense-in-depth filter, not the only safeguard."""
    if not text:
        return text, False
    redacted = False
    def _mask(pattern, s):
        nonlocal redacted
        def repl(m):
            nonlocal redacted
            redacted = True
            return '[hidden by Findora — contact details are not allowed in chat]'
        return pattern.sub(repl, s)
    out = _mask(_EMAIL_RE, text)
    out = _mask(_PHONE_RE, out)
    out = _mask(_SOCIAL_RE, out)
    return out, redacted


# --- Duplicate-report detector -----------------------------------------

def text_similarity_ratio(a: str, b: str) -> float:
    """Plain sequence similarity (0..1) between two short texts — used to warn
    a user their new report looks like one they already filed recently, so
    they don't accidentally create two open reports for the same item."""
    return SequenceMatcher(None, (a or '').strip().lower(), (b or '').strip().lower()).ratio()


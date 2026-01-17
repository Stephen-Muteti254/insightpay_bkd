import re
from presidio_analyzer import AnalyzerEngine
from app.services.chat_service import normalize_text

analyzer = AnalyzerEngine()

WINDOW = 25

def analyze_chat_behavior(messages):
    """
    messages = list of message objects (sorted by ascending time)
    Returns: { "risk": low|medium|high, "detected": [list of PII] }
    """

    # 1. Combine all message content
    raw_text = " ".join([m.content or "" for m in messages])

    # 2. Normalize obfuscation
    norm = normalize_text(raw_text)

    print(f"chat content = {norm}")

    # 3. Presidio hits
    presidio_hits = analyzer.analyze(text=norm, language="en")

    # 4. Regex fallback hits
    regex_hits = []
    PII_PATTERNS = [
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}",
        r"\+?\d{9,15}",
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{3,4}\b",
        r"[A-Za-z0-9._%+-]+@[A-Za-z]+"  # very loose username@domain
    ]

    for p in PII_PATTERNS:
        if re.search(p, norm, re.IGNORECASE):
            regex_hits.append(p)

    # 5. Detect previously redacted PII
    # redacted_count = norm.count("REDACTED")
    redacted_count = len(re.findall(r"\[REDACTED\]", norm))

    # 6. Calculate risk score
    total_hits = len(presidio_hits) + len(regex_hits) + redacted_count

    if total_hits >= 2:
        risk = "high"
    elif total_hits >= 1:
        risk = "medium"
    else:
        risk = "low"

    return {
        "risk": "low",
        "presidio_hits": presidio_hits,
        "regex_hits": regex_hits,
        "redacted_count": redacted_count,
        "normalized_text": norm,
    }

from transformers import pipeline
sentiment_analyzer = pipeline("sentiment-analysis")
URGENT_KEYWORDS = [
    "urgent", "immediately", "critical", "asap", "cannot access",
    "not working", "down", "issue", "problem", "failure", "important"
]

def analyze_sentiment(text: str) -> str:
    """Return sentiment of the text (Positive / Negative / Neutral)."""
    if not text.strip():
        return "Neutral"
    result = sentiment_analyzer(text[:512])[0]  # limit length for performance
    label = result["label"]
    if label == "POSITIVE":
        return "Positive"
    elif label == "NEGATIVE":
        return "Negative"
    return "Neutral"

def detect_urgency(text: str) -> str:
    """Return priority level (Urgent / Not urgent)."""
    text_lower = text.lower()
    for kw in URGENT_KEYWORDS:
        if kw in text_lower:
            return "Urgent"
    return "Not urgent"

def classify_type(subject: str, body: str) -> str:
    """Classify email type: support, help, request, query, spam."""
    text = (subject + " " + body).lower()

    if any(word in text for word in ["support", "issue", "problem", "ticket"]):
        return "support"
    elif any(word in text for word in ["help", "assist", "guidance"]):
        return "help"
    elif any(word in text for word in ["request", "apply", "need access", "require"]):
        return "request"
    elif any(word in text for word in ["how", "what", "when", "where", "query", "question"]):
        return "query"
    elif any(word in text for word in ["win money", "lottery", "click here", "offer", "buy now", "free"]):
        return "spam"
    else:
        return "query"  # fallback

def classify_email(email: dict) -> dict:
    """
    Classify email with type, sentiment and urgency.
    Input: email dict with keys (subject, body, sender, date)
    Output: updated dict with type, sentiment & priority
    """
    subject = email.get("subject", "")
    body = email.get("body", "")
    content = f"{subject} {body}"

    email["type"] = classify_type(subject, body)

    if email["type"] in ["support", "help", "request"]:
        email["sentiment"] = analyze_sentiment(content)
        email["priority"] = detect_urgency(content)
    else:
        email["sentiment"] = "Neutral"
        email["priority"] = "Not urgent"

    return email

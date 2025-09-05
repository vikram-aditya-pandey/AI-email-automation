from typing import Dict

def categorize_email(email: Dict) -> Dict:
    """
    Categorizes an email into a simple type (complaint, request, query, other)
    and urgency level (high, medium, low) based on subject/snippet content.

    Args:
        email (dict): Email dictionary with keys 'subject', 'from', 'snippet'.

    Returns:
        dict: A dictionary with 'category' and 'urgency' keys.
    """
    text = (email.get("subject", "") or "") + " " + (email.get("snippet", "") or "")
    text = text.lower()

    # --- simple keyword rules for category ---
    if any(word in text for word in ["error", "issue", "problem", "not working", "fail"]):
        category = "complaint"
    elif any(word in text for word in ["request", "feature", "need", "access"]):
        category = "request"
    elif any(word in text for word in ["how", "can i", "help", "clarify", "question"]):
        category = "query"
    else:
        category = "other"

    # --- urgency estimation ---
    if any(word in text for word in ["urgent", "immediately", "asap", "critical", "cannot login", "failed"]):
        urgency = "high"
    elif any(word in text for word in ["soon", "priority", "important"]):
        urgency = "medium"
    else:
        urgency = "low"

    return {
        "category": category,
        "urgency": urgency
    }

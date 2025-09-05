def filter_support_emails(emails):
    """Filter emails with support-related keywords in subject."""
    keywords = ["Support", "Query", "Request", "Help"]
    filtered = []
    for email in emails:
        if any(k.lower() in email["subject"].lower() for k in keywords):
            filtered.append(email)
    return filtered

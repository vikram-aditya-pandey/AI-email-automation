import re
from typing import Dict, Any
from transformers import pipeline
import spacy
import logging

# Logging setup
logging.basicConfig(
    filename="email_extraction.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_email_processing(email: dict, extracted: dict):
    logging.info(f"Email Subject: {email.get('subject')}")
    logging.info(f"Extracted Info: {extracted}")

# Load models
try:
    summarizer = pipeline("text2text-generation", model="google/flan-t5-base")
except Exception as e:
    summarizer = None

try:
    sentiment_model = pipeline("sentiment-analysis")
except Exception as e:
    sentiment_model = None

nlp = spacy.load("en_core_web_sm")

def ner_fallback(text: str) -> dict:
    doc = nlp(text)
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    return {"names": names, "dates": dates, "orgs": orgs}

def generate_summary(email_text: str) -> str:
    if not email_text.strip() or not summarizer:
        return "[Summarizer not available]"
    try:
        prompt = (
            "Summarize this email in 2-3 sentences. "
            "Focus on main issue, requests, important details:\n\n"
            f"{email_text}"
        )
        result = summarizer(prompt, max_new_tokens=150, do_sample=False)
        return result[0]["generated_text"].strip()
    except Exception as e:
        return f"[Error generating summary: {e}]"

def analyze_sentiment(email_text: str) -> str:
    if not sentiment_model:
        return "Neutral"
    try:
        result = sentiment_model(email_text[:512])
        label = result[0]["label"].lower()
        if "neg" in label:
            return "Negative"
        elif "pos" in label:
            return "Positive"
        else:
            return "Neutral"
    except:
        return "Neutral"

def detect_priority(email_text: str) -> str:
    urgent_keywords = ["urgent", "immediately", "asap", "critical", "cannot", "help", "fail", "problem"]
    text_lower = email_text.lower()
    for kw in urgent_keywords:
        if kw in text_lower:
            return "Urgent"
    return "Normal"

def generate_draft_response(email: Dict[str, Any], summary: str, sentiment: str, priority: str) -> str:
    if not summarizer:
        return "[Draft response unavailable]"
    try:
        sender = email.get("name") or "Customer"
        body = email.get("snippet", "")
        prompt = (
            f"Compose a professional, friendly email response.\n"
            f"Sender Name: {sender}\n"
            f"Email Content: {body}\n"
            f"Summary: {summary}\n"
            f"Sentiment: {sentiment}\n"
            f"Priority: {priority}\n\n"
            f"Respond in 2-3 sentences, acknowledge issue, provide guidance."
        )
        result = summarizer(prompt, max_new_tokens=200, do_sample=False)
        return result[0]["generated_text"].strip()
    except:
        return "[Error generating draft response]"

def extract_info(email: Dict[str, Any]) -> Dict[str, Any]:
    text = f"{email.get('subject','')}\n{email.get('snippet','')}"

    # Regex patterns
    name_pattern = r"(?:Hi|Hello|Dear)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)"
    order_pattern = r"(?:order|Order|ORDER)\s*ID[:\s\-]*([A-Za-z0-9\-]+)"
    phone_pattern = r"\+?\d{2,4}[-.\s]?\d{6,12}|\b\d{10}\b"
    email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    date_pattern = (
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{1,2},?\s?\d{4})"
    )

    name_match = re.search(name_pattern, text)
    order_match = re.search(order_pattern, text, re.IGNORECASE)
    phone_match = re.search(phone_pattern, text)
    email_match = re.search(email_pattern, text)
    date_match = re.search(date_pattern, text)

    # Fallback NER
    ner_results = ner_fallback(text)
    if not name_match and ner_results["names"]:
        name_match = ner_results["names"][0]
    if not date_match and ner_results["dates"]:
        date_match = ner_results["dates"][0]

    summary = generate_summary(text[:1000])
    sentiment = analyze_sentiment(text)
    priority = detect_priority(text)
    draft_response = generate_draft_response(email, summary, sentiment, priority)

    extracted = {
        "name": name_match.group(1) if hasattr(name_match, "group") else name_match,
        "order_id": order_match.group(1) if order_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "email": email_match.group(0) if email_match else None,
        "date": date_match.group(0) if hasattr(date_match, "group") else date_match,
        "summary": summary,
        "sentiment": sentiment,
        "priority": priority,
        "draft_response": draft_response
    }

    log_email_processing(email, extracted)
    return extracted

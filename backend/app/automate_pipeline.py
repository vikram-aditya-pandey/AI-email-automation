import imaplib
import email
from email.header import decode_header
import re
import json
import os
from typing import List, Dict
from email.utils import parsedate_to_datetime

from app.sentiment_priority import classify_email, sort_emails_by_priority, analyze_sentiment, assign_priority
from app.extraction.info_extract import extract_info  # uses your existing extractor
from app import db

# load credentials.json (app/credentials.json)
CREDS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
with open(CREDS_PATH, "r", encoding="utf-8") as f:
    creds = json.load(f)
EMAIL_USER = creds["email_user"]
EMAIL_PASS = creds["email_pass"]
IMAP_HOST = creds.get("imap_host", "imap.gmail.com")
IMAP_PORT = creds.get("imap_port", 993)

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

def fetch_emails(n: int = 50) -> List[Dict]:
    """
    Fetch last n messages via IMAP and return list of dicts with:
    id (Message-ID), subject, sender, body, date
    """
    mails = []
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(EMAIL_USER, EMAIL_PASS)
    imap.select("INBOX")

    status, data = imap.search(None, "ALL")
    if status != "OK":
        imap.logout()
        return mails

    ids = data[0].split()
    latest = ids[-n:] if len(ids) >= n else ids

    for mid in reversed(latest):
        status, msg_data = imap.fetch(mid, "(RFC822)")
        if status != "OK":
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        # Message-ID (unique)
        msg_id = msg.get("Message-ID") or msg.get("Message-Id") or f"<local-{mid.decode()}>"

        # Subject
        subject_raw = msg.get("Subject", "") or ""
        subject, enc = decode_header(subject_raw)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(enc or "utf-8", errors="ignore")
        subject = clean_text(subject)

        # From
        sender = msg.get("From", "")

        # Date
        date_raw = msg.get("Date", "") or ""
        date_str = date_raw

        # Body (prefer text/plain)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdisp = str(part.get("Content-Disposition") or "")
                if ctype == "text/plain" and "attachment" not in cdisp.lower():
                    try:
                        body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                        break
                    except Exception:
                        body = ""
            # if still empty, try html part fallback
            if not body:
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        try:
                            body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="ignore")
                            break
                        except Exception:
                            body = ""
        else:
            try:
                body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
            except Exception:
                body = ""

        mails.append({
            "id": msg_id.strip(),
            "subject": subject,
            "sender": sender,
            "date": date_str,
            "body": clean_text(body)
        })

    imap.logout()
    return mails


def run_pipeline(fetch_n: int = 100):
    """
    Main pipeline:
     - Ensure DB exists
     - Fetch latest N emails
     - For each email not already in DB:
         - classify type / sentiment / priority
         - extract structured info (phone, alt email, requirements) via extract_info
         - insert into DB
    """
    print("Initializing DB...")
    db.init_db()

    print(f"Fetching up to {fetch_n} emails...")
    emails = fetch_emails(fetch_n)
    print(f"Fetched {len(emails)} emails")

    inserted = 0
    for mail in emails:
        # skip duplicates by message-id
        if db.email_exists(mail["id"]):
            continue

        # classify (type, sentiment, priority)
        classified = classify_email(mail.copy())  # returns mail updated with type/sentiment/priority

        # ensure sentiment and priority exist (classify_email handles that)
        sentiment = classified.get("sentiment", "Neutral")
        priority = classified.get("priority", "Not Urgent")

        # info extraction (phone, alternate email, requirements or summary)
        try:
            info = extract_info({
                "subject": classified.get("subject"),
                "snippet": (classified.get("body") or "")[:200],
                "body": classified.get("body")
            })
            phone = info.get("phone") or None
            alt_email = info.get("alternate_email") or info.get("email") or None
            requirements = info.get("requirements") or info.get("summary") or None
        except Exception as e:
            phone = None
            alt_email = None
            requirements = None

        # Build record for DB
        record = {
            "id": classified["id"],
            "sender": classified.get("sender"),
            "subject": classified.get("subject"),
            "body": classified.get("body"),
            "date": classified.get("date"),
            "type": classified.get("type"),
            "sentiment": sentiment,
            "priority": priority,
            "phone": phone,
            "alt_email": alt_email,
            "requirements": requirements,
            "draft_response": None
        }

        try:
            inserted_flag = db.insert_email(record)
            if inserted_flag:
                inserted += 1
        except Exception as e:
            print(f"Error inserting email {record.get('id')}: {e}")

    print(f"Inserted {inserted} new email(s) into DB.")

    # Optional: print top 10 urgent unprocessed messages
    queue = db.get_next_emails(10)
    if queue:
        print("\nTop items in priority queue (unprocessed):")
        for q in queue:
            print(f"- [{q['priority']}] {q['type']} | {q['subject']} | from {q['sender']} | id={q['id']}")
    else:
        print("No unprocessed items in queue.")

if __name__ == "__main__":
    run_pipeline()

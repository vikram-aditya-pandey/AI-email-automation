import imaplib
import email
import json
from email.header import decode_header
import re
import os

# Load config.json
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

EMAIL_ACCOUNT = config["email_user"]
APP_PASSWORD = config["email_pass"]
IMAP_SERVER = config["imap_host"]
IMAP_PORT = 993

def clean_text(text):
    # Remove newlines and excessive spaces
    return re.sub(r'\s+', ' ', text).strip()

def fetch_emails(n=10):
    """Fetch the last `n` emails from the inbox."""
    mails = []
    # Connect to server
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
    mail.select("inbox")

    # Search all emails
    status, messages = mail.search(None, "ALL")
    mail_ids = messages[0].split()
    latest_ids = mail_ids[-n:]  # last n emails

    for i in reversed(latest_ids):
        status, msg_data = mail.fetch(i, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                from_ = msg.get("From")
                date_ = msg.get("Date")

                # Get email body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        cdisp = str(part.get("Content-Disposition"))
                        if ctype == "text/plain" and "attachment" not in cdisp:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                mails.append({
                    "subject": clean_text(subject),
                    "sender": from_,
                    "date": date_,
                    "body": clean_text(body)
                })

    mail.logout()
    return mails

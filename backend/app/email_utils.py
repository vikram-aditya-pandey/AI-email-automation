import imaplib
import email
from email.header import decode_header

def fetch_emails(imap_host, email_user, email_pass, limit=5):
    """
    Connects to an IMAP server and fetches the latest emails.
    Returns a list of dictionaries with subject, sender, and snippet.
    """
    mails = []
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(imap_host)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Search all mails
        status, data = mail.search(None, "ALL")
        if status != "OK":
            return []

        # Get latest N mails
        mail_ids = data[0].split()[-limit:]
        for num in reversed(mail_ids):
            status, msg_data = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])

            # Decode subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8", errors="ignore")

            # Get sender
            from_ = msg.get("From")

            # Extract body snippet
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            mails.append({
                "subject": subject,
                "from": from_,
                "snippet": body[:200]  # first 200 chars
            })

        mail.logout()
    except Exception as e:
        return [{"error": str(e)}]

    return mails

import imapclient
import email
from email.header import decode_header

def decode_mime_words(s):
    """Decode MIME-encoded words in headers."""
    decoded = decode_header(s)
    return ''.join(
        str(t[0], t[1] or 'utf-8') if isinstance(t[0], bytes) else t[0]
        for t in decoded
    )

def fetch_emails(imap_host, email_user, email_pass):
    server = imapclient.IMAPClient(imap_host, ssl=True)  # Use SSL
    server.login(email_user, email_pass)
    server.select_folder("INBOX")

    messages = server.search(["NOT", "DELETED"])
    emails = []

    for uid in messages:
        raw_message = server.fetch([uid], ["BODY[]", "FLAGS"])
        msg = email.message_from_bytes(raw_message[uid][b"BODY[]"])

        subject = decode_mime_words(msg.get("subject", ""))
        sender = decode_mime_words(msg.get("from", ""))
        date = msg.get("date")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="ignore"
                    )
                    break
            else:  # if no text/plain, fallback to text/html
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="ignore"
                        )
                        break
        else:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="ignore"
            )

        emails.append({
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body,
        })

    server.logout()
    return emails

# app/db.py
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = "emails.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY,            -- Message-ID or generated unique id
    sender TEXT,
    subject TEXT,
    body TEXT,
    date TEXT,                      -- original date string
    received_at TEXT,               -- insertion timestamp (ISO)
    type TEXT,
    sentiment TEXT,
    priority TEXT,
    phone TEXT,
    alt_email TEXT,
    requirements TEXT,
    draft_response TEXT,
    processed INTEGER DEFAULT 0     -- 0 = not processed, 1 = processed
);

CREATE INDEX IF NOT EXISTS idx_priority_date ON emails (priority, date);
CREATE INDEX IF NOT EXISTS idx_processed ON emails (processed);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()

def email_exists(msg_id: str) -> bool:
    if not msg_id:
        return False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM emails WHERE id = ?", (msg_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def insert_email(record: Dict):
    """
    Insert a classified email record into DB if not exists.
    record expected fields:
      id, sender, subject, body, date, type, sentiment, priority,
      phone, alt_email, requirements, draft_response (optional)
    """
    if "id" not in record or not record["id"]:
        raise ValueError("record must include unique 'id' field")

    if email_exists(record["id"]):
        return False

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO emails (id, sender, subject, body, date, received_at, type, sentiment, priority,
                            phone, alt_email, requirements, draft_response, processed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record.get("id"),
            record.get("sender"),
            record.get("subject"),
            record.get("body"),
            record.get("date"),
            datetime.utcnow().isoformat(),
            record.get("type"),
            record.get("sentiment"),
            record.get("priority"),
            record.get("phone"),
            record.get("alt_email"),
            record.get("requirements"),
            record.get("draft_response"),
            0
        ),
    )
    conn.commit()
    conn.close()
    return True

def get_next_emails(limit: int = 20) -> List[Dict]:
    """
    Returns next emails ordered by priority (Urgent first) then newest date.
    Priority ordering: 'Urgent' first, everything else after.
    """
    conn = get_conn()
    cur = conn.cursor()
    # Use CASE to order Urgent first, then Not Urgent
    cur.execute(
        f"""
        SELECT id, sender, subject, body, date, received_at, type, sentiment, priority,
               phone, alt_email, requirements, draft_response, processed
        FROM emails
        WHERE processed = 0
        ORDER BY (CASE WHEN priority = 'Urgent' THEN 0 ELSE 1 END) ASC,
                 COALESCE(date, received_at) DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    cols = ["id","sender","subject","body","date","received_at","type","sentiment","priority","phone","alt_email","requirements","draft_response","processed"]
    results = [dict(zip(cols, r)) for r in rows]
    return results

def mark_processed(msg_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE emails SET processed = 1 WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()

def update_draft_response(msg_id: str, draft: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE emails SET draft_response = ? WHERE id = ?", (draft, msg_id))
    conn.commit()
    conn.close()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json
import os

from app.gmail_fetch import fetch_emails
from app.extraction.info_extract import extract_info

app = FastAPI(title="AI Email Assistant")

# --------- Request Model ---------
class FetchRequest(BaseModel):
    limit: int = 5  # optional, default fetch 5 emails

# --------- Load Credentials ---------
creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")
with open(creds_path) as f:
    creds = json.load(f)

# --------- Routes ---------
@app.post("/fetch")
async def fetch_emails_route(request: FetchRequest) -> Dict[str, Any]:
    try:
        emails = fetch_emails(
            creds["imap_host"],
            creds["email_user"],
            creds["email_pass"],
            limit=request.limit
        )
        if not emails:
            return {"results": [], "message": "No emails found."}

        results = []
        for email in emails:
            info = extract_info(email)
            results.append({**email, **info})

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

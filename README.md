# AI-Powered Email Communication Assistant

## What the Project Is
This project is an AI-powered assistant that helps organizations manage support-related emails automatically. Instead of manually going through hundreds of emails, the system retrieves incoming emails, analyzes them, categorizes them, and even generates draft responses using AI.  

The goal is to improve efficiency, response quality, and customer satisfaction while reducing manual effort.

---

## How It Works
1. **Email Retrieval**  
   The system connects to the user’s mailbox via IMAP and fetches incoming emails.  

2. **Filtering & Categorization**  
   Emails containing keywords like *Support*, *Query*, *Request*, and *Help* are filtered.  
   They are then categorized and labeled with sentiment (Positive, Negative, Neutral) and priority (Urgent, Not Urgent).  

3. **AI-Powered Responses**  
   For each email, the system uses a language model to generate a draft reply that is context-aware and professional.  

4. **Database Storage**  
   All extracted email data, analysis results, and generated responses are stored in an SQLite database for use in dashboards or further processing.  

---

## Steps to Run

1. **Clone the Repository**
   ```bash
   git clone <repo-link>
   cd backend
2. **Create a virtual environment and activate it**
    ```bash
    python -m venv venv
    venv\Scripts\activate
3. **Install dependcencies**
    ```bash
    pip install -r requirements.txt
4. **Add credentials**
    ```bash
    {
    "email": "your-email@gmail.com",
    "password": "your-app-password",
    "imap_server": "imap.gmail.com"
}
5. **Run the project**
    ````bash
    python -m app.automate_pipeline


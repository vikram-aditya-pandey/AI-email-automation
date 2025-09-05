from transformers import pipeline
generator = pipeline("text-generation", model="distilgpt2")


def generate_response(email: dict, knowledge_base: dict = None) -> str:
    """
    Generates a professional and empathetic response to a support email.

    Args:
        email (dict): Dictionary with 'subject', 'body', 'sentiment', 'priority'.
        knowledge_base (dict, optional): Extra context for responses (e.g. FAQs).

    Returns:
        str: Generated response text.
    """
    subject = email.get("subject", "")
    body = email.get("body", "")
    sentiment = email.get("sentiment", "")
    priority = email.get("priority", "")

    # Build the base prompt
    prompt = (
        "You are a professional customer support agent.\n"
        f"Email Subject: {subject}\n"
        f"Email Body: {body}\n"
        f"Customer Sentiment: {sentiment}\n"
        f"Priority: {priority}\n\n"
        "Write a polite, empathetic, and helpful response:\n"
    )

    # Add knowledge base info if provided
    if knowledge_base:
        prompt += f"\nHelpful context:\n{knowledge_base}\n"

    try:
        response = generator(
            prompt,
            max_length=200,
            num_return_sequences=1,
            pad_token_id=50256,  # avoids warnings with GPT2-based models
        )
        reply = response[0]["generated_text"].replace(prompt, "").strip()
    except Exception as e:
        reply = f"Error generating response: {str(e)}"

    return reply

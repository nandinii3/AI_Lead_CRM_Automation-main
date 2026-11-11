import os
import openai
from app.models import LeadInput, LeadAnalysis

SCORE_THRESHOLD = int(os.getenv("LEAD_SCORE_THRESHOLD", "70"))

SYSTEM_PROMPT = """You are a B2B lead qualification specialist.
Analyze incoming leads and return a structured assessment.

Scoring guide (score 0-100):
- 80-100: high-value, clear need, budget signals, large team
- 60-79: medium-value, some positive signals, worth follow-up
- 40-59: unclear intent or limited information
- 0-39: low-value, vague, or likely spam

For key_signals: list 2-5 concrete phrases extracted from the message that influenced your score.
For suggested_action: one specific next step (max 200 characters)."""


def analyze_lead(lead: LeadInput) -> LeadAnalysis:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    user_message = (
        f"Name: {lead.name}\n"
        f"Company: {lead.company}\n"
        f"Email: {lead.email}\n"
        f"Message: {lead.message}\n"
        f"Source: {lead.source}"
    )

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=LeadAnalysis,
    )

    analysis = response.choices[0].message.parsed

    # Aplikacja wymusza requires_human_followup na podstawie score - nie AI
    analysis.requires_human_followup = analysis.score >= SCORE_THRESHOLD

    return analysis

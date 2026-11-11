import logging
import os

import httpx

from app.models import LeadAnalysis, LeadInput
from app.services.lead_service import SCORE_THRESHOLD

logger = logging.getLogger(__name__)


def should_notify(analysis: LeadAnalysis) -> bool:
    return analysis.priority == "high" or analysis.score >= SCORE_THRESHOLD


def notify_lead_if_qualified(
    lead: LeadInput, analysis: LeadAnalysis, lead_id: str | None
) -> bool:
    if not should_notify(analysis):
        return False

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning(
            "SLACK_WEBHOOK_URL not set — skipping notification for lead %s", lead_id
        )
        return False

    payload = {
        "text": (
            ":rotating_light: *New high-value lead*\n"
            f"*Name:* {lead.name}\n"
            f"*Company:* {lead.company}\n"
            f"*Score:* {analysis.score}/100 (priority: {analysis.priority})\n"
            f"*Suggested action:* {analysis.suggested_action}"
        )
    }
    try:
        response = httpx.post(webhook_url, json=payload, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("Slack notification failed for lead %s: %s", lead_id, e)
        return False

    logger.info("Slack notification sent for lead %s", lead_id)
    return True

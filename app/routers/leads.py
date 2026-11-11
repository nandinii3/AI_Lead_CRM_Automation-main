import logging
import openai
from fastapi import APIRouter, HTTPException
from app.models import LeadInput, LeadResponse, StoredLead
from app.services.lead_service import analyze_lead
from app.services.slack_service import notify_lead_if_qualified
from app.services.supabase_service import save_lead, get_all_leads, get_lead_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("/analyze", response_model=LeadResponse)
def analyze(lead: LeadInput) -> LeadResponse:
    try:
        analysis = analyze_lead(lead)
    except openai.APIConnectionError:
        raise HTTPException(status_code=502, detail="Cannot reach OpenAI API")
    except openai.RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
    except openai.APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")

    lead_id: str | None = None
    try:
        lead_id = save_lead(lead, analysis)
    except Exception as e:
        logger.error("Supabase save failed: %s", e)

    notify_lead_if_qualified(lead, analysis, lead_id)

    return LeadResponse(id=lead_id, lead=lead, analysis=analysis)


@router.get("/", response_model=list[StoredLead])
def list_leads() -> list[StoredLead]:
    try:
        return get_all_leads()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Database error: {e}")


@router.get("/{lead_id}", response_model=StoredLead)
def get_lead(lead_id: str) -> StoredLead:
    try:
        lead = get_lead_by_id(lead_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Database error: {e}")
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

import os
import psycopg2
import psycopg2.extras
from app.models import LeadInput, LeadAnalysis, StoredLead


def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def save_lead(lead: LeadInput, analysis: LeadAnalysis) -> str:
    sql = """
        INSERT INTO leads (
            name, company, email, message, source,
            category, priority, score, company_size_estimate, budget_signal,
            requires_human_followup, key_signals, suggested_action, confidence
        ) VALUES (
            %(name)s, %(company)s, %(email)s, %(message)s, %(source)s,
            %(category)s, %(priority)s, %(score)s, %(company_size_estimate)s, %(budget_signal)s,
            %(requires_human_followup)s, %(key_signals)s, %(suggested_action)s, %(confidence)s
        )
        RETURNING id
    """
    params = {
        **lead.model_dump(),
        "category": analysis.category,
        "priority": analysis.priority,
        "score": analysis.score,
        "company_size_estimate": analysis.company_size_estimate,
        "budget_signal": analysis.budget_signal,
        "requires_human_followup": analysis.requires_human_followup,
        "key_signals": analysis.key_signals,
        "suggested_action": analysis.suggested_action,
        "confidence": analysis.confidence,
    }
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            lead_id = str(cur.fetchone()[0])
        conn.commit()
        return lead_id
    finally:
        conn.close()


def get_all_leads() -> list[StoredLead]:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM leads ORDER BY created_at DESC")
            rows = cur.fetchall()
        return [StoredLead(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_lead_by_id(lead_id: str) -> StoredLead | None:
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
            row = cur.fetchone()
        return StoredLead(**dict(row)) if row else None
    finally:
        conn.close()

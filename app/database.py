import logging
import os
import psycopg2

logger = logging.getLogger(__name__)

_CREATE_LEADS_TABLE = """
CREATE TABLE IF NOT EXISTS leads (
    id                      uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at              timestamptz DEFAULT now(),
    name                    text        NOT NULL,
    company                 text        NOT NULL,
    email                   text        NOT NULL,
    message                 text        NOT NULL,
    source                  text        NOT NULL,
    status                  text        NOT NULL DEFAULT 'new',
    category                text        NOT NULL,
    priority                text        NOT NULL,
    score                   integer     NOT NULL CHECK (score >= 0 AND score <= 100),
    company_size_estimate   text        NOT NULL,
    budget_signal           text        NOT NULL,
    requires_human_followup boolean     NOT NULL,
    key_signals             text[]      NOT NULL DEFAULT '{}',
    suggested_action        text        NOT NULL,
    confidence              float       NOT NULL CHECK (confidence >= 0 AND confidence <= 1)
);
"""


def create_tables() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set — skipping table creation")
        return
    try:
        conn = psycopg2.connect(database_url)
        try:
            with conn.cursor() as cur:
                cur.execute(_CREATE_LEADS_TABLE)
            conn.commit()
            logger.info("Table 'leads' ready")
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Could not connect to database — skipping table creation: %s", e)

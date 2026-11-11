-- Run this in Supabase SQL Editor (Dashboard -> SQL Editor -> New query)

CREATE TABLE leads (
    id                    uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at            timestamptz DEFAULT now(),

    -- Lead input
    name                  text        NOT NULL,
    company               text        NOT NULL,
    email                 text        NOT NULL,
    message               text        NOT NULL,
    source                text        NOT NULL,
    status                text        NOT NULL DEFAULT 'new',

    -- AI analysis
    category              text        NOT NULL,
    priority              text        NOT NULL,
    score                 integer     NOT NULL CHECK (score >= 0 AND score <= 100),
    company_size_estimate text        NOT NULL,
    budget_signal         text        NOT NULL,
    requires_human_followup boolean   NOT NULL,
    key_signals           text[]      NOT NULL DEFAULT '{}',
    suggested_action      text        NOT NULL,
    confidence            float       NOT NULL CHECK (confidence >= 0 AND confidence <= 1)
);

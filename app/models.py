from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class LeadInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(min_length=10, max_length=2000)
    source: str = Field(default="contact_form", max_length=50)


class LeadAnalysis(BaseModel):
    category: Literal[
        "automation_inquiry",
        "pricing_inquiry",
        "support",
        "partnership",
        "spam",
        "other",
    ]
    priority: Literal["low", "medium", "high"]
    score: int = Field(ge=0, le=100)
    company_size_estimate: Literal["solo", "small", "medium", "large", "enterprise"]
    budget_signal: Literal["none", "low", "medium", "high", "open"]
    requires_human_followup: bool
    key_signals: list[str]
    suggested_action: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)


class LeadResponse(BaseModel):
    id: str | None = None
    status: Literal["new", "contacted", "qualified", "rejected"] = "new"
    lead: LeadInput
    analysis: LeadAnalysis


class StoredLead(BaseModel):
    id: str
    created_at: datetime
    name: str
    company: str
    email: str
    message: str
    source: str
    status: str
    category: str
    priority: str
    score: int
    company_size_estimate: str
    budget_signal: str
    requires_human_followup: bool
    key_signals: list[str]
    suggested_action: str
    confidence: float

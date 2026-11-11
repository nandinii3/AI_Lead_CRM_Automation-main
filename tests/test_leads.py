from unittest.mock import MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import LeadAnalysis
from app.services.slack_service import should_notify

client = TestClient(app)

VALID_LEAD = {
    "name": "Aarav Sharma",
    "company": "Nexa Logistics Pvt. Ltd.",
    "email": "aarav.sharma@nexalogistics.in",
    "message": "We need a solution to automate customer support. We have a team of 80 people and handle about 500 inquiries each month.",
    "source": "contact_form",
}

MOCK_ANALYSIS = LeadAnalysis(
    category="automation_inquiry",
    priority="high",
    score=82,
    company_size_estimate="medium",
    budget_signal="open",
    requires_human_followup=True,
    key_signals=["80-person team", "automation need"],
    suggested_action="Schedule discovery call within 24h",
    confidence=0.88,
)


@pytest.fixture(autouse=True)
def mock_openai():
    with patch("app.routers.leads.analyze_lead", return_value=MOCK_ANALYSIS):
        yield


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_200():
    response = client.post("/leads/analyze", json=VALID_LEAD)
    assert response.status_code == 200


def test_analyze_response_shape():
    response = client.post("/leads/analyze", json=VALID_LEAD)
    body = response.json()
    assert "status" in body
    assert "lead" in body
    assert "analysis" in body
    assert body["status"] == "new"


def test_analyze_score_range():
    response = client.post("/leads/analyze", json=VALID_LEAD)
    score = response.json()["analysis"]["score"]
    assert 0 <= score <= 100


def test_analyze_invalid_email():
    bad_lead = {**VALID_LEAD, "email": "not-an-email"}
    response = client.post("/leads/analyze", json=bad_lead)
    assert response.status_code == 422


def test_analyze_message_too_short():
    bad_lead = {**VALID_LEAD, "message": "za"}
    response = client.post("/leads/analyze", json=bad_lead)
    assert response.status_code == 422


LOW_VALUE_ANALYSIS = MOCK_ANALYSIS.model_copy(
    update={"priority": "low", "score": 25, "requires_human_followup": False}
)


def test_should_notify_thresholds():
    assert should_notify(MOCK_ANALYSIS) is True  # high priority + score 82
    assert should_notify(LOW_VALUE_ANALYSIS) is False  # low priority + score 25
    score_only = LOW_VALUE_ANALYSIS.model_copy(update={"score": 70})
    assert should_notify(score_only) is True  # score >= threshold wins


def test_analyze_sends_slack_for_hot_lead(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")
    mock_response = MagicMock()
    with patch("app.services.slack_service.httpx.post", return_value=mock_response) as mock_post:
        response = client.post("/leads/analyze", json=VALID_LEAD)
    assert response.status_code == 200
    mock_post.assert_called_once()
    sent_text = mock_post.call_args.kwargs["json"]["text"]
    assert VALID_LEAD["name"] in sent_text
    assert VALID_LEAD["company"] in sent_text
    assert str(MOCK_ANALYSIS.score) in sent_text
    assert MOCK_ANALYSIS.suggested_action in sent_text


def test_analyze_ok_when_slack_fails(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST")
    with patch(
        "app.services.slack_service.httpx.post",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        response = client.post("/leads/analyze", json=VALID_LEAD)
    assert response.status_code == 200


def test_analyze_skips_slack_without_webhook(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    with patch("app.services.slack_service.httpx.post") as mock_post:
        response = client.post("/leads/analyze", json=VALID_LEAD)
    assert response.status_code == 200
    mock_post.assert_not_called()

from datetime import UTC, date, datetime

import httpx
import pytest

import server


@pytest.fixture
def mock_transport(monkeypatch):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/advanced-search/companies"):
            return httpx.Response(
                200,
                json={"total_results": 1, "items": [{"company_number": "01234567", "title": "Acme Ltd"}]},
            )
        return httpx.Response(
            200,
            json={
                "company_number": "01234567",
                "company_name": "Acme Ltd",
                "company_status": "active",
                "type": "ltd",
                "accounts": {"next_due": "2020-01-01", "overdue": True},
                "confirmation_statement": {"next_due": "2099-01-01", "overdue": False},
            },
        )

    original = server.httpx.AsyncClient

    class Client(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(server.httpx, "AsyncClient", Client)
    monkeypatch.setenv("COMPANIES_HOUSE_API_KEY", "test-key")
    yield requests
    monkeypatch.setattr(server.httpx, "AsyncClient", original)


@pytest.mark.asyncio
async def test_search_is_one_request_and_caps_results(mock_transport):
    result = await server.advanced_company_search(name="Acme", page=2, page_size=5)
    assert result["companies"][0]["company_number"] == "01234567"
    assert len(mock_transport) == 1
    assert mock_transport[0].url.params["start_index"] == "5"
    assert mock_transport[0].headers["authorization"].startswith("Basic ")


@pytest.mark.asyncio
async def test_details_computes_days_overdue(mock_transport):
    result = await server.company_details("01234567")
    assert result["company_name"] == "Acme Ltd"
    assert result["accounts"]["days_overdue"] == (
        datetime.now(UTC).date() - date(2020, 1, 1)
    ).days
    assert result["confirmation_statement"]["days_overdue"] == 0
    assert result["source_endpoint"].endswith("/company/01234567")


@pytest.mark.asyncio
async def test_search_caps_page_size_at_five(mock_transport):
    result = await server.advanced_company_search(page_size=6)
    assert result["page_size"] == 5
    assert mock_transport[0].url.params["size"] == "5"

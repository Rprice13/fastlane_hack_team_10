"""FastMCP server exposing a small, audited Companies House API surface."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://api.company-information.service.gov.uk"
MAX_PAGE_SIZE = 5

mcp = FastMCP("companies-house-mcp", stateless_http=True, json_response=True)


def _api_key() -> str:
    key = os.environ.get("COMPANIES_HOUSE_API_KEY")
    if not key:
        raise RuntimeError("COMPANIES_HOUSE_API_KEY is not configured")
    return key


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make one authenticated Companies House request."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
        response = await client.get(path, params=params, auth=(_api_key(), ""))
        response.raise_for_status()
        return response.json()


def _date_value(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _days_overdue(due_date: str | None, today: date | None = None) -> int:
    due = _date_value(due_date)
    if due is None:
        return 0
    current_date = today or datetime.now(UTC).date()
    return max(0, (current_date - due).days)


def _company_summary(item: dict[str, Any]) -> dict[str, Any]:
    address = item.get("registered_office_address") or {}
    return {
        "company_number": item.get("company_number"),
        "company_name": item.get("title") or item.get("company_name"),
        "company_status": item.get("company_status"),
        "company_type": item.get("company_type"),
        "date_of_creation": item.get("date_of_creation"),
        "registered_office": {
            key: address.get(key)
            for key in ("address_line_1", "address_line_2", "locality", "region", "postal_code", "country")
            if address.get(key)
        },
        "sic_codes": item.get("sic_codes", []),
    }


@mcp.tool()
async def advanced_company_search(
    sic_code: str | None = None,
    location: str | None = None,
    name: str | None = None,
    status: str | None = None,
    incorporated_from: str | None = None,
    incorporated_to: str | None = None,
    page: int = 1,
    page_size: int = MAX_PAGE_SIZE,
) -> dict[str, Any]:
    """Search Companies House with optional filters, returning at most five results."""
    if page < 1:
        raise ValueError("page must be at least 1")
    if page_size < 1:
        raise ValueError("page_size must be at least 1")
    page_size = min(page_size, MAX_PAGE_SIZE)
    for value, label in ((incorporated_from, "incorporated_from"), (incorporated_to, "incorporated_to")):
        if value and _date_value(value) is None:
            raise ValueError(f"{label} must be an ISO date (YYYY-MM-DD)")

    params = {
        key: value
        for key, value in {
            "sic_codes": sic_code,
            "location": location,
            "company_name_includes": name,
            "company_status": status,
            "incorporated_from": incorporated_from,
            "incorporated_to": incorporated_to,
            "size": page_size,
            "start_index": (page - 1) * page_size,
        }.items()
        if value is not None and value != ""
    }
    payload = await _get("/advanced-search/companies", params)
    items = payload.get("items", [])
    return {
        "page": page,
        "page_size": page_size,
        "total_results": payload.get("total_results", len(items)),
        "companies": [_company_summary(item) for item in items[:MAX_PAGE_SIZE]],
        "source_endpoint": f"{BASE_URL}/advanced-search/companies",
        "retrieved_at": datetime.now(UTC).isoformat(),
    }


@mcp.tool()
async def company_details(company_number: str) -> dict[str, Any]:
    """Return useful audited fields and filing timeliness for a company."""
    if not company_number or not company_number.strip():
        raise ValueError("company_number is required")
    number = company_number.strip().upper()
    payload = await _get(f"/company/{number}")
    accounts = payload.get("accounts") or {}
    confirmation = payload.get("confirmation_statement") or {}
    accounts_due = accounts.get("next_due")
    confirmation_due = confirmation.get("next_due")
    return {
        "company_number": payload.get("company_number", number),
        "company_name": payload.get("company_name"),
        "company_status": payload.get("company_status"),
        "company_type": payload.get("type"),
        "date_of_creation": payload.get("date_of_creation"),
        "date_of_cessation": payload.get("date_of_cessation"),
        "registered_office": payload.get("registered_office_address"),
        "sic_codes": payload.get("sic_codes", []),
        "accounts": {
            "next_due": accounts_due,
            "overdue": accounts.get("overdue"),
            "days_overdue": _days_overdue(accounts_due),
        },
        "confirmation_statement": {
            "next_due": confirmation_due,
            "overdue": confirmation.get("overdue"),
            "days_overdue": _days_overdue(confirmation_due),
        },
        "source_endpoint": f"{BASE_URL}/company/{number}",
        "retrieved_at": datetime.now(UTC).isoformat(),
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )

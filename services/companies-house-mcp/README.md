# Companies House MCP server

Challenge 2's standalone [FastMCP](https://gofastmcp.com/) service. It uses
streamable HTTP, so it can run directly on Cloud Run (the default port is
`8080`).

## Tools

* `advanced_company_search` supports SIC code, location, name, status,
  incorporation date range, and page pagination. A request is capped at one
  Companies House API call and five results (`page_size` must be 1–5).
* `company_details` looks up one company and returns selected audited fields,
  including server-computed days overdue for accounts and confirmation
  statements.

The API key is read only from `COMPANIES_HOUSE_API_KEY`; do not commit it.

## Run locally

```sh
cp .env.example .env
export COMPANIES_HOUSE_API_KEY='your-key'
pip install -e '.[dev]'
python server.py
```

The MCP endpoint is available at `http://localhost:8080/mcp` by default.
Cloud Run sets `PORT` and the container honors that value.

Tests use mocked HTTP and never call Companies House:

```sh
pytest
```

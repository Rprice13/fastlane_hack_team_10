# Fastlane Hack Team 10

This repository contains the Northgate UK Market Entry & Competitive
Intelligence Analyst, a minimal Google ADK Python agent.

## Agent

The agent lives in
[`agents/northgate-market-analyst`](./agents/northgate-market-analyst). It helps
relationship managers structure UK market-entry assessments while clearly
separating evidence, assumptions, and missing data.

## Safe local setup

The repository includes a placeholder-only environment template:

```bash
cd agents/northgate-market-analyst
cp .env.example .env
```

Edit `.env` locally with a Google Cloud project you are authorised to use. Do
not commit `.env`, credentials, access tokens, or generated evaluation output.

Install dependencies and run a local smoke test:

```bash
agents-cli install
agents-cli run "I'm thinking about opening a second veterinary practice in Bristol. Is that a good idea?"
```

For interactive testing:

```bash
agents-cli playground
```

See the agent-specific [README](./agents/northgate-market-analyst/README.md)
for deployment and evaluation commands.
# AkhileshVarsityProject

FastAPI service for AuraMatch AI.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, with health checks at
`/api/v1/health` and `/api/v1/health/deep`.

## Run with Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Test

```bash
pytest
```
AuraMatch AI, is an Autonomous Agentic Persona Negotiation and Matchmaking Platform that replaces manual profile swiping with automated, agent-driven matchmaking.   Instead of browsing photos and bios, a user delegates the initial dating and vetting process to a personal AI agent that discovers what they want, finds prospective candidates, and negotiates compatibility with other users' AI agents behind the scenes.   End-to-End User Experience & FlowConversational Onboarding (Persona Discovery):A user interacts with an onboarding AI agent via a conversational chat interface.   The AI iteratively extracts lifestyle traits, deep core values, and non-negotiables (e.g., location, relocation plans, smoking, kids, communication styles) into a structured JSON profile.   This profile is converted into a high-dimensional vector embedding stored in PostgreSQL via pgvector.   Automated Candidate Filtering:When looking for matches, the system performs a vector similarity search using an HNSW index to quickly filter through thousands of profiles down to the most semantically relevant candidate pool in roughly 12 ms.   Background Agent-to-Agent (A2A) Negotiation:Instead of serving candidate cards immediately to the user, the platform spins up background sandboxes where the user's AI agent meets the prospective matches' AI agents.   Over multiple conversational turns, the two agents exchange typed data payloads (DealbreakerCheck, Offer, Evaluation).   They test non-negotiables, propose compromises, evaluate core value alignment, and verify dealbreakers off the main thread using Redis task queues.   The Final Match Presentation (Explainable Match Synthesis):The user opens their dashboard and receives a curated list of top compatible candidates.   Each match is paired with:A Compatibility Index (0–100%).   An AI-Generated Summary explaining why they match, where their values align, and what potential trade-offs were negotiated by their agents.   An inspection view of the multi-turn agent dialogue transcript.   

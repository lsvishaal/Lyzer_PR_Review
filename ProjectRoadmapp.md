# Project Roadmap: Automated GitHub PR Review Agent (Lyzr Backend Intern Challenge)

---

## Phase 1: Environment & Tooling Setup

### Tasks
- Install and configure **UV** for Python package management and environment isolation.
- Set Python version to **3.12** (ensure compatibility).
- Scaffold project layout: `src/`, `tests/`, `.vscode/`, `docker/`, `.github/`, `scripts/` directories.
- Initialize **FastAPI** app, with `main.py` and separate routers.
- Define **Pydantic models** for core datatypes: PR, diff, code chunk, comments, agent config.
- **Add a Pydantic `Settings` class (pydantic-settings) with fields like `LLM_BASE_URL` and `LLM_MODEL_NAME`, defaulting to the local Ollama service (for example `http://ollama:11434` and `qwen2.5-coder:3b`).**
- Add `.gitignore` with exclusions for bytecode, venv, logs, secrets, Docker artifacts, IDE files.
- Create `README.md` with: project overview, setup steps, architecture diagram, goal checklist, and a note that the LLM runs locally via Ollama so **no external API keys are required**.
- Add `pyproject.toml` for dependencies, managed/locked by UV.
- Prepare VS Code workspace files, initial launch.json and settings.json scaffolding.

### Deliverables
- `pyproject.toml` and UV lockfile
- Project structure (`src/`, `tests/`, etc.)
- Initial FastAPI server with hello-world endpoint
- Core Pydantic models scaffolded in `src/models.py`
- **Pydantic `Settings` class including `LLM_BASE_URL` and `LLM_MODEL_NAME` wired into the app, pointing to the local Ollama service instead of any external API.**
- .gitignore & README.md committed, with README explicitly mentioning "local LLM via Dockerized Ollama, no paid API keys."

---

## Phase 2: Docker & Containerization

### Tasks
- Write multi-stage **Dockerfile**:
    - Builder stage: dependency install, test/lint
    - Runtime: minimal, non-root user, healthcheck
- Optimize Docker layers: batch RUNs, only copy necessary files
- Configure `.dockerignore` for maximum cache and minimal context
- Target `python:3.12-slim` image for the **API container** (keep <300MB after all dependencies)
- **Create `docker-compose.yaml` with four core services:**
    - **`ollama` (LLM backend) using the official `ollama/ollama` image, exposing port 11434 and mounting a `ollama_data` volume at `/root/.ollama` for model storage.**
    - api (FastAPI) configured with `LLM_BASE_URL=http://ollama:11434` and `LLM_MODEL_NAME=qwen2.5-coder:3b` via environment variables.
    - prometheus (metrics)
    - grafana (dashboard)
- **Document a one-time `docker exec -it ollama ollama pull qwen2.5-coder:3b` step in README to download the local code model into the `ollama` container.**
- Write build & run scripts or Makefile for easy dev/prod tasks (for example, `docker compose up --build api ollama prometheus grafana`).

### Deliverables
- Production-ready Dockerfile for the FastAPI API container (multi-stage, non-root, healthcheck)
- `.dockerignore` excluding all non-essential files
- **`docker-compose.yaml` linking `ollama`, `api`, `prometheus`, and `grafana`, with `ollama_data` volume for model persistence and `LLM_BASE_URL` / `LLM_MODEL_NAME` wired into the `api` service.**
- CLI build/run instructions in README, including:
    - How to start only Ollama and pull the model.
    - How to start the full stack (`docker compose up --build`).

---

## Phase 3: GitHub Integration & Diff Parsing

### Tasks
- Integrate **GitHub REST API** via httpx or PyGithub
    - Authentication via PAT in env/config
    - Fetch PR list and metadata
    - Download diff, patch, and file changes
- Implement Python **diff parser**:
    - Split into files, hunks, line changes
    - Populate Pydantic models for each diff structure
- Add manual diff-paste option (for API-only testing)
- Create test cases for diff parsing, and validate against real PRs

### Deliverables
- Secure github API client & config
- Diff parser module with tests
- Endpoints and scripts to fetch/parse PRs
- Manual diff input method

---

## Phase 4: Agent Architecture & Multi-Agent Orchestration

### Tasks
- Modular agent design: BaseManager, LogicAgent, ReadabilityAgent, PerformanceAgent, SecurityAgent
- Define clear agent interfaces (async, structured I/O)
- **Introduce an `LLMClient` abstraction that uses `httpx.AsyncClient` to call the Ollama REST API (`/api/generate`) using `LLM_BASE_URL` and `LLM_MODEL_NAME` from settings; agents must depend on this client instead of making raw HTTP requests.**
- Implement agent orchestration:
    - Parallel/async reasoning across chunks/files
    - Feedback cycle or decision ranking (if advanced)
- Abstract agent orchestration for future extension: plug in LangChain, Lyzr Agent Studio, or other frameworks by swapping the `LLMClient` implementation, without changing agent code.
- Add auto-discovery and config-driven agent enablement
- Unit tests for agent input/output, ensemble logic, and fake `LLMClient` responses so the agent layer is testable without a running Ollama instance.

### Deliverables
- agent base and specialized agent modules
- Orchestrator with agent registry/config
- Sample agent implementations (logic, readability, performance, security) all consuming `LLMClient` rather than directly calling any LLM API.
- **Concrete `LLMClient` implementation for Ollama (including configuration and error handling) plus a fake/mock `LLMClient` for unit tests.**
- Agent layer covered with tests, including tests that run with the fake `LLMClient` so CI does not need a running Ollama service.

---

## Phase 5: API Layer & Preview

### Tasks
- Build REST endpoints:
    - `/review/pr` accepts PR id or diff; returns comments
    - `/metrics` for Prometheus scraping
    - `/health` for health status
- Add OpenAPI/Swagger docs via FastAPI
- Implement Pydantic-driven request/response schemas
- Document API in README: endpoint descriptions, sample payloads
- Prepare cURL/Postman/Insomnia scripts for functional testing
- Integration tests for main API flows

### Deliverables
- Fully documented API endpoints
- Swagger UI visible in browser
- API contract with sample requests
- API testing scripts and coverage

---

## Phase 6: Expert Logging, Monitoring & Performance

### Tasks
- Implement **structured logging** (JSON, trace/context fields) using stdlib or structlog/loguru
- Set environment-driven log levels (info/debug/error/fatal)
- Enrich logs with unique request IDs, agent execution time, PR info, error context
- Log sampling for high-frequency calls
- Set up Prometheus with **prometheus-fastapi-instrumentator** for key metrics
- Integrate Grafana dashboard, chart latency/error/throughput
- Monitor Docker stats for resource usage
- Advanced: add OpenTelemetry tracing (if time permits)

### Deliverables
- Structured log output, sample logs in README
- /metrics endpoint with exportable metrics
- Grafana dashboard template and example screenshots
- Logging summarization and troubleshooting guide

---

## Phase 7: VSCode Workspace & Developer Experience

### Tasks
- Setting up `.vscode/launch.json` for debugging FastAPI (reload, breakpoints)
- Extend `settings.json` for linting/formatting (ruff, black), Python path, workspace recs
- Optionally add `devcontainer.json` for Docker-based VSCode dev
- Write `scripts/init.sh` to bootstrap dev environment
- Document VSCode extension recommendations, debugging workflow, common issues

### Deliverables
- .vscode configs committed
- Devcontainer scaffold (if used)
- README section on VSCode setup and quickstart

---

## Phase 8: Security & Best Practices

### Tasks
- Store all secrets in `.env` or Docker secrets; never checked in or hardcoded
- Mask/redact secrets from logs and agent outputs
- Secure API endpoints (`admin`, `review`) with JWT or minimal auth (if required by scope)
- Implement security agent logic (detect OWASP/code issues in review)
- Follow GitHub security guidelines: sanitize diffs, avoid code injection, restrict scope
- Document/scan for common security pitfalls

### Deliverables
- Examples of secure secrets handling
- Docs on secure API and agent practices
- Security tests and code review samples

---

## Phase 9: Demo, Docs & Submission Prep

### Tasks
- Script and record demo video (project tour, agent flow, API and dashboard demo)
- Take screenshots/GIFs of critical flows (Swagger docs, healthcheck, metrics, Grafana)
- Polish README: architecture diagrams, setup/usage, extending the system, troubleshooting
- Prepare submission checklist:
    - All requirements met
    - Repo clean, structured, readable
    - Docs and launch steps easy to follow
    - Demo assets attached (video, README links)
    - Solution is extensible, testable, documented

### Deliverables
- Submission-ready README and video/GIFs
- Architecture and demo artifacts
- Submission checklist complete and visible at repo root

---

## Phase 10: Performance & Optimization

### Tasks
- Profile agent runner throughput; record base latency per agent, per review batch
- Optimize Docker image (remove unused deps, slim wheels, distroless if possible)
- Benchmark startup time, resource consumption (CPU/mem)
- Document how Prometheus/Grafana improves observability and ROI
- Prepare automated or sample test plans, generate test output for reviewers
- Final QA on logging, metrics, endpoint responsiveness, and failure modes

### Deliverables
- Benchmark results in README and/or Grafana
- Final image size <300MB, build time screenshots
- Automated test logs/output for review
- Tuning summary, optimizations list

---

**Each phase delivers concrete, testable artifacts. Track progress via commits and tick them off in README or a project board. This plan will catch omissions and ensure a thorough, industry-grade submission.**

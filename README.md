# Lyzer PR Review Agent 🤖

> **Automated GitHub PR Review Agent with Multi-Agent LLM System**

A production-grade FastAPI application that automatically reviews GitHub Pull Requests using specialized AI agents for logic analysis, readability, performance, and security.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![UV](https://img.shields.io/badge/UV-package%20manager-orange.svg)](https://github.com/astral-sh/uv)

---

## 🎯 Features

- **Multi-Agent Architecture**: Specialized agents for different review aspects
  - Logic Agent: Detects logical flaws and edge cases
  - Readability Agent: Improves code clarity and maintainability
  - Performance Agent: Identifies optimization opportunities
  - Security Agent: Catches security vulnerabilities

- **Production-Ready**
  - Structured JSON logging with context
  - Prometheus metrics integration
  - Docker containerization with multi-stage builds
  - Comprehensive error handling
  - Type-safe with Pydantic models

- **GitHub Integration**
  - Fetch PRs directly from GitHub API
  - Parse diffs into structured format
  - Support for manual diff input

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Layer                       │
│                    (HTTP Endpoints)                     │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼──────────┐
         │   Agent Manager      │
         │   (Orchestrator)     │
         └───────────┬──────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼────┐  ┌─────▼─────┐
│  Logic    │  │ Reading │  │Performance│
│  Agent    │  │ Agent   │  │  Agent    │
└───────────┘  └─────────┘  └───────────┘
```

### Layer Separation (SoC)

```
src/
└── app/
    ├── api/          # HTTP endpoints (thin layer)
    ├── agents/       # Agent logic (core reasoning)
    ├── github/       # GitHub API client
    ├── diff/         # Diff parser
    ├── core/         # Config & logging
    └── models/       # Pydantic models
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- UV package manager
- GitHub Personal Access Token (for PR fetching)
- OpenAI API Key (for LLM agents)

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd Lyzer_PR_Review
```

2. **Install UV** (if not already installed)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. **Create virtual environment and install dependencies**
```bash
uv sync
```

4. **Create .env file from template**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Run the application**
```bash
uv run uvicorn src.app.main:app --reload
```

The API will be available at `http://localhost:8000`

---

## 📚 API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### `GET /`
Root endpoint with API information.

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "pr-review-agent"
}
```

#### `GET /version`
Version and configuration information.

#### `GET /metrics`
Prometheus metrics endpoint.

---

## 🔧 Configuration

Configuration is managed through environment variables. See `.env.example` for all available options.

### Key Environment Variables

```bash
# GitHub
GITHUB_TOKEN=your_token_here

# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4

# Logging
LOG_LEVEL=info
LOG_FORMAT=json  # or "console" for development

# Server
PORT=8000
DEBUG=false
```

---

## 🧪 Testing

Run tests with pytest:

```bash
uv run pytest
```

Run with coverage:

```bash
uv run pytest --cov=src --cov-report=html
```

---

## 🐳 Docker

### Build

```bash
docker build -t lyzer-pr-review:latest .
```

### Run

```bash
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_token \
  -e OPENAI_API_KEY=your_key \
  lyzer-pr-review:latest
```

### Docker Compose

```bash
docker-compose up --build
```

This starts:
- FastAPI application on port 8000
- Prometheus on port 9090
- Grafana on port 3000

---

## 📊 Monitoring

### Prometheus Metrics

Available at `/metrics` endpoint:
- Request count and latency
- Agent execution time
- Error rates

### Grafana Dashboards

Access Grafana at `http://localhost:3000` (default credentials: admin/admin)

Pre-configured dashboards include:
- API performance
- Agent execution metrics
- System health

---

## ��️ Development

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
uv run pre-commit install
```

---

## 📖 Project Structure

```
Lyzer_PR_Review/
├── src/
│   └── app/
│       ├── api/              # API endpoints
│       ├── agents/           # AI agents
│       ├── core/             # Configuration & logging
│       ├── diff/             # Diff parsing
│       ├── github/           # GitHub integration
│       ├── models/           # Pydantic models
│       └── main.py           # FastAPI app
├── tests/                    # Test suite
├── docker/                   # Docker configs
├── scripts/                  # Utility scripts
├── .github/                  # Documentation
├── pyproject.toml           # Dependencies
├── Dockerfile               # Production image
└── docker-compose.yml       # Multi-service setup
```

---

## 🎓 Core Principles

This project follows strict software engineering principles:

1. **YAGNI**: Build only what's needed now
2. **SoC**: Clear separation of concerns across layers
3. **KISS**: Simple, maintainable solutions
4. **DRY**: Single source of truth for all logic
5. **Self-Documenting**: Type hints and clear naming

See `.github/copilot-instructions.md` for detailed guidelines.

---

## 📝 Phase 1 Checklist

- [x] Python 3.12 setup with UV
- [x] Project structure (src/, tests/, etc.)
- [x] Pydantic models (PR, FileDiff, CodeChunk, ReviewComment)
- [x] Settings management with pydantic-settings
- [x] Structured logging with structlog
- [x] FastAPI app with health endpoints
- [x] Prometheus metrics integration
- [x] Comprehensive .gitignore
- [x] Documentation (README.md)

---

## 🚧 Roadmap

### Phase 2: Docker & Containerization
- Multi-stage Dockerfile
- Docker Compose setup
- Prometheus & Grafana integration

### Phase 3: GitHub Integration
- GitHub API client
- Diff parser implementation
- PR fetching and parsing

### Phase 4: Agent Implementation
- Base agent architecture
- Specialized agent implementations
- Agent orchestration

### Phase 5: API Enhancement
- Review endpoint implementation
- Request/response validation
- Error handling

---

## 📄 License

[Add your license here]

---

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

---

## 📞 Contact

[Add contact information]

---

**Built with ❤️ for the Lyzr Backend Intern Challenge**

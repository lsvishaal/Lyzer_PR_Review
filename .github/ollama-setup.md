# Copilot Instructions: Dockerized Ollama + Local Code Model

_This document defines how to set up and use a **local LLM backend via Ollama** for the Automated GitHub PR Review Agent, with best practices for Docker, model choice, and API integration._

---

## Goals

- Use a **local, free LLM** for code review; **no paid API keys or cloud LLMs**.
- Run **Ollama in Docker** as a dedicated `ollama` service, and the PR-review API as a separate `api` service in the same `docker-compose` network.
- Use a **code-specific model** optimized for code generation and reasoning, such as `qwen2.5-coder:3b` or `qwen2.5-coder:7b`.
- Communicate with the model via a **typed `LLMClient`** using `httpx.AsyncClient`, with base URL and model name coming from configuration, **never hardcoded**.

---

## Model Choice

**Primary recommendation (default):**  
- **`qwen2.5-coder:3b`** or **`qwen2.5-coder:7b`**
  - Code-specific models tuned for code generation, reasoning, and fixing
  - Good balance between capability and RAM/GPU usage (3B: ~4GB RAM, 7B: ~8GB RAM)
  - Faster inference than larger models

**Alternative:**
- **`codellama:7b-instruct`**
  - Meta's code-specialized Llama 2
  - Tuned for following instructions for debugging and explaining code

**Default for this project**: `qwen2.5-coder:3b` (best performance/resource balance)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose Network              │
│                                                      │
│  ┌────────────────┐         ┌──────────────────┐   │
│  │   API Service  │────────▶│  Ollama Service  │   │
│  │   (FastAPI)    │  HTTP   │  (LLM Backend)   │   │
│  │  Port: 8000    │ :11434  │  Port: 11434     │   │
│  └────────────────┘         └──────────────────┘   │
│                                      │              │
│                              ┌───────▼────────┐    │
│                              │ ollama_data    │    │
│                              │ (Named Volume) │    │
│                              └────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

- [ ] Add `ollama` service to docker-compose.yml
- [ ] Create `LLMClient` abstraction in `src/app/llm/client.py`
- [ ] Update Settings to include Ollama config
- [ ] Wire `LLMClient` into agent architecture
- [ ] Write tests for `LLMClient` (mocked)
- [ ] Pull and test model locally
- [ ] Update .env.example with Ollama settings

---

## Best Practices

1. **Always use the abstraction**: Never call Ollama directly from agents/routers
2. **Configuration over hardcoding**: Model name and URL from env vars
3. **Test with mocks**: Use fake `LLMClient` for fast unit tests
4. **Async everywhere**: Use `httpx.AsyncClient` for non-blocking calls
5. **Error handling**: Wrap LLM calls with proper try/except and logging
6. **Prompt engineering**: Be explicit about language and context
7. **Resource awareness**: Start with 3B model, scale up only if needed

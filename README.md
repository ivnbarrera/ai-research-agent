# AI Upskill Project

**Blend's AI engineering onboarding curriculum.** A 5-week self-paced project
that takes engineers from async Python through agents, MCP, and evaluation
by building a small AI-powered news pipeline end-to-end.

- **Time commitment:** 1–2 hours per evening, ~5 weeks (38–54 hours total)
- **Format:** Self-paced. Each milestone ends with a PR checkpoint reviewed by two peers.
- **Outcome:** A working multi-agent news pipeline with tests, evaluation, and docs.

---

## Where to start

1. Read [`docs/architecture/overview.md`](docs/architecture/overview.md) for the 20-min big-picture orientation.
2. Open [`docs/milestones/setup.md`](docs/milestones/setup.md) and follow it. It will get you to a working dev environment in one evening.
3. From there, milestones link to the next one in sequence.

---

## Tech stack

- **Python 3.12** with async/await throughout
- **`aiohttp`** for concurrent HTTP, **`feedparser`** for RSS
- **LiteLLM** as the LLM provider abstraction — default model is `claude-haiku-4-5-20251001`, swap to any [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers) by changing one env var
- **MCP (Model Context Protocol)** for tool integration in Milestone 4
- **SQLite** for the database server in Milestone 4
- **pytest + pytest-asyncio** for tests
- **ruff** for formatting and linting

---

## Quickstart

```bash
git clone https://github.com/ivnbarrera/ai-research-agent.git
cd ai-research-agent

uv sync                            # creates .venv and installs all dependencies

cp .env.example .env               # then paste your API key
uv run python scripts/verify_setup.py    # should print all ✅
```

Then open [`docs/milestones/setup.md`](docs/milestones/setup.md).

---

## Repository layout

```
ai-research-agent/
├── README.md                  ← you are here
├── .env.example
├── scripts/
│   └── verify_setup.py        # M0 Task 5 runs this
├── src/                       # students fill this in milestone by milestone
│   ├── models/
│   ├── fetchers/
│   ├── storage/
│   ├── agents/
│   ├── mcp_servers/
│   ├── skills/
│   └── orchestration/
├── tests/
├── data/                      # created at runtime
└── docs/
    ├── architecture/overview.md
    ├── milestones/
```
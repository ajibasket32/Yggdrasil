# Yggdrasil Chronicles

```

If gameplay and AI conflict, gameplay wins.

## Documentation Map

Read these documents in this order:

1. [`AGENTS.md`](AGENTS.md) -- architectural law, AI boundaries, contributor rules
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) -- system layers and runtime boundaries
3. [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md), [`API_SPEC.md`](API_SPEC.md), [`CODING_STANDARDS.md`](CODING_STANDARDS.md), [`SECURITY_GUIDELINES.md`](SECURITY_GUIDELINES.md), [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md) -- implementation contracts
4. [`COMBAT_DESIGN.md`](COMBAT_DESIGN.md), [`JOB_SYSTEM.md`](JOB_SYSTEM.md), [`RAG_DESIGN.md`](RAG_DESIGN.md) -- system design
5. [`DOCUMENTATION_GOVERNANCE.md`](DOCUMENTATION_GOVERNANCE.md), [`DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md), [`SERVICE_LEVEL_OBJECTIVES.md`](SERVICE_LEVEL_OBJECTIVES.md), [`ACCESSIBILITY.md`](ACCESSIBILITY.md), [`SECURITY.md`](SECURITY.md), [`OBSERVABILITY.md`](OBSERVABILITY.md), [`OPERATIONS_RUNBOOK.md`](OPERATIONS_RUNBOOK.md), [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) -- governance, operations, and contribution rules
6. [`RELEASE_PROCESS.md`](RELEASE_PROCESS.md), [`MVP_ROADMAP.md`](MVP_ROADMAP.md), [`TASKS.md`](TASKS.md), [`RELEASE_STATUS.md`](RELEASE_STATUS.md), [`TECH_DEBT.md`](TECH_DEBT.md), [`RISK_REGISTER.md`](RISK_REGISTER.md) -- release execution, planning, and risk control
7. [`WORLD_BIBLE.md`](WORLD_BIBLE.md), [`PRODUCT_VISION.md`](PRODUCT_VISION.md) -- lore and product vision

Supporting records: [`CHANGELOG.md`](CHANGELOG.md), [`RELEASE_NOTES.md`](RELEASE_NOTES.md), [`assets/CATALOG.md`](assets/CATALOG.md), [`docs/adr/`](docs/adr/), and [`DOCUMENTATION_AUDIT.md`](DOCUMENTATION_AUDIT.md).

**Current Version**: v1.1.0-rc.1 (Release Candidate) - 2026-06-18

## Target Stack

- Frontend: React 18, TypeScript strict mode, Vite, Phaser 3, Zustand
- Backend: FastAPI, Python 3.12+, SQLAlchemy 2.x, Alembic, Pydantic v2
- Infrastructure: PostgreSQL 16, Redis 7, Qdrant, Docker Compose, Nginx, Ollama
- AI: Provider-agnostic orchestrator with adapters only under `backend/app/ai/adapters/`

## Beginner Windows Start

If you are a Windows user looking for the easiest way to start the game, please see the [**Windows Quickstart Guide**](WINDOWS_QUICKSTART.md).

## Development Start

### Content Generation Pipeline (Post-Launch)

The game includes a deterministic pipeline for generating new content packs:

1. **Generate**: `python tools/content/generate_content_pack.py --seed 42 --theme sylvan_supply --out content/packs/generated_sylvan_supply`
2. **Validate**: `python tools/content/validate_content_pack.py content/packs/generated_sylvan_supply`
3. **Resolve Assets**: `python tools/content/resolve_asset_manifest.py content/packs/generated_sylvan_supply`
4. **AI Repair (Optional)**: `python tools/content/content_ai_orchestrator.py --pack content/packs/generated_sylvan_supply --repair`

AI is optional and used only as an assistant; the core gameplay remains deterministic.

### Standard Start

Start the complete foundation stack:

```bash
docker compose up --build
```

Development endpoints:

- Application through Nginx: `http://localhost:8080`
- Frontend static container: `http://localhost:3000` (API proxy is not
  available on this direct port; use the Nginx application URL for gameplay)
- Backend directly: `http://localhost:8000`
- Health summary: `http://localhost:8000/health`
- Metrics: `http://localhost:8000/metrics`

Before starting the stack, copy `.env.example` to `.env`. The committed
`.env.example` contains development-only sample values. Never commit a real
`.env` file or production credentials.

## Local Test Start

Run backend integration and regression tests from the repository root on
Windows:

```powershell
.\test-local.ps1
```

The script uses `compose.test.yaml` and the committed safe `.env.test` values.
It starts isolated PostgreSQL, Redis, and Qdrant services on localhost ports
`15432`, `16379`, and `16333`; builds a backend test runner with Poetry dev
dependencies; applies Alembic migrations; verifies canonical migration seed
data; and runs:

```bash
pytest -c pyproject.toml ../tests/integration ../tests/regression
```

Useful variants:

```powershell
.\test-local.ps1 -Suite integration
.\test-local.ps1 -Suite regression
.\test-local.ps1 -KeepServices
.\test-local.cmd -Suite all
```

When `-KeepServices` is not used, the script removes the isolated test volumes
after the run. The `.env.test` file contains only local test credentials and
disables cloud AI providers by using the cached narrative provider.

## MVP Definition

A valid MVP lets a player create a character, explore, fight, progress, accept and complete quests, talk to NPCs, save, load, and continue after cloud AI providers fail.

NPC memory and AI narration are valuable, but they are not allowed to replace deterministic gameplay systems.

## Release Gates

Before any public or stakeholder release:

- `docker compose up --build` starts the complete stack.
- Unit, integration, regression, and E2E tests pass.
- Coverage meets the thresholds in `TESTING_STRATEGY.md`.
- Security scanning passes with no high-severity unresolved findings.
- Save/load is transactional and verified.
- No direct AI provider calls exist outside provider adapters.
- Observability, audit logging, backup, rollback, and incident response are documented and tested.
- Release evidence includes artifact digests, SBOM, provenance, security/license scans, RPO/RTO results, and signed approvals.
- Data inventory, privacy lifecycle, accessibility, originality/IP review, and active risks pass their gates.

## Contributor Start

Before writing code, read:

1. `PRODUCT_VISION.md`
2. `MVP_ROADMAP.md`
3. `TASKS.md`
4. `AGENTS.md`
5. `RELEASE_CHECKLIST.md`
6. `ARCHITECTURE.md`
7. `CODING_STANDARDS.md`
8. The system document related to the selected release

Generated code that violates the engine-first boundary must be rejected and regenerated.
Complete only the first unfinished release and stop before starting the next.

### Troubleshooting Docker Pull Rate Limits
If you encounter `429 Too Many Requests` or `unauthenticated pull rate limit` errors from Docker Hub, you can override the default images to use AWS ECR public mirrors.

Copy the image overrides from `.env.example` into your `.env` or `.env.test` file:

```env
POSTGRES_IMAGE=public.ecr.aws/docker/library/postgres:16.9-alpine
REDIS_IMAGE=public.ecr.aws/docker/library/redis:7.4.2-alpine
NGINX_IMAGE=public.ecr.aws/nginx/nginx:1.28.0-alpine
PYTHON_IMAGE=public.ecr.aws/docker/library/python:3.12.10-slim
NODE_IMAGE=public.ecr.aws/docker/library/node:22.15.0-alpine
```

You can also run the local fallback script `./release-validation.sh --fallback` to run tests locally outside of docker if needed. **Note:** Fallback mode is *only* for partial testing when Docker is unavailable and does not constitute full MVP validation.

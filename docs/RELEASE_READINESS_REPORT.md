# Release Readiness Report

*Last Updated Status Check: 2026-06-19 (v1.2.0 RC1 ready-to-use hardening)*

| Component / Test | Status | Notes |
| :--- | :--- | :--- |
| GitHub CI | PENDING | Local validation complete; remote CI not run in this session |
| Backend tests | PASS | 124 passed via `pytest -c pyproject.toml ../tests` |
| Frontend tests | PASS | 68/68 passing (incl. Shop/Inn flows) |
| Frontend Coverage | PASS | 80.04% branch coverage (Threshold: 80%) |
| Migrations | PASS | `alembic upgrade head`, `downgrade -1`, and re-upgrade verified |
| Docker compose config | PASS | Verified with Docker Desktop command path |
| Docker compose build | PASS | `docker compose build` completed |
| Docker startup and health | PASS | `docker compose up -d`; backend and game URLs returned HTTP 200 |
| E2E ready-to-use smoke | PASS | Playwright path passed through new game, shop, inn, combat, save, reload, continue |
| Shop System | PASS | Buy flow and gold deduction verified |
| Inn System | PASS | HP/MP restoration and cost verified |
| Quest Integration | PASS | Shop/Discovery progression verified |
| Visual Verification | PASS | Shop Overlay and World Panel updates refined |
| Beginner startup scripts | PASS | `start-game.ps1`, `verify-ready.ps1`, `stop-game.ps1` executed successfully |
| Content pipeline workflow | PASS | One-command pipeline writes validation, asset, simulation, and pipeline reports |
| Content import boundary | PASS | Dry-run import refuses missing or failed reports and does not mutate DB |
| Security audits | PASS | `pip-audit` and `npm audit --audit-level=high` reported no vulnerabilities |
| Local shell toolchain | PASS | Validated with bundled Node/Python/Poetry paths and Docker Desktop default path |

**Note**: GitHub CI remains pending until the branch is pushed and remote checks run.

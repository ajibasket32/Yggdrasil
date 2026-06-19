# Ready-to-use Checklist

Status labels: PASS, FAIL, BLOCKED, PARTIAL, SKIPPED.

## Clone and Start
1. Install Docker Desktop.
2. Clone the repository.
3. Open PowerShell in the repository folder.
4. Run `.\start-game.ps1`.
5. Open `http://localhost:8080`.

Status: PASS. `start-game.ps1`, `verify-ready.ps1`, and `stop-game.ps1` were
executed successfully on 2026-06-19. The scripts locate Docker Desktop from the
default Windows install path when Docker is not on PATH.

## Docker Startup Check
- PASS: `compose.yaml` exists.
- PASS: `.env.example` exists and keeps AI provider order on cached fallback.
- PASS: `start-game.ps1` creates `.env` from `.env.example`.
- PASS: `docker compose config`.
- PASS: `docker compose build`.
- PASS: `docker compose up -d`.

Commands:

```powershell
.\verify-ready.ps1
.\start-game.ps1
docker compose logs -f
.\stop-game.ps1
```

## Health Check
- URL: `http://localhost:8000/health`
- Status: PASS. Backend health returned HTTP 200 and the game URL returned HTTP
  200 after Docker startup.

## Gameplay Smoke Test Checklist
- Title screen loads.
- New Game works.
- Character creation works.
- World loads.
- Quest journal opens.
- Shop opens and purchase changes gold/inventory.
- Inn rest restores HP/MP for gold.
- Combat starts.
- Save works.
- Continue loads saved character.

Status: PASS. `frontend/e2e/ready-to-use.spec.ts` passed against the Docker
stack on 2026-06-19.

## Content Pipeline Checklist
- PASS: Generate pack.
- PASS: Validate pack.
- PASS: Resolve assets without download.
- PASS: Simulate pack.
- PASS: Write final report.
- PASS: Import dry-run verifies reports and does not mutate DB.

Commands:

```bash
python tools/content/run_content_pipeline.py --seed 42 --theme sylvan_supply --out content/packs/generated_sylvan_supply
python tools/content/import_content_pack.py content/packs/generated_sylvan_supply
```

## AI and Offline Checklist
- PASS: No cloud API key required for gameplay.
- PASS: Content pipeline does not call cloud AI by default.
- PASS: Optional AI repair writes deterministic fallback advice without keys.
- PASS: AI suggestions cannot mark content approved or import content.

## Troubleshooting
- Docker missing: install Docker Desktop and open a new PowerShell window.
- Docker not running: start Docker Desktop and wait for the engine.
- Port 8080 busy: set `NGINX_PORT=8081` in `.env` and open
  `http://localhost:8081`.
- Clean local database: run `docker compose down -v`. This deletes local
  development saves.
- Logs: run `docker compose logs -f`.

## Known Limitations
- Git, Docker, Poetry, Node/npm, and pytest are not all available on the
  default PATH in this desktop shell, but local validation passed using the
  bundled runtime paths and Docker Desktop's default install path.
- `tools/content/import_content_pack.py --apply` is intentionally refused until
  a backend import service exists.

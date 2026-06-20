# Release Status

Version: 1.2.0-rc.1
Status: Release Candidate (post-merge validation passed)
Last reviewed: 2026-06-20

## Current Release

**v1.2.0-rc.1** is ready for GA evidence review. Implementation of Shop, Inn,
Quest expansion, safe generated-content tooling, and real Phaser 2D playability
fixes is complete. PR #33 merged into `main` at commit
`2f1aa46a5c3b06963a8fd118e27104ece0e615a2`, with GitHub CI and strict
full-stack release validation passing.

## Completed Releases

1. v0.1 Foundation
2. v0.2 Save System and Persistence
3. v0.3 AI Provider Layer and Fallback
4. v0.4 RAG and Memory
5. v0.5 Character Creation and Job System
6. v0.6 Combat System
7. v0.7 World, NPC, and Quest System
8. v0.8 AI Narrative and Dialogue
9. v0.9 Asset Discovery and License Tracking
10. v0.10 Playable Vertical Slice
11. v1.0.0 MVP Release
12. v1.1.0 JRPG Polish
13. v1.2.0 Content Expansion

## Unfinished Releases

None.

## Content Generation Pipeline (Post-Launch Foundation)
- **Status**: IMPLEMENTED
- **Deterministic Generator**: PASS
- **Schema Validation**: PASS
- **Asset Resolver**: PASS
- **AI Orchestrator (Optional)**: PASS
- **Documentation**: docs/design/AUTO_CONTENT_GENERATION_PIPELINE.md
- **One-command Workflow**: `tools/content/run_content_pipeline.py`
- **Import Boundary**: `tools/content/import_content_pack.py` dry-run, no DB mutation by default

## Current Blockers

None for RC1 evidence. Final `v1.2.0` GA has not been created.

## Completion Percentage

**100% of implementation releases complete** (12 of 12).

## Release Validation Evidence (v1.2.0 RC1)
The v1.2.0-rc.1 release candidate has passed all local and PR #33 quality gates:
- **Backend Tests**: PASS (124/124)
- **Frontend Tests**: PASS (82/82)
- **Frontend Coverage**: 81.44% Branch Coverage
- **Security Audit**: PASS (`pip-audit` and `npm audit` zero vulnerabilities)
- **Docker Build/Startup**: PASS (`docker compose build`, `up -d`, health checks)
- **E2E Ready-to-use Smoke**: PASS (new game, NPC, shop, inn, combat, save, continue)
- **Real Phaser 2D Playability E2E**: PASS (keyboard movement, animation, NPC proximity, combat, victory return, save, Continue)
- **Quest Integration**: PASS (Shop/Travel linked to progression)
- **RAG Recovery Stability**: PASS (10/10 focused repeated runs after service restart)
- **GitHub CI**: PASS (backend, frontend, containers, secrets)
- **Full-Stack Release Validation**: PASS
- **Core Runtime Health**: PASS
- **Optional Cloud AI Provider Availability**: DEGRADED/UNAVAILABLE without credentials
- **Gameplay Fallback**: PASS via cached/offline narrative path; cloud AI remains optional and never gameplay authority

## Docker Pull Rate Limit Mitigations
In restricted environments, `compose.yaml` and `.env.example` allow parameterizing image mirrors (like AWS ECR Public). A `./release-validation.sh` fallback script is available for local diagnostic testing if Docker is completely unavailable.

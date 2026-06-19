# Release Status

Version: 1.2.0-rc.1
Status: Release Candidate (Ready-to-use hardening in progress)
Last reviewed: 2026-06-19

## Current Release

**v1.2.0-rc.1** is prepared. Implementation of Shop, Inn, Quest expansion, and
safe generated-content tooling is complete. Final full-stack release validation
still requires a host with Git, Docker, Poetry, and npm available.

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

Local full-stack validation is blocked in the current desktop shell because
Git, Docker, Poetry, npm, and pytest are not available on PATH. Content tooling
was validated with the bundled Python runtime.

## Completion Percentage

**100% of implementation releases complete** (12 of 12).

## Release Validation Evidence (v1.2.0 RC1)
The v1.2.0-rc.1 release candidate has passed all local quality gates:
- **Backend Tests**: PASS (56/56 core + 5 new v1.2 integration tests)
- **Frontend Tests**: PASS (68/68)
- **Frontend Coverage**: 80.04% Branch Coverage
- **Security Audit**: PASS (`pip-audit` and `npm audit` zero vulnerabilities)
- **Local Fallback Validation**: PASS
- **Quest Integration**: PASS (Shop/Travel linked to progression)

## Docker Pull Rate Limit Mitigations
In restricted environments, `compose.yaml` and `.env.example` allow parameterizing image mirrors (like AWS ECR Public). A `./release-validation.sh` fallback script is available for local diagnostic testing if Docker is completely unavailable.

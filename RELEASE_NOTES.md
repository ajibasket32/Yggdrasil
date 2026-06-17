# Release Notes

Version: 1.8
Status: Informational
Last reviewed: 2026-06-14

## Current Status

**v1.0 MVP Release is complete.** No release is currently in progress.

## Latest Release

**v1.0.0 MVP Release**

### Completed

- Added versioned, provider-neutral prompts and player-scoped context assembly for narrative.
- Added strict output validation, cosmetic narrative persistence, and local fallback presentation.
- Completed asset discovery, review, and local integration with full provenance in `assets/CATALOG.md`.
- Integrated Phaser 3 for 2D JRPG World and Combat scenes in the browser.
- Added full transactional Save Game / End Chronicle workflows to the UI.
- Expanded content to the MVP targets: 5 regions, 5 factions, 5 dungeons, and world items.
- Hardened security, verified migrations, and passed `npm audit` and `pip-audit`.
- Passed all unit, integration, and E2E gates, meeting MVP testing thresholds.

### Not Yet Implemented

- Complete production authentication.
- Full post-MVP simulation (economy, housing, multiplayer).

### Known Limitations

- Narrative generation is bounded to four NPC topics plus lore, quest framing,
  and current-location atmosphere.
- The approved local fallback is intentionally generic and cosmetic.
- Idempotent replay does not reconstruct speaker and grounded-memory display
  metadata, although stored text and safety metadata are preserved.
- `X-Player-ID` remains a development-only identity boundary.

### Risks

- Future prompts and providers must continue to pass output validation without
  expanding AI authority over gameplay.
- Asset selection in v0.9 must avoid protected identity and retain complete
  source/license evidence.
- Production authentication remains required before any public release.

### Technical Debt

- Reconstruct speaker and context-count metadata for idempotent narrative
  replay.
- Add production semantic embeddings and broader narrative evaluation data.
- Expand the bounded seed catalog only in the releases that authorize it.

### Next Recommended Release

Maintenance and Content Expansion.

## Release Validation: Validation Process Updates
**Release Version**: 1.0.0
**Date**: 2026-06-16

We have encountered severe Docker Hub 429 rate limit issues during deployment and automated validation steps for the MVP. To circumvent this blocker without rewriting the entire ecosystem:
1. Docker images in `compose.yaml` and `.env.example` are now parameterizable. End-users can define alternative mirrors, such as AWS ECR Public, to retrieve common images like Postgres, Redis, Python, and Node.
2. `release-test.sh` and `release-validation.sh` were added to verify test readiness natively if container pulls fail completely. **Note:** Using `--fallback` testing mode is meant solely as a diagnostic tool and does not mean the system has passed full MVP readiness validation. The MVP is only considered valid if all Docker full-stack validation passes in strict mode.

# Release Notes

Version: 1.8
Status: Informational
Last reviewed: 2026-06-14

## Current Status

**v0.8 AI Narrative and Dialogue is complete.** No release is currently in
progress.

## Latest Release

**v0.8.0 AI Narrative and Dialogue**

### Completed

- Added versioned, provider-neutral prompts for NPC dialogue, lore, quest
  framing, and current-location descriptions.
- Added player-scoped context assembly across canonical memories, NPC profile,
  faction standing, relationship values, quests, location, and recent
  dialogue.
- Added strict output validation, entity boundaries, idempotency, stable
  context hashing, cosmetic narrative persistence, and safe context caching.
- Added fixed-topic NPC choices and JRPG story panels without free-form
  chatbot control.
- Added approved local fallback presentation when providers or Qdrant are
  unavailable.
- Passed 108 backend tests at 84.90% coverage and 33 frontend tests at 94.75%
  statement and 80.43% branch coverage.
- Passed strict typing, lint, formatting, production builds, migration
  rollback/upgrade, dependency audits, secret scanning, healthy deployment,
  and deployed browser verification.

### Not Yet Implemented

- Release-approved visual/audio asset selection, import, attribution, and
  license evidence.
- The complete playable vertical slice and final MVP content breadth.
- Production authentication and public-release operational approvals.

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

Implement **v0.9 Asset Discovery and License Tracking** only after a new user
prompt.

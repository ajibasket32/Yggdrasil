# Release Status

Version: 1.8
Status: Informational
Last reviewed: 2026-06-14

## Current Release

**v1.0 MVP Release** is complete.

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
11. v1.0 MVP Release

## Unfinished Releases

None.

## Current Blockers

None.

## Completion Percentage

**100% of implementation releases complete** (11 of 11).

Task completion is **100%** (63 of 63 release tasks).

## Next Recommended Release

Maintenance and Content Expansion.

## Release Validation Issues
In restricted environments (such as some automated sandboxes), the full MVP critical gameplay journey (including DB-dependent endpoints and UI tests) cannot be validated due to Docker Hub unauthenticated pull rate limits. To mitigate this, `compose.yaml` and `.env.example` allow parameterizing image mirrors (like AWS ECR Public). A `./release-validation.sh` fallback script was added to test code functionality locally using standard package managers as a stopgap measure, but manual confirmation of end-to-end functionality via Docker remains necessary before true production shipment.

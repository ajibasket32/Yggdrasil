# RELEASE_CHECKLIST.md
# YGGDRASIL CHRONICLES
# Documentation Release Quality Checklist
Version: 2.1
Status: Normative
Last reviewed: 2026-06-13

---

## 1. PURPOSE AND AUTHORITY

This file is the only objective standard for deciding whether the repository's
Markdown documentation is clean. It evaluates documentation completeness,
consistency, navigation, and evidence. It does not assert that the game
implementation is ready to ship.

An audit must not add requirements that are absent from this checklist.
Changing this checklist is a governed contract change, not an audit finding.

## 2. RESULT RULES

Every item receives exactly one result in `DOCUMENTATION_AUDIT.md`:

- `PASS`: the requirement is satisfied and the audit cites a file and section.
- `FAIL`: the requirement is applicable but unsatisfied; the audit states the
  affected file/section and the smallest required fix.
- `N/A`: the requirement does not apply; the audit gives a short reason.

Documentation is release-clean only when every applicable item is `PASS` and
every other item is `N/A`, with evidence. A software release can remain blocked
by implementation, test, security, legal, or operational evidence without
making the Markdown set unclean.

## 3. DOCUMENTATION INVENTORY

- **INV-01**: `DOCUMENTATION_AUDIT.md` lists every Markdown file in the
  repository and records that it was reviewed.
- **INV-02**: Root canonical contracts identify their version or review date,
  status, and authority or purpose.
- **INV-03**: Canonical and supplemental documentation locations are defined,
  and duplicate contracts are absent or explicitly marked non-canonical.

## 4. README AND NAVIGATION

- **NAV-01**: `README.md` states project identity, current phase, core
  engine/AI boundary, MVP summary, and release-status disclaimer.
- **NAV-02**: `README.md` links to every root canonical, planning, governance,
  operations, contribution, audit, ADR, and asset-catalog document.
- **NAV-03**: Documentation authority order and conflict resolution are
  defined and consistent between `README.md` and `AGENTS.md`.

## 5. PRODUCT SCOPE

- **SCOPE-01**: Product vision, target experience, audience, and success
  criteria are documented.
- **SCOPE-02**: MVP capabilities, limits, sequencing, and completion criteria
  are documented.
- **SCOPE-03**: Post-MVP scope is separated from MVP commitments.
- **SCOPE-04**: Product and MVP non-goals are explicit.
- **SCOPE-05**: Material planning assumptions are explicit and do not conflict
  with higher-authority contracts.

## 6. ARCHITECTURE AND PERSISTENCE

- **ARCH-01**: System layers, authority boundaries, deployment components, and
  prohibited dependencies are documented.
- **ARCH-02**: Request runtime flow, gameplay data flow, event flow, and
  narrative/RAG flow are documented.
- **ARCH-03**: Canonical persistence, world persistence, cache/vector roles,
  and permanent-state rules are documented.
- **ARCH-04**: Save contents, transactional behavior, recovery, migration,
  rollback, versioning, and compatibility obligations are documented.
- **ARCH-05**: Mutation idempotency, transactional outbox behavior,
  post-commit publication, and duplicate-delivery handling are documented.

## 7. AI PROVIDERS AND PROMPTS

- **AI-01**: Provider abstraction, adapter-only provider calls, supported
  providers, and deployment-configured model selection are documented.
- **AI-02**: Ordered fallback, timeout/degradation behavior, Ollama/offline
  behavior, and cached/template fallback are documented.
- **AI-03**: AI endpoint rate limits, budgets, and abuse/cost controls are
  documented.
- **AI-04**: Prompt ownership, required prompt sections, storage, versioning,
  and context-builder responsibility are documented.
- **AI-05**: AI isolation from gameplay authority and direct state writes is
  explicit in architecture, API, and contributor rules.
- **AI-06**: AI input boundaries, structured output validation, rejection
  conditions, and safe failure behavior are documented.

## 8. RAG AND MEMORY

- **RAG-01**: Memory candidate creation, canonical storage, embedding,
  indexing, deduplication, and deletion/rebuild behavior are documented.
- **RAG-02**: Retrieval sources, ranking, context limits, quest/world context,
  privacy filtering, caching, and provider-neutral packaging are documented.
- **RAG-03**: Progress, relationship, quest, and world-state updates remain
  engine-owned; memory and AI may observe or narrate but may not cause them.

## 9. API, DATA, AND COMPATIBILITY

- **CONTRACT-01**: API authority, authentication, envelopes, errors, rate
  limits, endpoint contracts, authorization, and event boundaries are
  documented.
- **CONTRACT-02**: Required entities, identifiers, relationships, indexes,
  audit records, and persistence ownership are documented.
- **CONTRACT-03**: Save schema fields and the complete logical save contents
  are documented.
- **CONTRACT-04**: API, schema, engine, prompt, event, and save versioning or
  compatibility rules are documented where applicable.

## 10. GAME SYSTEMS

- **GAME-01**: Combat flow, formulas, deterministic inputs/results, rewards,
  persistence, and AI exclusion are documented.
- **GAME-02**: Character, race, job/class, skill, and progression rules and
  authority are documented.
- **GAME-03**: Item, inventory, equipment, crafting/loot ownership, atomicity,
  and lore/stat separation are documented.
- **GAME-04**: NPC identity, schedules, dialogue, memory, knowledge,
  relationships, and AI boundaries are documented.
- **GAME-05**: Quest state, world simulation, story/lore canon, player
  consequence, and permanent world rules are documented.

## 11. SECURITY, PRIVACY, AND LEGAL

- **SEC-01**: Threat model, authentication, authorization, input handling,
  secrets, dependency security, and incident severity are documented.
- **SEC-02**: User-data classification, purpose, retention, access, export,
  correction, deletion, backup behavior, and breach response are documented.
- **SEC-03**: Third-party AI provider exposure, data minimization, retention,
  regional controls, logging, and training-use restrictions are documented.
- **SEC-04**: Asset source, local-use, license, attribution, catalog, and
  originality/IP rules are documented.
- **SEC-05**: Abuse risks include rate-limit abuse, prompt injection, cost
  abuse, replay, cross-player access, administrative misuse, and reporting.

## 12. GOVERNANCE AND REGISTERS

- **GOV-01**: Documentation ownership, authority, review cadence, change
  impact, approval, and exception control are documented.
- **GOV-02**: Material architecture decisions require ADRs with status,
  context, decision, alternatives, consequences, rollback, and affected
  contracts.
- **GOV-03**: The risk register defines scoring and gives each active risk an
  owner, impact, likelihood, mitigation, trigger/contingency, target, and
  status.
- **GOV-04**: The technical debt register gives each accepted debt an owner,
  severity/priority, impact/risk, mitigation, target, and exit criteria.

## 13. OPERATIONS AND RECOVERY

- **OPS-01**: Structured logging, metrics, traces, health states, dashboards,
  alerts, retention, ownership, and protected critical paths are documented.
- **OPS-02**: Expected failure modes, degraded behavior, incident handling,
  rollback, data-integrity response, and recovery objectives are documented.
- **OPS-03**: Backup, restore, Qdrant rebuild, deletion tombstones, account
  export, and recovery verification are documented.

## 14. ACCESSIBILITY AND UX

- **A11Y-01**: Accessibility target, readable alternatives, focus, contrast,
  motion, zoom, audio/text equivalents, and critical-journey tests are
  documented.
- **A11Y-02**: Keyboard operation is required; pointer and controller/gamepad
  expectations are stated when applicable, without removing an accessible
  keyboard path.

## 15. CLEANLINESS

- **CLEAN-01**: No unresolved work markers or filler remain. The audit must
  search case-insensitively for `TODO`, `TBD`, `FIXME`, `XXX`, `placeholder`,
  `lorem ipsum`, `coming soon`, `later`, `to be defined`, and
  `to be decided`. Policy references, non-secret configuration examples, and
  ordinary temporal prose are not failures when the audit explicitly
  classifies them.
- **CLEAN-02**: All relative Markdown links and README navigation targets
  resolve to files or directories in the repository.
- **CLEAN-03**: No unresolved contradiction exists across authority,
  terminology, numeric targets, state machines, provider boundaries, save
  rules, or release status. Intentional differences are scoped and explained.
- **CLEAN-04**: No document claims that the implemented product is
  production-ready or release-ready while implementation blockers remain.
  Conditional standards and clearly labeled future targets are allowed.

## 16. AUDIT EVIDENCE

- **EVID-01**: `DOCUMENTATION_AUDIT.md` records audit date, scope, auditor,
  repository location, method, and source-revision availability.
- **EVID-02**: Every checklist item has `PASS`, `FAIL`, or `N/A`, with evidence,
  affected file/section, and either the minimal fix or N/A reason.
- **EVID-03**: The audit contains an executive summary, audit rules, checklist
  results, files reviewed, changes made, remaining failures, optional
  non-blocking improvements, counts, and final decision.

## 17. STOP CONDITION

- **STOP-01**: If all applicable checklist items are PASS or N/A with evidence,
  no more documentation changes are required. Optional improvements are not
  release blockers.

When `STOP-01` is satisfied, a documentation audit must stop. It must not
rewrite stable content for tone, wording, style, additional detail, or a newly
invented standard.

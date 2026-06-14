# RISK_REGISTER.md
# YGGDRASIL CHRONICLES
# Enterprise Risk Register
Version: 2.0 -- Enterprise Edition
Status: Planning
Last reviewed: 2026-06-13

---

## 1. POLICY

Risks describe uncertain events; technical debt describes known compromises. A risk may create debt, but the records must not be conflated.

Every active risk requires an owner, likelihood, impact, mitigation, trigger, contingency, target date or release, and status.

Scales:

- Likelihood: 1 (rare) to 5 (almost certain)
- Impact: 1 (minor) to 5 (critical)
- Score: likelihood multiplied by impact
- Score 15-25 is release-significant and requires explicit review

---

## 2. ACTIVE RISKS

| ID | Risk | L | I | Score | Owner | Mitigation | Trigger / Contingency | Target | Status |
|---|---|---:|---:|---:|---|---|---|---|---|
| R-001 | Save migration corrupts or loses progress | 3 | 5 | 15 | Engineering Lead | Versioned snapshots, migration fixtures, compatibility suite | Any mismatch blocks release; restore backup and roll back | Before first RC | Open |
| R-002 | AI output crosses gameplay authority boundary | 3 | 5 | 15 | AI/System Owner | Typed narrative schemas, output validation, isolation tests | Disable AI path and serve approved templates | Before AI release | Open |
| R-003 | Originality/IP review fails due to source inspiration | 3 | 5 | 15 | Product Owner | Original names, story, assets, and legal review | Remove or replace disputed content before distribution | Before public demo | Open |
| R-004 | Account or provider secret exposure | 3 | 5 | 15 | Security Owner | Secret manager, scanning, short-lived credentials | Rotate immediately, contain, investigate | Before production | Open |
| R-005 | PostgreSQL outage exceeds recovery objective | 3 | 5 | 15 | Operations Owner | PITR, monitored backups, restore drills | Fail closed for mutations; recover to approved point | Before production | Open |
| R-006 | Persistent memory growth breaches cost/performance limits | 4 | 4 | 16 | Data Owner | Retention tiers, indexes, archival, capacity tests | Degrade narrative retrieval safely; preserve canonical rows | Before scale test | Open |
| R-007 | Dependency or image supply-chain compromise | 3 | 5 | 15 | Security Owner | Lockfiles, SBOM, signed images, provenance, scans | Quarantine artifact and rebuild from trusted source | Before RC | Open |
| R-008 | World tick causes offline progress surprise or irreversible harm | 3 | 4 | 12 | Gameplay Owner | Explicit simulation policy, bounded catch-up, deterministic replay | Pause tick and restore last consistent checkpoint | Before world simulation | Open |
| R-009 | Accessibility gaps block keyboard or assistive-technology users | 4 | 3 | 12 | Frontend Owner | WCAG review, keyboard and contrast tests | Block affected UI from release or provide accessible path | Before public release | Open |
| R-010 | Operational alerting misses player-state corruption | 2 | 5 | 10 | Operations Owner | Integrity metrics, canaries, reconciliation jobs | Freeze writes, preserve evidence, restore safely | Before production | Open |

---

## 3. REVIEW

Review this register:

- monthly during active development;
- at release planning and release candidate approval;
- after every P0/P1 incident;
- when a material architecture, provider, or legal dependency changes.

Closed risks remain in the file with closure evidence and date.

---

## 4. FINAL RULE

An unowned release-significant risk is a release blocker.

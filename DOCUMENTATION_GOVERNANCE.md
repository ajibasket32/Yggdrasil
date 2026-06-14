# DOCUMENTATION_GOVERNANCE.md
# YGGDRASIL CHRONICLES
# Documentation Governance and Change Control
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. PURPOSE

This document defines ownership, review, approval, evidence, and change-control rules for project documentation. It does not override the authority order in `AGENTS.md`.

Documentation is part of the product. A behavior, schema, endpoint, security control, operational procedure, or release gate is incomplete when its canonical document is stale.

---

## 2. DOCUMENT CLASSES

| Class | Examples | Required Approval |
|---|---|---|
| Architectural law | `AGENTS.md`, `ARCHITECTURE.md` | Engineering Lead |
| Implementation contract | schema, API, coding, security, testing | Owning Lead plus affected reviewers |
| System design | combat, jobs, RAG | Gameplay or System Owner |
| Operations and release | observability, runbook, SLO, checklist | Operations and Security Owners |
| Planning | roadmap, tasks, technical debt, risk register | Product and Engineering Leads |
| Lore and vision | world bible, product vision | Product or Narrative Owner |

The role names are approval functions. One person may hold multiple roles in a small team, but each approval responsibility must still be recorded separately.

---

## 3. REQUIRED DOCUMENT METADATA

Canonical documents must state:

- document title
- project name
- version
- status: `Normative`, `Operational`, `Planning`, or `Informational`
- last-reviewed date in `YYYY-MM-DD`

Metadata may be added incrementally to legacy documents, but every release candidate must verify that all canonical documents were reviewed during the release window.

---

## 4. CHANGE IMPACT MATRIX

| Change Type | Documents That Must Be Reviewed |
|---|---|
| Gameplay rule or formula | `AGENTS.md`, `ARCHITECTURE.md`, relevant system design, tests, save compatibility |
| API contract | `API_SPEC.md`, security, tests, changelog |
| Database or persisted state | `DATABASE_SCHEMA.md`, save contract, migration/rollback plan, tests, runbook |
| AI or RAG behavior | `AGENTS.md`, architecture, RAG design, security, tests |
| Deployment or dependency | architecture, runbook, observability, security, release checklist |
| Personal-data handling | `DATA_GOVERNANCE.md`, security, API, runbook |
| SLO or alert threshold | `SERVICE_LEVEL_OBJECTIVES.md`, observability, runbook |
| Release scope | roadmap, tasks, risk register, changelog, release checklist |

Pull requests must name every reviewed document, including documents reviewed with no change required.

---

## 5. DECISION RECORDS

Architecture decisions that are expensive to reverse require an Architecture Decision Record under `docs/adr/`.

Each ADR must include:

- status: proposed, accepted, superseded, or rejected
- context and constraints
- decision
- alternatives considered
- consequences and risks
- migration and rollback implications
- affected canonical documents

An ADR explains a decision; it cannot silently override a canonical contract.

---

## 6. RELEASE EVIDENCE

Every release candidate must have an immutable evidence directory or CI artifact containing:

- release version and source revision
- build artifact digests
- test and coverage reports
- migration dry-run and rollback results
- security, dependency, secret, container, and license scan reports
- SBOM and provenance/attestation
- performance and SLO verification
- backup, restore, and rollback drill records
- save compatibility results
- approvals and accepted exceptions

Release evidence claims without linked evidence do not count as complete.

---

## 7. EXCEPTIONS

Exceptions require:

- a unique exception ID
- affected requirement
- business justification
- risk and player impact
- compensating control
- owner
- expiry date
- approval from the requirement owner

No exception may permit save corruption, silent world reset, direct AI gameplay influence, leaked secrets, or authorization bypass.

---

## 8. REVIEW CADENCE

| Document Class | Minimum Review |
|---|---|
| Architecture and implementation contracts | Every material change and every release |
| Security, data governance, risk, operations, SLO | Quarterly and every release |
| System design | Every affected feature release |
| Planning documents | At least monthly during active development |
| Lore and vision | Every content release that changes canon |

Stale review dates are release warnings. Stale documents that govern changed behavior are release blockers.

---

## 9. FINAL RULE

Documentation is trustworthy only when ownership, evidence, and implemented behavior agree.

# CONTRIBUTING.md
# YGGDRASIL CHRONICLES
# Contributor Guide
Version: 2.0 -- Enterprise Edition
Status: Operational
Last reviewed: 2026-06-13

---

## 1. BEFORE YOU START

Read these documents before making changes:

1. `AGENTS.md`
2. `ARCHITECTURE.md`
3. `CODING_STANDARDS.md`
4. The relevant system design document
5. `DOCUMENTATION_GOVERNANCE.md` for contract and evidence requirements

Contributors and AI assistants must follow the same rules.

---

## 2. DEVELOPMENT PRINCIPLES

- Build the JRPG first.
- Keep gameplay deterministic.
- Keep AI narrative-only.
- Keep database writes behind repositories.
- Keep API routers thin.
- Keep tests close to the risk.
- Document any accepted debt in `TECH_DEBT.md`.

---

## 3. BRANCHES AND COMMITS

Use Conventional Commits:

```text
feat(combat): add deterministic initiative order
fix(save): rollback failed snapshot writes
docs(api): clarify quest reward contract
security(auth): rotate refresh token on login
```

Branch examples:

```text
feature/save-system
fix/combat-determinism
docs/release-checklist
test/quest-state-machine
```

---

## 4. CHANGE REQUIREMENTS

Every gameplay feature must include:

- implementation
- unit tests
- integration tests
- regression tests when fixing a bug
- documentation updates
- save/load compatibility review

Every API change must update `API_SPEC.md`.

Every schema change must update `DATABASE_SCHEMA.md` and include an Alembic migration.

Every architecture exception must be recorded in `TECH_DEBT.md`.

Material architecture decisions require an ADR under `docs/adr/`. Security, privacy, reliability, or release exceptions require a time-bounded exception record and may not waive non-exemptible release laws.

---

## 5. AI-GENERATED CODE

AI-generated code is acceptable only when it follows all project rules.

Reject generated code if it:

- places gameplay authority in AI
- calls AI providers outside adapters
- puts business logic in controllers
- queries the database from engines
- hardcodes secrets
- skips tests for core behavior

---

## 6. REVIEW CHECKLIST

Reviewers must check:

- architecture boundaries
- deterministic gameplay outcomes
- persistence and rollback behavior
- security and authorization
- test coverage
- observability
- documentation updates
- technical debt entries
- affected documentation and ADRs
- privacy/data lifecycle impact
- SLO, rollback, and operational evidence
- accessibility impact for user-facing changes

---

## 7. FINAL CONTRIBUTOR RULE

Do not optimize for the fastest demo. Optimize for a playable game that can survive release.

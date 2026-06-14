# DATA_GOVERNANCE.md
# YGGDRASIL CHRONICLES
# Data Classification, Privacy, Retention, and Lifecycle
Version: 2.0 -- Enterprise Edition
Status: Normative
Last reviewed: 2026-06-13

---

## 1. PURPOSE

This document defines how project data is classified, collected, used, retained, exported, deleted, backed up, and disclosed. It applies to production, staging, support tooling, analytics, logs, AI context, and backups.

---

## 2. DATA PRINCIPLES

- Collect only data required for gameplay, security, operations, or explicit product functionality.
- Use data only for documented purposes.
- Protect canonical player progress from accidental deletion or partial mutation.
- Keep personal data out of AI prompts unless it is necessary, disclosed, and minimized.
- Never use production player data to train a model without explicit legal approval and player consent.
- Production data must not be copied into development environments without approved sanitization.

---

## 3. CLASSIFICATION

| Class | Examples | Handling |
|---|---|---|
| Public | published lore, public patch notes | May be publicly distributed |
| Internal | architecture, metrics aggregates, non-secret configuration | Staff/service access only |
| Confidential | email, IP address, support records, private dialogue | Encryption and least privilege |
| Restricted | password hashes, tokens, provider keys, security evidence | Dedicated secret/control plane; never logged |
| Canonical gameplay | saves, world state, inventory, progression, relationships | Transactional integrity, backup, auditability |

Canonical gameplay data is not automatically personal data, but records linked to a player account must receive confidential-data controls.

---

## 4. DATA INVENTORY AND OWNERSHIP

Before production release, every stored field and event stream must appear in a data inventory containing:

- system and table/collection
- data class
- purpose and lawful/approved basis
- owner
- source
- consumers and subprocessors
- retention period
- deletion method
- backup behavior
- encryption requirements

Uninventoried production data collection is prohibited.

---

## 5. RETENTION

| Data | Default Retention |
|---|---|
| Active account and canonical saves | Account lifetime |
| Deleted account identity mapping | Up to 30 days for recovery, then purge or irreversible anonymization |
| Security audit logs | 1 year minimum, subject to legal requirements |
| Application logs | 30 days |
| Metrics | 90 days |
| Traces | 14 days |
| Raw dialogue history | 90 days unless required as an active game memory |
| Permanent in-world memories | Account/world lifetime; minimize personal text |
| Backups | Per backup policy, with expired backups destroyed |
| Release and incident evidence | 1 year minimum; incident reports permanent |

Retention settings must be configurable where regulation or deployment region requires a shorter or longer period.

---

## 6. PLAYER RIGHTS AND REQUESTS

The production system must support authenticated workflows for:

- account data export in a machine-readable format
- account deletion
- correction of account profile data
- disclosure of applicable data uses and subprocessors

Account deletion is not the same as deleting a save slot. Deletion must:

1. re-authenticate the requester;
2. create an auditable deletion request;
3. revoke sessions;
4. remove or irreversibly anonymize personal identifiers;
5. preserve only legally required security records;
6. remove derived cache and vector data;
7. expire from backups according to the documented backup lifecycle.

World-history records may be retained only after unlinking them irreversibly from personal identity where product continuity requires it.

---

## 7. AI AND RAG DATA USE

- Context builders must use allowlists, not broad record dumps.
- Secrets, tokens, email addresses, network identifiers, and unrelated player data must never enter prompts.
- Provider requests must follow configured regional and retention controls.
- Providers must not receive training rights to player data by default.
- Prompt and response logging is disabled by default; approved samples must be redacted.
- Deleting a memory must delete or tombstone its Qdrant vectors and invalidate caches.

---

## 8. ENCRYPTION AND ACCESS

- TLS is mandatory in transit outside an isolated local environment.
- Confidential, restricted, backup, and canonical gameplay data must be encrypted at rest.
- Access follows least privilege and is reviewed quarterly.
- Production access uses named identities, MFA, short-lived credentials, and audit logs.
- Shared production accounts are prohibited.

---

## 9. BACKUP AND DELETION

Backups are immutable recovery artifacts, not alternate production databases. Deletion requests do not require rewriting every historical backup immediately, but deleted data must not be restored into active service without reapplying deletion tombstones.

Restore procedures must verify:

- tombstones are replayed;
- expired data does not reappear;
- Qdrant and Redis are rebuilt or invalidated consistently;
- player progress remains internally consistent.

---

## 10. BREACH RESPONSE

Suspected unauthorized access to confidential or restricted data is at least a P1 incident. Response follows `SECURITY_GUIDELINES.md` and `OPERATIONS_RUNBOOK.md`, including scope assessment, credential rotation, evidence preservation, notification review, and post-incident regression controls.

---

## 11. RELEASE GATES

Production release is blocked until:

- the data inventory is complete;
- retention jobs are tested;
- export and deletion workflows pass integration tests;
- subprocessors and AI provider data settings are reviewed;
- restore testing proves deleted data is not silently resurrected;
- privacy notice and terms match actual behavior.

---

## 12. FINAL RULE

Persistent worlds require durable state, not permanent retention of unnecessary personal data.

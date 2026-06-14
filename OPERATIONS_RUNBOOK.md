# OPERATIONS_RUNBOOK.md
# YGGDRASIL CHRONICLES
# Operations, Backup, Restore, and Incident Runbook
Version: 2.0 -- Enterprise Edition
Status: Operational
Last reviewed: 2026-06-13

---

## 1. PURPOSE

This runbook defines how to operate, recover, and release Yggdrasil Chronicles without risking player progress or world persistence.

---

## 2. ENVIRONMENTS

| Environment | Purpose | Data |
|---|---|---|
| `local` | developer work | synthetic |
| `test` | CI validation | disposable |
| `staging` | release verification | sanitized production-like |
| `production` | live game | real player data |

Production data must never be copied to local machines without sanitization.

---

## 3. STARTUP

The full stack must start with:

```bash
docker compose up --build
```

Required services:

- frontend
- backend
- postgres
- redis
- qdrant
- ollama
- worker
- nginx

Startup is not successful until `/health` returns `healthy` or `degraded` with gameplay still playable.

---

## 4. SHUTDOWN

Before planned shutdown:

1. Stop accepting new mutating requests.
2. Let active save transactions finish.
3. Pause world tick workers.
4. Flush background queues or mark tasks resumable.
5. Confirm PostgreSQL backup status.
6. Stop services.

No shutdown process may leave a partially written save.

---

## 5. BACKUP POLICY

PostgreSQL is the source of truth for canonical game state. Qdrant indexes are rebuildable from PostgreSQL memory records.

Minimum backup schedule:

- PostgreSQL full backup: daily
- PostgreSQL point-in-time recovery: enabled
- Redis: no canonical gameplay data; snapshot only for operational convenience
- Qdrant: daily snapshot plus rebuild procedure
- Asset catalog and release artifacts: versioned with release

Backups must be encrypted at rest and access-controlled.

Recovery objectives are defined in `SERVICE_LEVEL_OBJECTIVES.md`. PostgreSQL PITR configuration must demonstrate an RPO of 5 minutes or better and an RTO of 60 minutes or better before production release.

Backup jobs must:

- verify checksums;
- write to a separate failure domain;
- use immutable or object-locked retention for protected generations;
- alert on missed or unverified runs;
- record restore-compatible application and schema versions.

---

## 6. RESTORE POLICY

Restore drills must run before every major release.

Restore validation requires:

- database schema migrates successfully
- latest save can load
- world state matches backup timestamp
- memory records exist in PostgreSQL
- Qdrant can be restored or rebuilt
- health checks pass

---

## 7. QDRANT REBUILD

If Qdrant is corrupted or unavailable:

1. Keep gameplay online if PostgreSQL is healthy.
2. Disable AI narrative generation or use cached templates.
3. Recreate Qdrant collections.
4. Re-embed memories from PostgreSQL.
5. Verify memory retrieval latency and relevance.
6. Re-enable AI narrative endpoints.

Qdrant failure must not corrupt canonical world state.

The v0.4 worker recreates all configured collections, creates durable
`memory_index_jobs` for active PostgreSQL memories, and dispatches only job
UUIDs through Celery/Redis. Failed jobs remain `RETRY` or `FAILED` with a safe
error code. Operators must resolve the dependency failure and re-run recovery;
they must not edit canonical memory rows to repair Qdrant.

---

## 8. RELEASE PROCEDURE

1. Freeze release branch.
2. Build the artifact once and record its digest, SBOM, signature, and provenance.
3. Run full CI and security/license scans against that artifact and source revision.
4. Run database migration and rollback dry runs on production-like data.
5. Run backup, restore, deletion-tombstone, and save-compatibility drills.
6. Deploy the same artifact to staging.
7. Execute `RELEASE_CHECKLIST.md` and collect approvals.
8. Tag the approved source revision and evidence record.
9. Deploy progressively to production using canary or bounded traffic.
10. Halt automatically on save integrity, auth, determinism, migration, or SLO threshold failures.
11. Monitor dashboards for at least 60 minutes and until the defined bake period ends.
12. Record go/no-go outcome and close or roll back the release.

---

## 9. ROLLBACK PROCEDURE

Rollback is required if:

- save/load corruption is detected
- database migration fails
- combat determinism failure occurs
- authentication or authorization is compromised
- API error rate exceeds release threshold

Rollback steps:

1. Stop traffic to the new version.
2. Restore previous application image.
3. If migration is backward compatible, keep database.
4. If migration is not backward compatible, restore from pre-release backup.
5. Rebuild Qdrant if needed.
6. Run smoke tests.
7. Publish incident note.

Application rollback must not blindly downgrade a database. The migration plan must classify each change as backward compatible, expand/contract, or irreversible. Irreversible migrations require a tested forward-fix and restore plan before approval.

Backward-incompatible migrations require explicit release approval.

---

## 10. INCIDENT RESPONSE

Incident priorities follow `SECURITY_GUIDELINES.md`.

Every incident must produce:

- timeline
- affected systems
- affected player data, if any
- root cause
- mitigation
- regression test
- documentation update

### Incident Command

P0 and P1 incidents require:

- a named incident commander;
- an operations lead and communications owner;
- a timestamped incident channel/log;
- preservation of audit evidence;
- explicit write-freeze authority when player state may be at risk;
- internal updates at least every 30 minutes for P0 and every 60 minutes for P1.

### Player-State Integrity Response

When corruption is suspected:

1. Stop affected writes without destroying evidence.
2. Preserve database, queue, log, and artifact snapshots.
3. Identify the last verified consistent point.
4. Reconcile affected saves and world events.
5. Restore or repair only through reviewed, repeatable tooling.
6. Notify affected players according to security/privacy requirements.

---

## 11. ACCESS CONTROL AND ROUTINE OPERATIONS

- Production access requires named accounts, MFA, least privilege, and audit logging.
- Break-glass access is time-limited, alerts Security, and requires after-action review.
- Access is reviewed quarterly and on role departure.
- Credentials and signing keys rotate on schedule and immediately after suspected exposure.
- Capacity, backup, restore, retention, certificate, and dependency status are reviewed monthly.

---

## 12. FINAL RULE

The world is persistent. Operations must protect continuity before convenience.

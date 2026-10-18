# AGRIFY — Backup, Restore & Rollback Operations Guide

**Scope:** Staging PostgreSQL database (`agrify-db-staging`) and the AGRIFY backend application.  
**Status:** Operational documentation only. No production backup or restore has been performed or verified as part of this task.

---

## 1. Safety rules (read first)

- **Never run `pg_dump`, `pg_restore`, `psql`, or Alembic against the production database** during this task or without explicit authorization.
- **Never print, log, or commit connection strings, passwords, or secret values.** Use environment-variable references (e.g. `${DATABASE_URL}`) only.
- **Do not claim a restore was tested** unless a disposable test database was actually available and the restore was executed against it. This document does not claim that.
- Backups contain potentially sensitive farm data. Treat backup files as confidential: restrict filesystem permissions, encrypt at rest, and delete temporary restore databases after verification.

---

## 2. Backing up PostgreSQL with pg_dump

Create a logical backup of the staging database. Run from a machine with network access to the database and `postgresql-client` installed. The connection string must come from the environment, never hard-coded.

```bash
# Example only — values come from the environment; do not hard-code.
BACKUP_FILE="agrify-db-staging-$(date +%Y%m%d%H%M%S).sql"
pg_dump "${DATABASE_URL}" > "${BACKUP_FILE}"
gzip "${BACKUP_FILE}"
```

Recommended options for a production-grade dump:

```bash
pg_dump "${DATABASE_URL}" \
  --no-owner \
  --no-privileges \
  --verbose \
  --file="${BACKUP_FILE}"
```

- `--no-owner` / `--no-privileges` make the dump easier to restore into a differently-named test database.
- Verify the dump is non-empty and ends with a `COPY`/`CREATE TABLE` completion marker before trusting it:
  ```bash
  gunzip -t "${BACKUP_FILE}.gz"          # integrity check
  tail -n 20 "${BACKUP_FILE}"            # confirm clean termination
  ```

Store the compressed backup with restricted permissions:

```bash
chmod 600 "${BACKUP_FILE}.gz"
```

---

## 3. Restoring into a disposable test database (never production)

To verify a backup without touching production, restore it into a throwaway database on a non-production instance (or a separate schema/role on staging with explicit approval).

```bash
# 1. Create a disposable database (example; adapter names vary by provider)
createdb -h "${TEST_DB_HOST}" -U "${TEST_DB_USER}" agrify_restore_verify_$(date +%s)

# 2. Restore the dump into it
pg_restore --no-owner --no-privileges -d "postgresql://${TEST_DB_USER}:${TEST_DB_PASS}@${TEST_DB_HOST}/${TEST_DB_NAME}" "${BACKUP_FILE}"

# 3. Run verification checks against the disposable DB only
#    (row counts, Alembic version, key tables present)

# 4. Tear down the disposable database when done
dropdb -h "${TEST_DB_HOST}" -U "${TEST_DB_USER}" "${TEST_DB_NAME}"
```

Never restore into `agrify-db-staging` or the production database from this procedure unless a formal incident-recovery process authorizes it.

---

## 4. Verifying a restore before relying on it

After restoring into the disposable database, run these checks:

1. **Alembic version matches head:**
   ```bash
   alembic -c backend/alembic.ini current
   # expected: 0002_ownership_action_plans (head)
   ```
2. **Core tables exist and are non-empty (or expected-empty):**
   ```sql
   SELECT to_regclass('farm_profiles') IS NOT NULL AS farm_profiles_exists;
   SELECT count(*) FROM farm_profiles;
   ```
3. **Foreign-key integrity:**
   ```sql
   -- Example: every action plan references a real farm
   SELECT count(*) FROM farm_action_plans fap
   LEFT JOIN farm_profiles fp ON fp.id = fap.farm_id
   WHERE fp.id IS NULL;
   -- expected: 0
   ```
4. **Application smoke test:** Point a disposable backend instance at the restored DB (stateless mode or the test DB) and call `GET /api/health`; confirm `database: connected` (or configured mode) and `version: 3.0-production`.

Only after all checks pass should the backup be considered trustworthy.

---

## 5. Alembic migration review and safe upgrade order

Migrations live in `backend/migrations/`:
- `0001_initial_10_models.py` — baseline (10 core tables).
- `0002_farm_ownership_and_action_plans.py` — adds `owner_token_hash` to `farm_profiles` and creates `farm_action_plans`. Revision id `0002_ownership_action_plans`, shortened to 27 chars to satisfy PostgreSQL `alembic_version.version_num` VARCHAR(32).

Safe upgrade procedure:

1. Review the migration SQL offline before applying:
   ```bash
   alembic -c backend/alembic.ini upgrade head --sql
   ```
2. Back up the database first (Section 2).
3. Apply in strict order — never skip a revision:
   ```bash
   alembic -c backend/alembic.ini upgrade head
   ```
4. Confirm the applied revision:
   ```bash
   alembic -c backend/alembic.ini current
   ```
5. Rollback is supported per migration (`downgrade` is implemented for both revisions), but downgrading destroys data added after the target revision. Only downgrade as part of a documented rollback with a fresh backup.

This repository has verified `upgrade head → downgrade base → upgrade head` against a local SQLite database; production PostgreSQL behavior must be confirmed in a staging restore before applying to production.

---

## 6. Application rollback (known-good deployment/commit)

Rollback of the application code is separate from database rollback.

### 6.1 Revert application code to a known-good commit

```bash
# On staging branch only. Do not merge into main.
git checkout staging
git pull --ff-only origin staging
git revert <bad-commit-sha>        # or reset to a known-good tag/commit, then force is NOT permitted on published branches
```

Published branches must never be reset or force-pushed. If a bad commit is already on `origin/staging`, revert it with a new commit rather than rewriting history.

### 6.2 Roll back the rendering/deployment

- Render blueprint deploys are tied to the branch commit. Redeploying the staging service from the reverted commit rolls the application forward to that commit.
- Keep the previous stable image/tag available until the rollback is confirmed.

### 6.3 Database rollback limitations

- **Reverting application code does NOT roll back the database.** If a bad migration or data-writing deployment ran, reverting code leaves the schema/data as they were after the bad deployment.
- To truly roll back database state, you must restore from a pre-incident backup (Section 3) into the target database — this is disruptive and causes data loss for changes made after the backup.
- Alembic `downgrade` can reverse schema changes but cannot recover data deleted or corrupted after the target revision.
- Therefore: **prefer backup restoration for database incidents; prefer code revert for application-logic incidents.** Coordinate both when an incident spans both layers.

---

## 7. Recovery checks

After any restore or rollback, confirm:

- `GET /api/health` returns `status: healthy`, `version: 3.0-production`, and the expected database mode.
- Alembic `current` reports the intended revision.
- A sample tenant can read its own farm profile and cannot read another tenant's (multi-tenant isolation preserved).
- Rate limiting, CORS, and the 413/429 handlers behave as configured.
- No secrets or connection strings appear in logs or response bodies.

---

## 8. Responsible access to backup files

- Store backups off the application host where possible, with encrypted-at-rest and restricted IAM/filesystem access.
- Rotate backups per a retention policy (e.g. daily for 7 days, weekly for 4 weeks).
- Log backup/restore events (who, when, which database) without logging credentials.
- Delete disposable test databases and temporary dump files immediately after verification.

# Nautilus Builder Deployment Guide

## Environment Profiles

### Local
```bash
BUILDER_ENV=local
BUILDER_DEV_AUTH_TOKEN=dev-token
```
- In-memory repositories allowed
- Local artifact store allowed
- Dev tokens allowed
- Localhost CORS allowed
- In-memory rate limiter (default)

### Staging
```bash
BUILDER_ENV=staging
BUILDER_API_TOKEN=<32+ char secret>
BUILDER_DATABASE_URL=postgresql://...
BUILDER_CORS_ORIGINS=https://staging.builder.example.com
BUILDER_RATE_LIMIT_BACKEND=redis
BUILDER_REDIS_URL=redis://redis:6379/0
```
- PostgreSQL required
- Object storage required
- Strong token required
- Wildcard CORS forbidden
- Redis rate limiting recommended

### Production
```bash
BUILDER_ENV=production
BUILDER_API_TOKEN=<32+ char secret>
BUILDER_DATABASE_URL=postgresql://...
BUILDER_CORS_ORIGINS=https://builder.example.com
BUILDER_RATE_LIMIT_BACKEND=redis
BUILDER_REDIS_URL=redis://redis:6379/0
GIT_COMMIT_SHA=<sha>
BUILD_TIME=<utc timestamp>
```
- PostgreSQL required
- Object storage required
- Secret manager recommended
- NEXT_PUBLIC_BUILDER_API_TOKEN forbidden
- Redis rate limiting required
- Audit middleware writes to Postgres

## Required Environment Variables

| Variable | Required In | Description |
|----------|-------------|-------------|
| `BUILDER_ENV` | All | `local`, `staging`, or `production` |
| `BUILDER_API_TOKEN` | staging, production | Strong API token (≥32 chars) |
| `BUILDER_DATABASE_URL` | staging, production | PostgreSQL connection string |
| `BUILDER_CORS_ORIGINS` | staging, production | Comma-separated allowed origins |
| `GIT_COMMIT_SHA` | production | Deployed commit SHA |
| `BUILD_TIME` | production | Build timestamp (UTC) |

## Forbidden Production Defaults

The following patterns are **rejected at startup** in staging/production:

| Pattern | Reason |
|---------|--------|
| `BUILDER_API_TOKEN=dev-token` | Known weak token |
| `BUILDER_API_TOKEN=test-token` | Known weak token |
| `BUILDER_API_TOKEN=changeme` | Known weak token |
| `BUILDER_API_TOKEN` < 32 chars | Insufficient entropy |
| `NEXT_PUBLIC_BUILDER_API_TOKEN` set | Browser must not hold raw API token |
| `BUILDER_CORS_ORIGINS=*` | Wildcard CORS forbidden |
| `BUILDER_CORS_ORIGINS` empty | Origins must be explicit |

## Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BUILDER_RATE_LIMIT_BACKEND` | `memory` | `memory` or `redis` |
| `BUILDER_REDIS_URL` | — | Redis URL (required if backend=redis) |
| `BUILDER_RATE_LIMIT` | `100` | Requests per minute per IP |
| `BUILDER_ARTIFACT_BACKEND` | `local` | `local` or `s3` |
| `BUILDER_S3_ENDPOINT_URL` | — | S3/MinIO endpoint |
| `BUILDER_S3_BUCKET` | — | S3 bucket name |
| `BUILDER_S3_REGION` | — | S3 region |
| `BUILDER_S3_ACCESS_KEY_ID` | — | S3 access key |
| `BUILDER_S3_SECRET_ACCESS_KEY` | — | S3 secret key |
| `BUILDER_DEV_AUTH_TOKEN` | local only | Dev token for local development |
| `BUILDER_SEED_DEMO_STRATEGIES` | `0` | Seed demo strategies (1/0) |

## PostgreSQL Setup

### Local (Docker)

```bash
docker compose up -d db
```

### Manual

```bash
# Create database and user
psql -U postgres -c "CREATE USER builder WITH PASSWORD 'CHANGE_ME';"
psql -U postgres -c "CREATE DATABASE nautilus_builder OWNER builder;"

# Verify connection
psql postgresql://builder:CHANGE_ME@localhost:5432/nautilus_builder -c "SELECT 1;"
```

Migrations run automatically on API startup. To run manually:

```bash
# Check current version
psql $BUILDER_DATABASE_URL -c "SELECT * FROM builder.schema_migrations ORDER BY version;"

# Rollback last migration
# Use the builder CLI or fastapi_app startup
```

## S3/MinIO Artifact Storage

### MinIO (Local/Staging)

```bash
# Start MinIO
docker compose up -d minio

# Create bucket
mc alias set local http://localhost:9000 minioadmin minioadmin
mc mb local/nautilus-builder-artifacts
```

### S3 (Production)

```bash
# Set environment variables
export BUILDER_ARTIFACT_BACKEND=s3
export BUILDER_S3_BUCKET=nautilus-builder-artifacts
export BUILDER_S3_REGION=us-east-1
export BUILDER_S3_ACCESS_KEY_ID=AKIA...
export BUILDER_S3_SECRET_ACCESS_KEY=...
```

Artifacts are stored with content-addressed keys:
```
artifacts/{artifact_type}/{sha256}/{filename}
```

## Health Endpoints

| Endpoint | Purpose | Returns |
|----------|---------|---------|
| `GET /health` | Legacy health check | `{"status": "ok", "service": "nautilus_builder_api"}` |
| `GET /health/live` | Liveness (process alive) | `{"status": "alive"}` |
| `GET /health/ready` | Readiness (DB, storage, migrations) | `{"status": "ready", "checks": {...}}` |
| `GET /health/build` | Build info (version, commit SHA) | `{"version": "v0.5.0", "commit": "..."}` |

## Migration Commands

```bash
# Migrations run automatically on API startup.
# To check current state:
psql $BUILDER_DATABASE_URL -c "SELECT * FROM builder.schema_migrations ORDER BY version;"

# To rollback (use programmatic interface or psql):
# v3: audit_events.project_id column
# v2: compiler_runs, replay_runs, promotion_ledger, audit_events tables
# v1: initial schema (strategies, adapters, instruments)
```

## Backup and Restore

### PostgreSQL Backup

```bash
# Full backup (custom format, compressed)
pg_dump -Fc nautilus_builder > backup_$(date +%Y%m%d_%H%M%S).dump

# SQL dump (plain text)
pg_dump nautilus_builder > backup_$(date +%Y%m%d).sql
```

### PostgreSQL Restore

```bash
# From custom format
pg_restore -d nautilus_builder backup_20260607.dump

# From SQL dump
psql nautilus_builder < backup_20260607.sql
```

### Verification After Restore

```bash
# Check migration state
psql $BUILDER_DATABASE_URL -c "SELECT * FROM builder.schema_migrations ORDER BY version;"

# Check promotion ledger integrity
psql $BUILDER_DATABASE_URL -c "SELECT count(*) FROM builder.promotion_ledger;"

# Verify health
curl http://localhost:8000/health/ready
```

### Artifact Backup (S3)

```bash
# Sync artifacts to backup bucket
aws s3 sync s3://nautilus-builder-artifacts s3://nautilus-builder-artifacts-backup/$(date +%Y%m%d)/
```

## Release Checklist

- [ ] All CI checks passing (lint, test, build, hygiene)
- [ ] CHANGELOG.md updated with version entry
- [ ] `.env.production.example` reviewed for new variables
- [ ] Migration tested on staging (apply + rollback)
- [ ] Postgres backup taken before deployment
- [ ] Artifact storage backup verified
- [ ] Promotion ledger readable after deployment
- [ ] Health endpoints responding (`/health/live`, `/health/ready`, `/health/build`)
- [ ] Audit trail writing correctly (submit a test mutation, check `audit_events`)
- [ ] Rate limiting active (verify via response headers or logs)
- [ ] No forbidden production defaults in deployed config
- [ ] Docker image built and tagged with version + commit SHA

## Rollback Checklist

1. Stop API and worker processes
2. Confirm no running replay/backtest jobs
3. Deploy previous Docker image: `nautilus-builder:v<PREVIOUS>`
4. Run rollback if migration changed: `builder db rollback --steps 1`
5. Verify migration state: `SELECT * FROM builder.schema_migrations ORDER BY version;`
6. Verify health: `GET /health/ready`
7. Validate promotion ledger rows are readable
8. Check audit trail for rollback event

### Rollback v0.5.0 → v0.4.0

1. Stop API and worker processes
2. Deploy `nautilus-builder:v0.4.0`
3. Migration v3 can be left in place (additive column, backwards compatible)
4. Verify readiness: `GET /health/ready`

### Rollback v0.4.0 → v0.3.0

1. Follow same steps as above
2. Migration v2 tables (compiler_runs, replay_runs, promotion_ledger, audit_events) are backwards compatible
3. Verify health and ledger readability

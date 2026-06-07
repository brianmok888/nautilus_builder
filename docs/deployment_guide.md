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

### Staging
```bash
BUILDER_ENV=staging
BUILDER_API_TOKEN=<32+ char secret>
BUILDER_DATABASE_URL=postgresql://...
BUILDER_CORS_ORIGINS=https://staging.builder.example.com
```
- PostgreSQL required
- Object storage required
- Strong token required
- Wildcard CORS forbidden

### Production
```bash
BUILDER_ENV=production
BUILDER_API_TOKEN=<32+ char secret>
BUILDER_DATABASE_URL=postgresql://...
BUILDER_CORS_ORIGINS=https://builder.example.com
GIT_COMMIT_SHA=<sha>
BUILD_TIME=<utc timestamp>
```
- PostgreSQL required
- Object storage required
- Secret manager recommended
- NEXT_PUBLIC_BUILDER_API_TOKEN forbidden

## Health Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Legacy health check |
| `GET /health/live` | Liveness (process alive) |
| `GET /health/ready` | Readiness (DB, storage, migrations) |
| `GET /health/build` | Build info (version, commit SHA) |

## Rollback Guide

### Rollback v0.4.0 -> v0.3.0

1. Stop API and worker processes
2. Confirm no running replay jobs
3. Deploy previous Docker image: `nautilus-builder:v0.3.0`
4. Run `builder db current` to check migration state
5. If migration v2 was applied, run `builder db rollback --steps 1`
6. Verify readiness: `GET /health/ready`
7. Validate promotion ledger rows are readable

### Rollback v0.3.0 -> v0.2.0

1. Follow same steps as above
2. Migration v1 schema is compatible with v0.2.0 code

## Backup and Restore

### PostgreSQL Backup
```bash
pg_dump -Fc nautilus_builder > backup_$(date +%Y%m%d).dump
```

### PostgreSQL Restore
```bash
pg_restore -d nautilus_builder backup_20260607.dump
```

### Verification
```bash
# After restore, verify migration state
psql nautilus_builder -c "SELECT * FROM builder.schema_migrations ORDER BY version;"
```

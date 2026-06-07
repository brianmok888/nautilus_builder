# Nautilus Builder — Operations Guide

## Monitoring

### Health Endpoints

| Endpoint | Method | Purpose | Expected Response |
|----------|--------|---------|-------------------|
| `/health/live` | GET | Liveness probe | `200 {"status": "alive"}` |
| `/health/ready` | GET | Readiness (DB + storage) | `200 {"status": "ready", "checks": {...}}` |
| `/health/build` | GET | Build metadata | `200 {"version": "...", "commit": "..."}` |

Configure your orchestrator (Kubernetes, Docker, systemd) to hit:
- `/health/live` every 10-30s for liveness
- `/health/ready` every 30-60s for readiness (restart if unhealthy)

### Log Levels

| Level | Use |
|-------|-----|
| `ERROR` | Failures requiring immediate attention |
| `WARNING` | Degraded but operational (Redis unavailable, rate limit open-fallback) |
| `INFO` | Normal operations (startup, shutdown, promotion events) |
| `DEBUG` | Verbose request/response data (development only) |

### Key Metrics to Monitor

- `audit_events` write rate (should match mutation traffic)
- `promotion_ledger` entry rate
- Rate limit rejections (429 responses)
- Redis connectivity (if backend=redis)
- PostgreSQL connection pool health
- Artifact store write latency

## Incident Response

### API Unresponsive

1. Check liveness: `curl http://localhost:8000/health/live`
2. Check logs: `docker logs nautilus-builder-api --tail 100`
3. Check PostgreSQL: `psql $BUILDER_DATABASE_URL -c "SELECT 1;"`
4. Check Redis (if configured): `redis-cli -u $BUILDER_REDIS_URL ping`
5. Restart if needed: `docker compose restart api`

### Database Issues

1. Check connection: `psql $BUILDER_DATABASE_URL -c "SELECT 1;"`
2. Check migration state: `SELECT * FROM builder.schema_migrations ORDER BY version;`
3. Check table sizes: `SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname = 'builder';`
4. If migration failed partway: inspect `schema_migrations`, may need manual cleanup

### Rollback a Migration

```bash
# Check current version
psql $BUILDER_DATABASE_URL -c "SELECT * FROM builder.schema_migrations ORDER BY version;"

# If programmatic rollback is available:
# builder db rollback --steps 1

# Manual rollback (example: v3 down)
psql $BUILDER_DATABASE_URL -c "
ALTER TABLE builder.audit_events DROP COLUMN IF EXISTS project_id;
DELETE FROM builder.schema_migrations WHERE version = 3;
"
```

### Redis Unavailable

When `BUILDER_RATE_LIMIT_BACKEND=redis` and Redis is down:
- Rate limiter **fails open** (allows all requests, logs WARNING)
- Audit middleware continues writing to Postgres (not dependent on Redis)
- Monitor logs for `rate_limit_fallback_open` warnings

## Backup and Restore

### PostgreSQL

#### Automated Backup (cron)

```bash
# Add to crontab (daily at 02:00 UTC)
0 2 * * * pg_dump -Fc nautilus_builder | gzip > /backups/builder_$(date +\%Y\%m\%d).dump.gz
```

#### Manual Backup

```bash
pg_dump -Fc nautilus_builder > backup_$(date +%Y%m%d_%H%M%S).dump
```

#### Restore

```bash
# Drop and recreate (destructive!)
dropdb nautilus_builder
createdb nautilus_builder
pg_restore -d nautilus_builder backup_20260607.dump

# Non-destructive (restore to a verification copy)
createdb nautilus_builder_verify
pg_restore -d nautilus_builder_verify backup_20260607.dump
```

#### Verify Restore

```bash
psql nautilus_builder -c "SELECT count(*) FROM builder.promotion_ledger;"
psql nautilus_builder -c "SELECT count(*) FROM builder.audit_events;"
psql nautilus_builder -c "SELECT * FROM builder.schema_migrations ORDER BY version;"
```

### Artifact Storage (S3/MinIO)

```bash
# Sync artifacts to backup location
aws s3 sync s3://nautilus-builder-artifacts/ s3://backup-bucket/artifacts/$(date +%Y%m%d)/

# Restore from backup
aws s3 sync s3://backup-bucket/artifacts/20260607/ s3://nautilus-builder-artifacts/
```

## Environment Profiles

### Local Development

```bash
BUILDER_ENV=local
BUILDER_DEV_AUTH_TOKEN=dev-token
BUILDER_RATE_LIMIT_BACKEND=memory
```

Characteristics:
- In-memory stores (no Postgres required)
- Dev tokens accepted
- Local artifact store (JSON files)
- In-memory rate limiting
- CORS allows localhost

### Staging

```bash
BUILDER_ENV=staging
BUILDER_API_TOKEN=<32+ char secret>
BUILDER_DATABASE_URL=postgresql://...
BUILDER_RATE_LIMIT_BACKEND=redis
BUILDER_REDIS_URL=redis://redis:6379/0
BUILDER_CORS_ORIGINS=https://staging.builder.example.com
```

Characteristics:
- PostgreSQL required
- Redis for rate limiting recommended
- S3/MinIO for artifacts recommended
- Strong tokens required
- No wildcard CORS

### Production

```bash
BUILDER_ENV=production
BUILDER_API_TOKEN=<32+ char secret>
BUILDER_DATABASE_URL=postgresql://...
BUILDER_RATE_LIMIT_BACKEND=redis
BUILDER_REDIS_URL=redis://redis:6379/0
BUILDER_CORS_ORIGINS=https://builder.example.com
GIT_COMMIT_SHA=<sha>
BUILD_TIME=<timestamp>
BUILDER_ARTIFACT_BACKEND=s3
```

Characteristics:
- PostgreSQL required
- Redis for rate limiting required
- S3 for artifacts required
- Secret manager recommended
- NEXT_PUBLIC_BUILDER_API_TOKEN forbidden
- Audit middleware writes all mutations to Postgres

## Rate Limiting Architecture

```
Request → FastAPI → Rate Limiter Check → Route Handler → Response
                          ↓ (if limited)
                     429 Too Many Requests
```

### Backend Selection

Controlled by `BUILDER_RATE_LIMIT_BACKEND`:

| Backend | Config | Use Case |
|---------|--------|----------|
| `memory` (default) | No config needed | Local development |
| `redis` | `BUILDER_REDIS_URL` required | Staging, production |

### Redis Rate Limiter Behavior

- Sliding window counter per client IP
- Default: 100 requests/minute per IP (configurable via `BUILDER_RATE_LIMIT`)
- Uses Redis `INCR` + `EXPIRE` for atomic counting
- **Fails open**: if Redis is unreachable, requests are allowed and a WARNING is logged
- Does not block the request path on Redis latency

### In-Memory Rate Limiter

- Sliding window counter per client key
- Suitable for single-instance deployments only
- State is lost on process restart

## Audit Trail

### Audit Events Table

Every mutation (POST, PUT, DELETE, PATCH) generates an audit event in `builder.audit_events`:

| Column | Description |
|--------|-------------|
| `id` | UUID primary key |
| `request_id` | Correlation ID from `X-Request-ID` header |
| `actor_id` | Authenticated user ID |
| `project_id` | Project scope (v3+) |
| `action` | Mutation action (e.g., `strategy.create`) |
| `resource_type` | Type of resource affected |
| `resource_id` | ID of affected resource |
| `before_hash` | Hash of resource state before mutation |
| `after_hash` | Hash of resource state after mutation |
| `status` | `success` or `failed` |
| `error_code` | Error code if failed |
| `created_at` | Timestamp |

### Audit Queries

```sql
-- Recent mutations by actor
SELECT action, resource_type, resource_id, status, created_at
FROM builder.audit_events
WHERE actor_id = 'user-001'
ORDER BY created_at DESC
LIMIT 50;

-- Failed mutations
SELECT request_id, actor_id, action, error_code, created_at
FROM builder.audit_events
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 100;

-- Mutations on a specific resource
SELECT request_id, actor_id, action, before_hash, after_hash, created_at
FROM builder.audit_events
WHERE resource_type = 'strategy' AND resource_id = 'strat-001'
ORDER BY created_at DESC;

-- Audit trail for a promotion
SELECT *
FROM builder.audit_events
WHERE action LIKE '%promotion%' OR resource_type = 'promotion'
ORDER BY created_at DESC;

-- Project-scoped audit (v3+)
SELECT action, resource_type, resource_id, actor_id, created_at
FROM builder.audit_events
WHERE project_id = 'proj-001'
ORDER BY created_at DESC
LIMIT 100;

-- Rate of mutations over time
SELECT date_trunc('hour', created_at) AS hour, count(*)
FROM builder.audit_events
GROUP BY hour
ORDER BY hour DESC
LIMIT 48;
```

### Request ID Correlation

Every API response includes an `X-Request-ID` header (UUID). Use this to correlate:
- Client-side errors
- Server logs
- Audit events
- Runtime events

```bash
# Find all audit events for a specific request
SELECT * FROM builder.audit_events WHERE request_id = '<uuid>';
```

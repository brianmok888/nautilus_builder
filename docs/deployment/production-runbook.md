# Production Deployment Runbook

## Prerequisites
- All staging prerequisites
- Production PostgreSQL with migrations applied
- Production Redis for rate limiting
- S3-compatible artifact storage (MinIO or cloud S3)
- 32+ character `BUILDER_API_TOKEN`
- Non-wildcard CORS origins

## Startup
```bash
cp .env.production .env
docker compose -f docker-compose.production.yml up -d
```

## Health Checks
Same as staging. Additionally verify:
- `/health/ready` reports artifact store reachable
- Rate limiter connected to Redis
- Audit store reachable
- No browser token exposure in web container

## Critical Checks
1. `execution_authority` must be `false` in `/health/backend`
2. No `submit_order` in production code: `bash scripts/check_forbidden_authority.sh`
3. No `NEXT_PUBLIC_BUILDER_API_TOKEN` in web container env
4. CORS origins are explicit, not wildcard

## Backup
- PostgreSQL: `pg_dump builder > backup.sql`
- Artifacts: S3 bucket snapshot

## Disaster Recovery
1. Restore PostgreSQL from backup
2. Restore artifact bucket from snapshot
3. Restart compose stack
4. Verify health checks pass

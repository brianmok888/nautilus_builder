# Staging Deployment Runbook

## Prerequisites
- Docker Compose v2+
- `.env.staging` with strong tokens (32+ chars)

## Startup
```bash
cp .env.staging .env
docker compose -f docker-compose.staging.yml up -d
docker compose -f docker-compose.staging.yml ps
```

## Health Checks
```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/build
curl http://localhost:8000/health/backend
```

## Verification
- `/health/ready` must report all services reachable
- `/health/backend` must show `execution_authority: false`
- Forbidden authority scan must pass: `bash scripts/check_forbidden_authority.sh`

## Teardown
```bash
docker compose -f docker-compose.staging.yml down -v
```

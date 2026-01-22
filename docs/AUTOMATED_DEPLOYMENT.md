# Automated Deployment System

Automated deployment system for local Docker deployments with health checks, rollback capability, and deployment criteria.

## Features

✅ **Pre-deployment Checks**
- Test suite validation
- Docker environment verification
- Disk space monitoring
- Configuration validation

✅ **Automated Deployment**
- Build and deploy new images
- Health check monitoring
- Automatic rollback on failure
- Deployment logging

✅ **Rollback Capability**
- Automatic rollback on health check failures
- Manual rollback to any previous deployment
- MongoDB data backup and restore
- Container image snapshots

✅ **Deployment Criteria**
- Configurable test pass thresholds
- Resource usage limits
- Custom health check endpoints
- Skip deployments for doc-only changes

## Quick Start

### 1. One-Command Deployment

```bash
./scripts/auto-deploy.sh
```

This will:
1. Run pre-deployment checks (tests, Docker, disk space)
2. Backup current deployment
3. Build and deploy new version
4. Verify health checks
5. Rollback automatically if anything fails
6. Clean up old backups

### 2. Manual Rollback

If you need to rollback to a previous version:

```bash
./scripts/rollback.sh
```

This will show you a list of available backups and let you choose which one to restore.

## Configuration

Edit `.deploy-config` to customize deployment behavior:

```bash
# Example configuration
REQUIRE_TESTS=true                    # Run tests before deployment
MIN_TEST_PASS_RATE=90                 # Minimum pass rate (%)
HEALTH_CHECK_RETRIES=10               # Health check attempts
ROLLBACK_ENABLED=true                 # Auto-rollback on failure
BACKUP_RETENTION_COUNT=5              # Keep last 5 backups
```

## Deployment Criteria

The system checks the following before deployment:

### ✅ Must Pass
- Docker is running
- docker-compose is available
- Test suite passes (if enabled)
- Sufficient disk space

### ⚠️ Warnings
- No .env file (uses defaults)
- Disk usage > 90%
- Some tests failed (if below threshold)

### ❌ Deployment Blocked
- Docker not running
- Tests failed completely
- Build failures
- Health checks failed after deployment

## Health Checks

After deployment, the system verifies:

1. **Containers Running**
   - `dinner-menu-api` container is up
   - `dinner-menu-vue` container is up
   - `dinner-menu-mongodb` container is up

2. **API Health**
   - `/api/health` endpoint responds
   - `/api/recipes` endpoint works

3. **Frontend Health**
   - Frontend accessible at port 5173

Default: 10 retries with 5-second intervals (configurable)

## Rollback Process

### Automatic Rollback

Triggered automatically when:
- Build fails
- Container startup fails
- Health checks fail after deployment

Process:
1. Stop new containers
2. Restore previous container images
3. Restart with previous version
4. Verify health checks
5. Report success or failure

### Manual Rollback

Use when you need to go back to a specific version:

```bash
./scripts/rollback.sh
```

You'll see a menu like:
```
────────────────────────────────────
Deployment: dinner-menu-20260121-143022
Date: Tue Jan 21 14:30:22 UTC 2026
API Image: dinner-menu-api:backup-20260121-143022
Frontend Image: dinner-menu-vue:backup-20260121-143022
MongoDB Backup: backups/deployments/mongodb-20260121-143022.archive
────────────────────────────────────
```

Select the deployment to restore.

## Backup Management

### What Gets Backed Up

1. **Container Images**
   - API container snapshot
   - Frontend container snapshot

2. **MongoDB Data**
   - Full database dump
   - Compressed archive format

3. **Metadata**
   - Deployment timestamp
   - Image references
   - Backup locations

### Backup Location

```
backups/deployments/
├── dinner-menu-20260121-143022.info
├── mongodb-20260121-143022.archive
├── dinner-menu-20260121-150534.info
└── mongodb-20260121-150534.archive
```

### Backup Retention

- Keeps last 5 backups by default (configurable)
- Older backups automatically cleaned up
- Manual backups never deleted

## Git Integration

### Automatic Deployment on Git Pull

Set up the post-merge hook:

```bash
cp scripts/git-deploy-hook.sh .git/hooks/post-merge
chmod +x .git/hooks/post-merge
```

Now when you run `git pull`, you'll be asked if you want to deploy:
```
🎣 Git Post-Merge Hook
======================
✅ Code changes detected, deployment will proceed

New changes merged. Deploy now?
  1. Deploy now
  2. Skip (manual deployment later)
Choice (1/2):
```

### Skip Docs-Only Changes

The hook automatically skips deployment if only documentation changed (configurable in `.deploy-config`).

## Logging

All deployments are logged to:
```
logs/deploy-dinner-menu-YYYYMMDD-HHMMSS.log
```

Check logs after deployment:
```bash
tail -f logs/deploy-dinner-menu-*.log
```

## Advanced Usage

### Custom Health Check Endpoints

Edit `.deploy-config`:
```bash
ADDITIONAL_ENDPOINTS="http://localhost:5000/api/custom,http://localhost:5000/api/another"
```

### Deployment Notifications

Future feature - configure webhooks for Slack/Discord notifications:
```bash
NOTIFICATIONS_ENABLED=true
NOTIFICATION_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Scheduled Deployments

Add to crontab for automatic deployments:
```bash
# Daily at 2 AM
0 2 * * * cd /home/kenny/dinner-menu && ./scripts/auto-deploy.sh >> logs/cron-deploy.log 2>&1
```

## Troubleshooting

### Deployment Fails Immediately

**Check Docker:**
```bash
docker info
```

**Check Tests:**
```bash
python -m pytest tests/ -v
```

**Check Logs:**
```bash
tail -f logs/deploy-*.log
```

### Health Checks Fail

**Check containers:**
```bash
docker ps -a
docker logs dinner-menu-api
docker logs dinner-menu-vue
```

**Test manually:**
```bash
curl http://localhost:5000/api/health
curl http://localhost:5173/
```

### Rollback Fails

**Check backups:**
```bash
ls -la backups/deployments/
```

**Manual recovery:**
```bash
docker-compose down
docker-compose up -d --build
```

### No Backups Found

If rollback can't find backups, you may need to rebuild:
```bash
docker-compose down
docker-compose up -d --build
```

## Safety Features

🛡️ **Pre-deployment Validation**
- Tests must pass
- Docker must be running
- Sufficient disk space

🛡️ **Automatic Backups**
- Every deployment creates backups
- Container images preserved
- MongoDB data backed up

🛡️ **Health Monitoring**
- Multiple health check attempts
- Configurable retry intervals
- Multiple endpoint verification

🛡️ **Automatic Rollback**
- Triggered on any failure
- Restores previous working state
- Verifies rollback success

🛡️ **Error Handling**
- All errors trapped
- Automatic cleanup on failure
- Detailed error logging

## Deployment Workflow

```
┌─────────────────────────────────┐
│  Start Deployment               │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Pre-deployment Checks          │
│  ├─ Docker running?             │
│  ├─ Tests passing?              │
│  ├─ Disk space OK?              │
│  └─ .env file exists?           │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Backup Current Deployment      │
│  ├─ Save container images       │
│  ├─ Backup MongoDB data         │
│  └─ Create metadata file        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Deploy New Version             │
│  ├─ Pull latest code (git)      │
│  ├─ Stop containers             │
│  ├─ Build new images            │
│  └─ Start containers            │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Health Checks                  │
│  ├─ Containers running?         │
│  ├─ API responding?             │
│  ├─ Frontend accessible?        │
│  └─ Retry up to 10 times        │
└────────┬───────────┬────────────┘
         │           │
    ✅ Pass      ❌ Fail
         │           │
         │           ▼
         │  ┌─────────────────────┐
         │  │  Automatic Rollback │
         │  │  ├─ Stop containers │
         │  │  ├─ Restore images  │
         │  │  ├─ Restart         │
         │  │  └─ Verify health   │
         │  └─────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Cleanup Old Backups            │
│  ├─ Keep last 5                 │
│  └─ Remove older backups        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  🎉 Deployment Complete          │
└─────────────────────────────────┘
```

## Best Practices

1. **Always Run Tests First**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Check Docker Status**
   ```bash
   docker ps
   docker-compose ps
   ```

3. **Review Logs After Deployment**
   ```bash
   tail -f logs/deploy-*.log
   ```

4. **Keep Backups**
   - Don't delete backup files manually
   - Increase `BACKUP_RETENTION_COUNT` if needed

5. **Monitor Disk Space**
   ```bash
   df -h
   docker system df
   ```

6. **Test Rollback in Non-Production**
   - Verify rollback works before you need it

## Support

For issues or questions:
- Check deployment logs: `logs/deploy-*.log`
- Review Docker logs: `docker logs <container-name>`
- Check container status: `docker ps -a`
- Verify health: `curl http://localhost:5000/api/health`

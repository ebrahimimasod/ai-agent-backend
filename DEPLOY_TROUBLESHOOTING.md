# Deployment Troubleshooting Guide

## Common Git Pull Errors

### Error: "You have divergent branches"

```
hint: You have divergent branches and need to specify how to reconcile them.
hint: You can do so by running one of the following commands sometime before
hint: your next pull:
hint:
hint:   git config pull.rebase false  # merge
hint:   git config pull.rebase true   # rebase
hint:   git config pull.ff only       # fast-forward only
```

**What it means:**
Your local branch and remote branch have different commits. Git doesn't know whether to merge or rebase.

**Solutions:**

#### Option 1: Use the simple deployment script (Recommended for production)

```bash
chmod +x deploy-simple.sh
./deploy-simple.sh
```

This script forcefully syncs with remote, discarding any local changes.

#### Option 2: Configure Git pull strategy

Choose one of these strategies:

**A. Merge (creates merge commits):**
```bash
git config pull.rebase false
./deploy.sh
```

**B. Rebase (cleaner history):**
```bash
git config pull.rebase true
./deploy.sh
```

**C. Fast-forward only (safest, fails if diverged):**
```bash
git config pull.ff only
./deploy.sh
```

To set globally for all repositories:
```bash
git config --global pull.rebase false
```

#### Option 3: Manual resolution

```bash
# Discard all local changes and sync with remote
git fetch origin
git reset --hard origin/main  # or your branch name

# Then run deploy
./deploy.sh
```

## Which Deployment Script to Use?

### deploy.sh
- Interactive (asks before discarding changes)
- Uses rebase strategy
- Falls back to force reset if rebase fails
- Good for: Development environments

### deploy-simple.sh
- Non-interactive
- Always force syncs with remote
- Discards all local changes
- Good for: Production servers, CI/CD

## Common Scenarios

### Scenario 1: Local changes on server

**Problem:** You edited files directly on the server.

**Solution:**
```bash
# Save your changes first (if needed)
git stash

# Deploy
./deploy.sh

# Apply your changes back (if needed)
git stash pop
```

Or just use `deploy-simple.sh` to discard local changes.

### Scenario 2: Merge conflicts

**Problem:** Git can't automatically merge changes.

**Solution:**
```bash
# Force sync with remote (discard local changes)
git fetch origin
git reset --hard origin/main

# Then deploy
./deploy.sh
```

### Scenario 3: Wrong branch

**Problem:** Server is on wrong branch.

**Solution:**
```bash
# Switch to correct branch
git checkout main  # or your branch name
git pull origin main

# Then deploy
./deploy.sh
```

## Best Practices for Production

1. **Never edit files directly on the server**
   - Always commit and push from development
   - Let deployment scripts pull changes

2. **Use deploy-simple.sh for production**
   - Ensures clean sync with remote
   - No manual intervention needed

3. **Set up Git config once**
   ```bash
   cd /opt/your-project
   git config pull.rebase false
   ```

4. **Use specific branches**
   ```bash
   # In deploy script, change to:
   git pull origin production  # instead of $CURRENT_BRANCH
   ```

5. **Backup before deploy**
   ```bash
   # Create backup script
   ./backup.sh
   ./deploy.sh
   ```

## Automated Deployment Setup

### One-time Git configuration on server

```bash
# Navigate to project
cd /opt/your-project

# Set pull strategy (choose one)
git config pull.rebase false  # merge strategy
# or
git config pull.rebase true   # rebase strategy

# Verify
git config --list | grep pull
```

### Make scripts executable

```bash
chmod +x deploy.sh
chmod +x deploy-simple.sh
```

### Test deployment

```bash
# Test with simple script first
./deploy-simple.sh

# If successful, you can use either script
./deploy.sh
```

## Emergency Rollback

If deployment breaks something:

```bash
# View commit history
git log --oneline -10

# Rollback to previous commit
git reset --hard COMMIT_HASH

# Restart services
docker compose down
docker compose up -d --build
```

## Monitoring Deployment

```bash
# Watch logs during deployment
docker compose logs -f api

# Check service health
curl http://localhost:8001/health

# View all services status
docker compose ps
```

## Getting Help

If you encounter issues:

1. Check logs: `docker compose logs`
2. Check Git status: `git status`
3. Check Git config: `git config --list`
4. Try force sync: `git reset --hard origin/main`
5. Use simple deployment: `./deploy-simple.sh`

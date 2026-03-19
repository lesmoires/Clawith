---
trigger: manual
---

## Release Workflow

### 1. Update version numbers
Update the VERSION file in both `frontend/` and `backend/` directories:
- **frontend/VERSION**: Read by `vite.config.ts`, displayed as `x.y.z+YYYYMMDD.HHMM` in the sidebar footer
- **backend/VERSION**: Read by `config.py`, used by `/health` endpoint and API docs

```bash
echo "1.8.0" > frontend/VERSION
echo "1.8.0" > backend/VERSION
```

### 2. Pre-release upgrade verification
Before tagging, review all changes since the last release and verify the upgrade path:

1. **Identify breaking changes**: Run `git diff v<prev>..HEAD` to review. Look for:
   - New database columns/tables (need Alembic migration)
   - Renamed or removed columns (need data migration script)
   - New environment variables (need `.env.example` update)
   - New Python/npm dependencies
   - Changed API contracts

2. **Prepare upgrade scripts if needed**: Ensure:
   - Alembic migrations are idempotent (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`)
   - Data migration scripts (if any) are idempotent and safe to re-run
   - Both **Docker** and **source deployment** upgrade paths are covered

3. **Test the upgrade on dev environment**:
   - Clean the dev environment
   - Deploy the **previous release** version
   - Upgrade to the **new release** following the upgrade steps
   - Verify the application works correctly after upgrade
   - Test both Docker and source deployment upgrade paths

4. **Write release notes** with upgrade instructions for both deployment methods:
   - **Option A: Docker Deployment** — `git pull` + `docker compose down && docker compose up -d --build`
   - **Option B: Source Deployment** — `git pull` + `alembic upgrade head` + dependency update + restart
   - Document any manual steps required (env changes, config migration, etc.)

5. **Cross-version upgrade warning**: Always include this notice in release notes:
   > Users must upgrade one version at a time (e.g., v1.6.0 -> v1.7.0 -> v1.8.0). Skipping versions is not supported because data migration scripts and upgrade steps may depend on the intermediate state of each version.

### 3. Rebuild frontend with new version
`frontend/VERSION` is read by `vite.config.ts` at build time and baked into the JS bundle. **Must rebuild after updating VERSION, before committing.**
```bash
cd frontend && rm -rf dist node_modules/.vite && npm run build && cp public/logo.png dist/ && cp public/logo.svg dist/ && rm -f dist.zip && cd dist && zip -r ../dist.zip . && cd ..
```
> Verify: check that `dist/assets/` JS file hash changed compared to the previous build.

### 4. Commit, tag, and push
Only after upgrade verification passes:
```bash
git add frontend/VERSION backend/VERSION frontend/dist.zip
git commit -m "release: v1.8.0"
git tag v1.8.0
git push origin main --tags
```

### 5. Create GitHub Release
```bash
gh release create v1.8.0 --title "v1.8.0" --notes-file RELEASE_NOTES.md
```
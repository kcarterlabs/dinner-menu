# Migration from Streamlit to Vue.js Frontend

## Overview
This document describes the migration from the Streamlit Python frontend to the Vue.js frontend for the Dinner Menu application.

## Changes Made

### 1. GitHub Actions Workflow (`.github/workflows/docker-build.yml`)

**Updated Test Job:**
- Added Node.js 20 setup
- Added Vue.js frontend test suite execution
- Both Python backend and Vue frontend tests now run in CI/CD

**Updated Build Job:**
- Frontend image now builds from `vue-frontend/Dockerfile` (production build)
- Changed from Streamlit to Vue.js with nginx
- Build summary now references "Vue.js Frontend Image"

### 2. Docker Compose Configuration

**Development (`docker-compose.yml`):**
- Streamlit frontend service commented out as deprecated
- Vue frontend remains active on port 5173 (development mode with hot reload)

**Production (`docker-compose.prod.yml`):**
- Streamlit frontend commented out and documented as deprecated
- Vue frontend promoted to main `frontend` service
- Main domain: `dinner-menu.kcarterlabs.tech` → Vue.js frontend
- Alternative domain: `vue.dinner-menu.kcarterlabs.tech` → Vue.js frontend (duplicate)
- Streamlit accessible at: `streamlit.dinner-menu.kcarterlabs.tech` (if enabled)

### 3. Container Images

**ECR Repository Usage:**
- `dinner-menu-api`: Python Flask backend (unchanged)
- `dinner-menu-frontend`: **Now Vue.js production build** (was Streamlit)

### 4. Frontend Technology Stack

**Old Stack (Deprecated):**
- Python 3.11
- Streamlit
- Port: 8501

**New Stack (Active):**
- Node.js 20
- Vue 3 (Composition API)
- Vite (build tool)
- Nginx (production server)
- Port: 80 (production), 5173 (development)

## Deployment Instructions

### Local Development
```bash
# Start without Streamlit
./rebuild.sh --no-streamlit

# Or manually
docker compose up api vue-frontend
```

### Production Deployment
```bash
# Pull latest images
docker compose -f docker-compose.prod.yml pull

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

### Running Tests
```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd vue-frontend
npm test
```

## Features Comparison

### Streamlit Frontend (Deprecated)
- ✅ Recipe management
- ✅ Dinner menu generation
- ✅ Basic ingredient input
- ❌ No fuzzy ingredient matching
- ❌ No interactive recipe re-roll
- ❌ Limited real-time updates

### Vue.js Frontend (Current)
- ✅ Recipe management with fuzzy ingredient matching
- ✅ Dinner menu generation with weather display
- ✅ Individual recipe re-roll (preserves order)
- ✅ Shopping list with download functionality
- ✅ Real-time interactive updates
- ✅ Responsive design
- ✅ Modern UI with gradient themes
- ✅ Comprehensive test coverage (42 tests)

## Migration Benefits

1. **Better UX**: Interactive, modern interface with real-time updates
2. **Performance**: Faster page loads with client-side rendering
3. **Testability**: Full test suite with component testing
4. **Maintainability**: Standard web stack (HTML/CSS/JS)
5. **Scalability**: Nginx can handle more concurrent users
6. **Features**: Fuzzy matching, individual re-roll, downloadable lists

## Rollback Plan

If needed, to rollback to Streamlit:

1. Uncomment Streamlit service in docker-compose files
2. Update GitHub workflow to build `Dockerfile.frontend`
3. Redeploy with old configuration

```bash
# In docker-compose.prod.yml, uncomment the old frontend service
# and comment out the new one, then:
docker compose -f docker-compose.prod.yml up -d
```

## Testing Checklist

- [x] Backend tests pass in CI/CD
- [x] Frontend tests pass in CI/CD
- [x] Menu generation works
- [x] Recipe re-roll preserves order
- [x] Weather display shows correctly
- [x] Shopping list displays and downloads
- [x] Fuzzy ingredient matching works
- [x] All navigation works
- [x] Responsive design on mobile
- [x] Production build completes successfully

## Next Steps

1. Monitor production deployment
2. Gather user feedback on new UI
3. Remove Streamlit-related files after successful migration
4. Update documentation to remove Streamlit references
5. Archive `Dockerfile.frontend` and `streamlit_app.py`

## Support

For issues or questions about the migration:
- Check Vue.js frontend tests: `cd vue-frontend && npm test`
- Check backend tests: `pytest tests/ -v`
- Review logs: `docker compose logs -f vue-frontend`

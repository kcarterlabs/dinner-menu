# Dinner Menu - Docker Setup

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Your `RAPID_API_FORECAST_KEY` environment variable set

### Running with Docker Compose

1. **Set your API key:**
   ```bash
   export RAPID_API_FORECAST_KEY="your_api_key_here"
   ```

2. **Start the application:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - Streamlit Frontend: http://localhost:8501
   - Flask API: http://localhost:5000

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### View Logs

```bash
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api

# Just frontend
docker-compose logs -f frontend
```

### Rebuild After Changes

```bash
docker-compose up -d --build
```

## Manual Docker Commands

### Build the image:
```bash
docker build -t dinner-menu .
```

### Run API:
```bash
docker run -d -p 5000:5000 \
  -e RAPID_API_FORECAST_KEY="your_key" \
  -v $(pwd)/recipes.json:/app/recipes.json \
  -v $(pwd)/backups:/app/backups \
  --name dinner-menu-api \
  dinner-menu python app.py
```

### Run Streamlit:
```bash
docker run -d -p 8501:8501 \
  --link dinner-menu-api:api \
  --name dinner-menu-frontend \
  dinner-menu python -m streamlit run streamlit_app.py --server.address=0.0.0.0
```

## Data Persistence

The `recipes.json` and `backups/` directory are mounted as volumes, so your data persists even when containers are stopped or removed.

## Environment Variables

- `RAPID_API_FORECAST_KEY`: Your RapidAPI weather forecast key (required)
- `API_BASE_URL`: Base URL for the API (default: http://api:5000/api)

## Troubleshooting

### API key not working
Make sure you export the environment variable before running docker-compose:
```bash
export RAPID_API_FORECAST_KEY="your_key_here"
docker-compose up -d
```

### Cannot connect to API from frontend
The services are on the same Docker network, so the frontend connects to `http://api:5000/api` internally.

### Port already in use
If ports 5000 or 8501 are already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "5001:5000"  # Change host port to 5001
```

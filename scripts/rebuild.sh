#!/bin/bash

set -e

echo "🔧 Dinner Menu - Full Rebuild Script"
echo "====================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
BUILD_API=true
BUILD_STREAMLIT=false  # Streamlit is deprecated, Vue is now default
BUILD_VUE=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --api-only)
      BUILD_STREAMLIT=false
      BUILD_VUE=false
      shift
      ;;
    --streamlit-only)
      BUILD_API=false
      BUILD_VUE=false
      shift
      ;;
    --vue-only)
      BUILD_API=false
      BUILD_STREAMLIT=false
      shift
      ;;
    --no-api)
      BUILD_API=false
      shift
      ;;
    --no-streamlit)
      BUILD_STREAMLIT=false
      shift
      ;;
    --no-vue)
      BUILD_VUE=false
      shift
      ;;
    --help)
      echo "Usage: ./rebuild.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --api-only         Build only the Flask API"
      echo "  --streamlit-only   Build only the Streamlit frontend (deprecated)"
      echo "  --vue-only         Build only the Vue.js frontend"
      echo "  --no-api           Skip building the API"
      echo "  --no-streamlit     Skip building Streamlit frontend (default)"
      echo "  --no-vue           Skip building Vue.js frontend"
      echo "  --help             Show this help message"
      echo ""
      echo "Note: Streamlit frontend is deprecated. Vue.js is now the default."
      echo "      To enable Streamlit, use --streamlit-only or uncomment it in docker-compose.yml"
      echo ""
      echo "Examples:"
      echo "  ./rebuild.sh                    # Build API and Vue.js (default)"
      echo "  ./rebuild.sh --vue-only         # Build only Vue frontend"
      echo "  ./rebuild.sh --api-only         # Build only the API"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}Build Configuration:${NC}"
echo "  API (Flask):        $([ "$BUILD_API" = true ] && echo "✅" || echo "⏭️  Skip")"
echo "  Streamlit Frontend: $([ "$BUILD_STREAMLIT" = true ] && echo "✅" || echo "⏭️  Skip (deprecated)")"
echo "  Vue.js Frontend:    $([ "$BUILD_VUE" = true ] && echo "✅" || echo "⏭️  Skip")"
echo ""

echo -e "${YELLOW}🛑 Stopping all containers...${NC}"
docker compose down

echo ""
echo -e "${YELLOW}🗑️  Removing old images...${NC}"

if [ "$BUILD_API" = true ]; then
  echo "  - Removing dinner-menu-api images..."
  docker rmi dinner-menu-api 2>/dev/null || true
fi

if [ "$BUILD_STREAMLIT" = true ]; then
  echo "  - Removing dinner-menu-frontend (Streamlit) images..."
  docker rmi dinner-menu-frontend 2>/dev/null || true
fi

if [ "$BUILD_VUE" = true ]; then
  echo "  - Removing dinner-menu-vue images..."
  docker rmi dinner-menu-vue 2>/dev/null || true
fi

echo "  - Removing dangling dinner-menu images..."
docker rmi $(docker images -q dinner-menu) 2>/dev/null || true

echo ""
echo -e "${YELLOW}🧹 Pruning dangling images...${NC}"
docker image prune -f

echo ""
echo -e "${GREEN}🔨 Building containers...${NC}"
echo ""

# Build specific services
BUILD_SERVICES=""

if [ "$BUILD_API" = true ]; then
  echo -e "${BLUE}📦 Building Flask API...${NC}"
  BUILD_SERVICES="$BUILD_SERVICES api"
fi

if [ "$BUILD_STREAMLIT" = true ]; then
  echo -e "${BLUE}📦 Building Streamlit Frontend...${NC}"
  BUILD_SERVICES="$BUILD_SERVICES frontend"
fi

if [ "$BUILD_VUE" = true ]; then
  echo -e "${BLUE}📦 Building Vue.js Frontend...${NC}"
  BUILD_SERVICES="$BUILD_SERVICES vue-frontend"
fi

# Build and start services
if [ -n "$BUILD_SERVICES" ]; then
  docker compose up -d --build $BUILD_SERVICES
else
  echo "No services selected to build!"
  exit 1
fi

echo ""
echo -e "${GREEN}✅ Done! Containers are running.${NC}"
echo ""

echo -e "${BLUE}📊 Container Status:${NC}"
docker compose ps

echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo "  API:                http://localhost:5000/api"
echo "  Vue.js Frontend:    http://localhost:5173"
if [ "$BUILD_STREAMLIT" = true ]; then
  echo "  Streamlit Frontend: http://localhost:8501 (deprecated)"
fi

echo ""
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "  View all logs:       docker compose logs -f"
echo "  View API logs:       docker compose logs -f api"
echo "  View Vue logs:       docker compose logs -f vue-frontend"
if [ "$BUILD_STREAMLIT" = true ]; then
  echo "  View Streamlit logs: docker compose logs -f frontend"
fi
echo "  Stop all:            docker compose down"
echo ""

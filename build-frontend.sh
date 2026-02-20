#!/bin/bash

# Build script for frontend - builds for production and places output in backend/dist
# Usage: ./build-frontend.sh [output_dir] [api_url]
#   output_dir: where to place the built files (default: backend/dist)
#   api_url: backend API URL (default: /api for relative path)
#
# Examples:
#   ./build-frontend.sh                                    # Uses /api
#   ./build-frontend.sh backend/dist /api                  # Explicit relative path
#   ./build-frontend.sh backend/dist https://example.com/api  # Absolute URL

set -e

# Parse arguments
PROJECT_ROOT=$(dirname "$(realpath "$0")")
FRONTEND_DIR="$PROJECT_ROOT/frontend"
OUTPUT_DIR=${1:-"$PROJECT_ROOT/backend/dist"}
API_URL=${2:-"/api"}

echo "🏗️  Building frontend for production..."
echo "📁 Output directory: $OUTPUT_DIR"
echo "🔗 API URL: $API_URL"

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Set build configuration
export BUILD_OUTPUT_DIR="$OUTPUT_DIR"
export VITE_API_URL="$API_URL"

# Clean previous build if it exists
if [ -d "$OUTPUT_DIR" ]; then
    echo "🧹 Cleaning previous build..."
    rm -rf "$OUTPUT_DIR"
fi

# Build the frontend
echo "🔨 Building frontend..."
npm run build

# Add version info to build
BUILD_VERSION=$(node -p "require('./package.json').version")
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "{\"version\":\"$BUILD_VERSION\",\"buildTime\":\"$BUILD_TIME\"}" > "$OUTPUT_DIR/build-info.json"

echo "✅ Frontend build complete!"
echo "📊 Build size:"
du -sh "$OUTPUT_DIR"

echo ""
echo "🏷️  Build info:"
echo "   Version: $BUILD_VERSION"
echo "   Build time: $BUILD_TIME"
echo "   API URL: $API_URL"
echo ""
echo "🌐 Frontend ready to serve from FastAPI backend at:"
echo "   http://localhost:8000"


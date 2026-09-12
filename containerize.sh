#!/usr/bin/bash
# Containerization Script for Futuristic Contact Manager

# Step 1: Stop running processes
pkill -f uvicorn 2>/dev/null || echo "No uvicorn processes to stop"
pkill -f "python3 futuristic-contact-manager/backend/api.py" 2>/dev/null || echo "No API processes to stop"

# Step 2: Fix dependencies if needed
declare -a NECESSARY_PACKAGES=(
    "fastapi>=0.104.0"
    "uvicorn[standard]>=0.24.0"
    "pydantic>=2.5.0"
    "python-multipart>=0.0.3"
    "httptools>=0.6.3"
    "watchfiles>=0.20"
)

echo "=== Containerization Script for Futuristic Contact Manager ==="
echo ""
echo "This script will prepare the system for Docker containerization."
echo ""

# Step 3: Create optimized Dockerfile
OUTPUT_FILE="Dockerfile"
REDIRECT=""

if [[ -w "${OUTPUT_FILE}" ]]; then
    REDIRECT=""
elif [[ -e "${OUTPUT_FILE}" ]]; then
    echo "Warning: ${OUTPUT_FILE} exists but is not writable."
    REDIRECT=">/dev/null
else
    REDIRECT=""
fi

cat > "${OUTPUT_FILE}" "${REDIRECT}" <<'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for container build
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Create necessary directories
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "✓ Created optimized Dockerfile"

# Step 4: Create enhanced docker-compose.yml
OUTPUT_FILE="docker-compose.yml"
cat > "${OUTPUT_FILE}" <<'EOF'
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///data/contacts.db
      - PYTHONUNBUFFERED=1
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Optional: Redis for caching/queue
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

EOF

echo "✓ Created enhanced docker-compose.yml"

# Step 5: Create requirements.txt with all necessary packages
OUTPUT_FILE="requirements.txt"
cat > "${OUTPUT_FILE}" <<'EOF'
# Core FastAPI and web framework dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.3

# Additional performance and development dependencies
httptools>=0.6.3
watchfiles>=0.20
EOF

echo "✓ Created comprehensive requirements.txt"

# Step 6: Stop any existing processes before finalizing
echo ""
echo "=== Checking for existing processes ==="
if pgrep -f "uvicorn" >/dev/null; then
    echo "⚠ Warning: uvicorn processes are still running."
    echo "   Please stop them before using Docker."
else
    echo "✓ No running uvicorn processes found."
fi

# Step 7: Verify all required files exist
REQUIRED_FILES=(
    "Dockerfile"
    "docker-compose.yml"
    "requirements.txt"
    "backend/api.py"
    "frontend/package.json"
)

echo ""
echo "=== Verification ==="
all_files_exist=true
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "${file}" ]]; then
        echo "✓ ${file} exists"
    else
        echo "✗ ${file} MISSING"
        all_files_exist=false
    fi
done

if $all_files_exist; then
    echo ""
    echo "=== Containerization Complete ==="
    echo "✓ All necessary files have been created"
    echo "✓ The project is now ready for Docker containerization"
    echo ""
    echo "Next steps to run the containerized application:"
    echo "  1. Build the Docker image:"
    echo "     docker build -t futuristic-contact-manager ."
    echo ""
    echo "  2. Run the container:":
    echo "     docker run -p 8000:8000 --rm futuristic-contact-manager"
    echo ""
    echo "  3. Or use docker-compose (recommended):"
    echo "     docker compose up -d"
    echo ""
    echo "  4. Verify the running service:"
    echo "     curl http://localhost:8000/health"
else
    echo ""
    echo "✗ Some required files are missing. Please check the project structure."
fi

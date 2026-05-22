#!/bin/bash
echo "Starting application..."
cd /home/site/wwwroot

# Install dependencies if not already installed
if [ ! -d "/home/site/wwwroot/.venv" ]; then
  echo "Creating virtual environment..."
  python -m venv /home/site/wwwroot/.venv
  source /home/site/wwwroot/.venv/bin/activate
  echo "Installing dependencies..."
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "Using existing virtual environment..."
  source /home/site/wwwroot/.venv/bin/activate
fi

# Start gunicorn
echo "Starting FastAPI with gunicorn..."
gunicorn backend.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
#
# ============================================================================
# TROUBLESHOOTING
# ============================================================================
# If app doesn't start, check logs:
#   az webapp log tail --resource-group zava-rg --name zava-backend-<id>
#
# Common issues:
# - Requirements not found: Ensure requirements.txt is in /home/site/wwwroot
# - Module not found: Ensure backend/main.py exists and has 'app' instance
# - Port conflict: Azure requires port 8000 for Python apps
# - Permission denied: Ensure script has execute permissions (chmod +x)
#
# ============================================================================

# This file is a template/placeholder
# The actual startup.sh is created during deployment by deploy-azure.yml
# See challenge-4-guide.md Exercise 1 for complete workflow generation

echo "This is a template file. The actual startup.sh is created during deployment."
echo "See challenge-4-guide.md Exercise 1 Task 1 for complete instructions."

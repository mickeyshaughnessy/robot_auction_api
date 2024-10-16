#!/bin/bash

# Set variables
PROJECT_DIR="/home/ubuntu/robot_auction_api"
LOG_FILE="/var/log/robot_auction_api_build.log"
REQUIREMENTS_FILE="requirements.txt"
SERVICE_NAME="robot-exchange-api.service"

# Function for logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Navigate to the project directory
cd "$PROJECT_DIR" || { log "Failed to change to project directory. Exiting."; exit 1; }

# Update the repository
log "Pulling latest changes from git..."
if git pull; then
    log "Git pull successful."
else
    log "Git pull failed. Exiting."; exit 1
fi

# Install or update dependencies
log "Installing/updating dependencies..."
if pip3 install -r "$REQUIREMENTS_FILE" --break-system-packages; then
    log "Dependencies installed/updated successfully."
else
    log "Failed to install/update dependencies. Exiting."; exit 1
fi

# Restart the service
log "Restarting the API service..."
if sudo systemctl restart "$SERVICE_NAME"; then
    log "API service restarted successfully."
else
    log "Failed to restart API service. Exiting."; exit 1
fi

log "API server updated, tested, and restarted successfully."

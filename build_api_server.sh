#!/bin/bash

# Navigate to the project directory
cd /home/ubuntu/robot_auction_api

# Update the repository
git pull

# Install or update dependencies
pip3 install -r requirements.txt --break-system-packages

# Restart the service
sudo systemctl restart robot-exchange-api.service

echo "API server updated and restarted"

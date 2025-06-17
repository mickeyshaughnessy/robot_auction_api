#!/bin/bash
############
#<thinking>
#🤔🤔🤔🤠
#User has expired cert on rse-api.com:5002
#Running Flask app via systemd service: robot-exchange-api.service
#Need to renew cert and restart the specific Flask service
#Check status, renew, restart Flask service, verify
#</thinking>
###########

set -e

DOMAIN="rse-api.com"
SERVICE_NAME="robot-exchange-api.service"
LOG_FILE="/tmp/ssl_renew_$(date +%Y%m%d_%H%M%S).log"

echo "=== SSL Certificate Renewal for $DOMAIN ===" | tee $LOG_FILE

# Check current certificate status
echo "Checking current certificate..." | tee -a $LOG_FILE
openssl s_client -connect $DOMAIN:5002 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -dates -issuer | tee -a $LOG_FILE

# Show existing certbot certificates
echo -e "\nExisting certbot certificates:" | tee -a $LOG_FILE
sudo certbot certificates 2>&1 | tee -a $LOG_FILE

# Attempt renewal
echo -e "\nAttempting certificate renewal..." | tee -a $LOG_FILE
if sudo certbot renew --cert-name $DOMAIN 2>&1 | tee -a $LOG_FILE; then
    echo "Certificate renewed successfully!" | tee -a $LOG_FILE
else
    echo "Standard renewal failed, trying force renewal..." | tee -a $LOG_FILE
    sudo certbot renew --cert-name $DOMAIN --force-renewal 2>&1 | tee -a $LOG_FILE
fi

# Restart Flask application
echo -e "\nRestarting Flask application ($SERVICE_NAME)..." | tee -a $LOG_FILE
if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    sudo systemctl restart $SERVICE_NAME
    echo "Restarted $SERVICE_NAME successfully" | tee -a $LOG_FILE
    
    # Wait for service to come back up
    echo "Waiting for service to start..." | tee -a $LOG_FILE
    sleep 5
    
    # Check service status
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ $SERVICE_NAME is running" | tee -a $LOG_FILE
    else
        echo "⚠️  $SERVICE_NAME failed to start properly" | tee -a $LOG_FILE
        sudo systemctl status $SERVICE_NAME --no-pager | tee -a $LOG_FILE
    fi
else
    echo "⚠️  $SERVICE_NAME is not currently running" | tee -a $LOG_FILE
fi

# Test the renewed certificate
echo -e "\nTesting renewed certificate..." | tee -a $LOG_FILE
sleep 2
if curl -s --max-time 10 https://$DOMAIN:5002/ping >/dev/null; then
    echo "✅ SUCCESS: SSL certificate is working!" | tee -a $LOG_FILE
    echo "API Response:" | tee -a $LOG_FILE
    curl https://$DOMAIN:5002/ping | tee -a $LOG_FILE
else
    echo "⚠️  WARNING: Still having SSL issues, check manually" | tee -a $LOG_FILE
    echo "Trying with -k flag to test if service is running:" | tee -a $LOG_FILE
    curl -k https://$DOMAIN:5002/ping | tee -a $LOG_FILE
fi

# Enable auto-renewal if not already enabled
if ! systemctl is-enabled --quiet certbot.timer 2>/dev/null; then
    echo -e "\nEnabling certbot auto-renewal..." | tee -a $LOG_FILE
    sudo systemctl enable certbot.timer
    sudo systemctl start certbot.timer
fi

echo -e "\n=== Renewal Complete ===" | tee -a $LOG_FILE
echo "Log saved to: $LOG_FILE"

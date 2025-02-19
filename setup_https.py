#!/usr/bin/env python3

"""
############
#<thinking>
# We need to:
# 1. Copy existing certificates if available
# 2. Generate self-signed certificate if needed
# 3. Set up systemd service
# 4. Make sure permissions are correct
#</thinking>
###########
"""

import os, subprocess, sys

def setup_https():
    print("Setting up HTTPS for Robot Exchange API")
    
    # Certificate paths
    cert_dir = "/etc/ssl/certs"
    key_dir = "/etc/ssl/private"
    cert_path = f"{cert_dir}/robot_exchange.pem"
    key_path = f"{key_dir}/robot_exchange_key.pem"
    
    # Check if we need to create directories
    os.makedirs(cert_dir, exist_ok=True)
    os.makedirs(key_dir, exist_ok=True)
    
    # Check if certificates exist
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        use_existing = input("Do you have existing certificates for robotservicesauction.com? (y/n): ").lower()
        
        if use_existing == 'y':
            existing_cert = input("Path to existing certificate (.pem): ")
            existing_key = input("Path to existing key (.pem): ")
            
            # Copy existing certificates
            subprocess.run(f"sudo cp {existing_cert} {cert_path}", shell=True)
            subprocess.run(f"sudo cp {existing_key} {key_path}", shell=True)
        else:
            # Generate self-signed certificate
            print("Generating self-signed certificate...")
            cmd = f"sudo openssl req -x509 -newkey rsa:4096 -keyout {key_path} -out {cert_path} -days 365 -nodes"
            subprocess.run(cmd, shell=True)
    
    # Set permissions
    subprocess.run(f"sudo chmod 644 {cert_path}", shell=True)
    subprocess.run(f"sudo chmod 600 {key_path}", shell=True)
    
    # Reload and start service
    subprocess.run("sudo systemctl daemon-reload", shell=True)
    subprocess.run("sudo systemctl restart robot-exchange-api.service", shell=True)
    
    print("HTTPS setup complete!")
    print(f"Certificates installed at {cert_path} and {key_path}")
    print("Remember to update your robot-exchange-api.service file manually")
    print("Then restart with: sudo systemctl restart robot-exchange-api.service")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run with sudo")
        sys.exit(1)
    setup_https()

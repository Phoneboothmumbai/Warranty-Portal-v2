#!/bin/bash

# ============================================================
# TGMS Installation Script for Warranty Portal
# ============================================================
# This script installs and configures TGMS with
# multi-tenant white-labeling support.
# 
# Run on Ubuntu 20.04/22.04 or Debian 11/12
# ============================================================

set -e

echo "=============================================="
echo "  TGMS Installation for Warranty Portal"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./install_tgms.sh)"
    exit 1
fi

# Configuration
read -p "Enter your domain for TGMS (e.g., rmm.yourcompany.com): " MESH_DOMAIN
read -p "Enter admin email: " ADMIN_EMAIL
read -p "Enter admin password: " -s ADMIN_PASSWORD
echo ""

if [ -z "$MESH_DOMAIN" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "Error: All fields are required."
    exit 1
fi

echo ""
echo "Installing dependencies..."
apt-get update
apt-get install -y nodejs npm mongodb-org || apt-get install -y nodejs npm mongodb

# Create tgms user
useradd -m -s /bin/bash tgms 2>/dev/null || true

# Install TGMS
echo "Installing TGMS..."
cd /opt
mkdir -p tgms
cd tgms
npm install tgms

# Create data directory
mkdir -p tgms-data
mkdir -p tgms-files
mkdir -p tgms-web/public

# Create config.json with white-label support
echo "Creating configuration..."
cat > tgms-data/config.json << EOF
{
  "\$schema": "http://info.tgms.com/downloads/tgms-config-schema.json",
  "settings": {
    "cert": "${MESH_DOMAIN}",
    "port": 443,
    "redirPort": 80,
    "AgentPong": 300,
    "TLSOffload": false,
    "SelfUpdate": false,
    "AllowFraming": true,
    "WebRTC": true,
    "MongoDb": "mongodb://127.0.0.1:27017/tgms",
    "WANonly": true,
    "SessionTime": 60,
    "SessionKey": "$(openssl rand -hex 32)"
  },
  "domains": {
    "": {
      "title": "Remote Management Portal",
      "title2": "Device Management",
      "newAccounts": false,
      "userNameIsEmail": true,
      "minify": true,
      "NewAccountsUserGroups": [],
      "footer": "",
      "welcomeText": "Welcome to Remote Management",
      "nightMode": 1,
      "siteStyle": 2,
      "allowedOrigin": "*",
      "agentCustomization": {
        "displayName": "Remote Agent",
        "description": "Remote Support Agent",
        "companyName": "Your Company",
        "serviceName": "RemoteAgent",
        "foregroundColor": "#FFFFFF",
        "backgroundColor": "#0F62FE"
      },
      "consentMessages": {
        "title": "Remote Support",
        "desktop": "Your IT support team would like to view your desktop. Do you allow this?",
        "terminal": "Your IT support team would like to open a terminal session. Do you allow this?",
        "files": "Your IT support team would like to access files on your computer. Do you allow this?"
      }
    }
  }
}
EOF

# Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/tgms.service << EOF
[Unit]
Description=TGMS Remote Management
After=network.target mongodb.service

[Service]
Type=simple
LimitNOFILE=1000000
ExecStart=/usr/bin/node /opt/tgms/node_modules/tgms
WorkingDirectory=/opt/tgms
Environment=NODE_ENV=production
User=tgms
Group=tgms
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R tgms:tgms /opt/tgms

# Start MongoDB
systemctl enable mongod 2>/dev/null || systemctl enable mongodb 2>/dev/null || true
systemctl start mongod 2>/dev/null || systemctl start mongodb 2>/dev/null || true

# Start TGMS
systemctl daemon-reload
systemctl enable tgms
systemctl start tgms

# Wait for TGMS to start
echo "Waiting for TGMS to initialize..."
sleep 10

# Create admin account
echo "Creating admin account..."
cd /opt/tgms
node node_modules/tgms --createaccount "$ADMIN_EMAIL" --pass "$ADMIN_PASSWORD" --admin || true

# Configure firewall
echo "Configuring firewall..."
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true
ufw allow 4433/tcp 2>/dev/null || true

echo ""
echo "=============================================="
echo "  Installation Complete!"
echo "=============================================="
echo ""
echo "TGMS is now running at: https://${MESH_DOMAIN}"
echo ""
echo "Admin credentials:"
echo "  Email: ${ADMIN_EMAIL}"
echo "  Password: [as entered]"
echo ""
echo "To connect from Warranty Portal:"
echo "1. Go to Settings > Remote Management"
echo "2. Enter Server URL: https://${MESH_DOMAIN}"
echo "3. Enter your admin credentials"
echo "4. Click 'Configure Connection'"
echo ""
echo "To customize white-labeling, edit:"
echo "  /opt/tgms/tgms-data/config.json"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status tgms   # Check status"
echo "  sudo systemctl restart tgms  # Restart"
echo "  sudo journalctl -u tgms -f   # View logs"
echo ""
echo "=============================================="

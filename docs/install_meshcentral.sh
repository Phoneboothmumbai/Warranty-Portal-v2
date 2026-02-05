#!/bin/bash

# ============================================================
# MeshCentral Installation Script for Warranty Portal
# ============================================================
# This script installs and configures MeshCentral with
# multi-tenant white-labeling support.
# 
# Run on Ubuntu 20.04/22.04 or Debian 11/12
# ============================================================

set -e

echo "=============================================="
echo "  MeshCentral Installation for Warranty Portal"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./install_meshcentral.sh)"
    exit 1
fi

# Configuration
read -p "Enter your domain for MeshCentral (e.g., rmm.yourcompany.com): " MESH_DOMAIN
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

# Create meshcentral user
useradd -m -s /bin/bash meshcentral 2>/dev/null || true

# Install MeshCentral
echo "Installing MeshCentral..."
cd /opt
mkdir -p meshcentral
cd meshcentral
npm install meshcentral

# Create data directory
mkdir -p meshcentral-data
mkdir -p meshcentral-files
mkdir -p meshcentral-web/public

# Create config.json with white-label support
echo "Creating configuration..."
cat > meshcentral-data/config.json << EOF
{
  "\$schema": "http://info.meshcentral.com/downloads/meshcentral-config-schema.json",
  "settings": {
    "cert": "${MESH_DOMAIN}",
    "port": 443,
    "redirPort": 80,
    "AgentPong": 300,
    "TLSOffload": false,
    "SelfUpdate": false,
    "AllowFraming": true,
    "WebRTC": true,
    "MongoDb": "mongodb://127.0.0.1:27017/meshcentral",
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
cat > /etc/systemd/system/meshcentral.service << EOF
[Unit]
Description=MeshCentral Remote Management
After=network.target mongodb.service

[Service]
Type=simple
LimitNOFILE=1000000
ExecStart=/usr/bin/node /opt/meshcentral/node_modules/meshcentral
WorkingDirectory=/opt/meshcentral
Environment=NODE_ENV=production
User=meshcentral
Group=meshcentral
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R meshcentral:meshcentral /opt/meshcentral

# Start MongoDB
systemctl enable mongod 2>/dev/null || systemctl enable mongodb 2>/dev/null || true
systemctl start mongod 2>/dev/null || systemctl start mongodb 2>/dev/null || true

# Start MeshCentral
systemctl daemon-reload
systemctl enable meshcentral
systemctl start meshcentral

# Wait for MeshCentral to start
echo "Waiting for MeshCentral to initialize..."
sleep 10

# Create admin account
echo "Creating admin account..."
cd /opt/meshcentral
node node_modules/meshcentral --createaccount "$ADMIN_EMAIL" --pass "$ADMIN_PASSWORD" --admin || true

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
echo "MeshCentral is now running at: https://${MESH_DOMAIN}"
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
echo "  /opt/meshcentral/meshcentral-data/config.json"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status meshcentral   # Check status"
echo "  sudo systemctl restart meshcentral  # Restart"
echo "  sudo journalctl -u meshcentral -f   # View logs"
echo ""
echo "=============================================="

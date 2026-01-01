# 🚀 Deployment Guide: Warranty & Asset Tracking Portal
## Deploy on Ubuntu VPS (Vultr/DigitalOcean/AWS)

---

## 📋 Prerequisites

- Ubuntu 20.04/22.04 LTS server
- Domain name (optional but recommended)
- SSH access to server
- Minimum: 1GB RAM, 1 vCPU, 25GB SSD

---

## 🔧 Step 1: Server Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl git nginx certbot python3-certbot-nginx

# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11+ and pip
sudo apt install -y python3 python3-pip python3-venv

# Install MongoDB
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

---

## 📁 Step 2: Create Application Directory

```bash
# Create app directory
sudo mkdir -p /var/www/warranty-portal
sudo chown $USER:$USER /var/www/warranty-portal
cd /var/www/warranty-portal

# Create subdirectories
mkdir -p backend frontend uploads
```

---

## 🔙 Step 3: Deploy Backend

### 3.1 Upload Backend Files

Upload the `/app/backend` folder contents to `/var/www/warranty-portal/backend/`

Required files:
- `server.py`
- `requirements.txt`
- `.env` (create new one)

### 3.2 Create Python Virtual Environment

```bash
cd /var/www/warranty-portal/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Create Backend .env File

```bash
cat > /var/www/warranty-portal/backend/.env << 'EOF'
MONGO_URL=mongodb://localhost:27017
DB_NAME=warranty_portal
CORS_ORIGINS=https://yourdomain.com,http://localhost:3000
JWT_SECRET=your-super-secure-secret-key-change-this-in-production-2025
EOF
```

**⚠️ IMPORTANT:** Change `JWT_SECRET` to a secure random string!

### 3.4 Create Systemd Service for Backend

```bash
sudo cat > /etc/systemd/system/warranty-backend.service << 'EOF'
[Unit]
Description=Warranty Portal Backend
After=network.target mongod.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/warranty-portal/backend
Environment="PATH=/var/www/warranty-portal/backend/venv/bin"
ExecStart=/var/www/warranty-portal/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
sudo chown -R www-data:www-data /var/www/warranty-portal
sudo chmod -R 755 /var/www/warranty-portal

# Start backend service
sudo systemctl daemon-reload
sudo systemctl enable warranty-backend
sudo systemctl start warranty-backend

# Check status
sudo systemctl status warranty-backend
```

---

## 🎨 Step 4: Deploy Frontend

### 4.1 Upload Frontend Build

Upload the `/app/frontend/build` folder contents to `/var/www/warranty-portal/frontend/`

The `build` folder contains the production-ready static files.

### 4.2 Set Permissions

```bash
sudo chown -R www-data:www-data /var/www/warranty-portal/frontend
sudo chmod -R 755 /var/www/warranty-portal/frontend
```

---

## 🌐 Step 5: Configure Nginx

### 5.1 Create Nginx Configuration

```bash
sudo cat > /etc/nginx/sites-available/warranty-portal << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;  # Change this!

    # Frontend - React App
    root /var/www/warranty-portal/frontend;
    index index.html;

    # Handle React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        client_max_body_size 50M;
    }

    # File uploads
    location /uploads/ {
        alias /var/www/warranty-portal/uploads/;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/warranty-portal /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔒 Step 6: SSL Certificate (HTTPS)

```bash
# Install SSL certificate with Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

---

## 🔥 Step 7: Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## ✅ Step 8: Verify Deployment

```bash
# Check services
sudo systemctl status mongod
sudo systemctl status warranty-backend
sudo systemctl status nginx

# Test backend API
curl http://localhost:8001/api/

# Test frontend
curl http://localhost/
```

---

## 📝 Environment Variables Reference

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=warranty_portal
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET=your-secure-random-string
```

### Frontend (build-time)
The frontend is pre-built with the backend URL. If you need to change it:

1. Edit `/app/frontend/.env`:
```
REACT_APP_BACKEND_URL=https://yourdomain.com
```

2. Rebuild: `cd /app/frontend && yarn build`

3. Re-upload the `build` folder

---

## 🔄 Updating the Application

### Update Backend
```bash
cd /var/www/warranty-portal/backend
# Upload new server.py
sudo systemctl restart warranty-backend
```

### Update Frontend
```bash
# Upload new build folder to /var/www/warranty-portal/frontend/
sudo systemctl reload nginx
```

---

## 📊 Useful Commands

```bash
# View backend logs
sudo journalctl -u warranty-backend -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart warranty-backend
sudo systemctl restart nginx
sudo systemctl restart mongod

# MongoDB shell
mongosh warranty_portal
```

---

## 🆘 Troubleshooting

### Backend not starting
```bash
# Check logs
sudo journalctl -u warranty-backend -n 100

# Test manually
cd /var/www/warranty-portal/backend
source venv/bin/activate
python -c "import server; print('OK')"
```

### 502 Bad Gateway
- Backend not running: `sudo systemctl start warranty-backend`
- Check backend logs: `sudo journalctl -u warranty-backend -f`

### MongoDB connection issues
```bash
sudo systemctl status mongod
sudo systemctl restart mongod
```

### Permission issues
```bash
sudo chown -R www-data:www-data /var/www/warranty-portal
sudo chmod -R 755 /var/www/warranty-portal
```

---

## 🎉 Done!

Your Warranty & Asset Tracking Portal should now be live at:
- **Frontend**: https://yourdomain.com
- **Admin Panel**: https://yourdomain.com/admin/login
- **API**: https://yourdomain.com/api/

**Default Admin Login:**
- Email: admin@demo.com
- Password: admin123

**⚠️ Change the admin password after first login!**

# MoltBot Setup Guide for Your Portal

## Prerequisites

Your server (65.20.87.25) needs:
- Node.js 22+ 
- npm or pnpm

## Step 1: Install MoltBot

SSH into your server and run:

```bash
# Check Node.js version (must be 22+)
node --version

# If Node.js is old, update it:
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install MoltBot globally
npm install -g moltbot@latest
```

## Step 2: Run the Setup Wizard

```bash
moltbot onboard --install-daemon
```

During the wizard:
1. **Select LLM**: Choose "Claude" or "OpenAI" (you'll need an API key)
2. **Link WhatsApp**: Scan the QR code with your WhatsApp
3. **Link Telegram** (optional): Create a bot via @BotFather and paste the token
4. **Install as daemon**: Say "yes" to auto-start on boot

## Step 3: Configure Webhook to Your Portal

After MoltBot is running, configure it to send messages to your portal:

```bash
# Set the webhook URL (replace with your actual domain)
moltbot config set webhook.url "https://your-domain.com/api/admin/moltbot/webhook/YOUR_ORG_ID"

# Set a webhook secret (optional but recommended)
moltbot config set webhook.secret "YOUR_SECRET_KEY_HERE"
```

To get your `YOUR_ORG_ID`:
1. Log into your admin portal
2. Go to Settings → Organization
3. Copy the Organization ID

## Step 4: Configure Your Portal

1. Go to **Admin Panel → Settings → Integrations** (or create this page)
2. Enable MoltBot Integration
3. Enter:
   - **API Key**: Get from `moltbot config get api.key`
   - **Webhook Secret**: Same as you set in Step 3

## Step 5: Test the Integration

Send a message to your WhatsApp/Telegram bot. You should see:
1. A greeting message asking how to help
2. Options to create a ticket, check status, or general inquiry
3. If you choose to create a ticket, it will ask for details before creating

## Useful Commands

```bash
# Check MoltBot status
moltbot doctor

# View logs
moltbot logs -f

# Restart MoltBot
sudo systemctl restart moltbot

# Test sending a message
moltbot message send --to +91XXXXXXXXXX --message "Test message"
```

## Troubleshooting

### WhatsApp Disconnected
```bash
moltbot whatsapp reconnect
```

### Webhook Not Receiving Messages
1. Check if MoltBot is running: `moltbot doctor`
2. Check webhook config: `moltbot config get webhook`
3. Test webhook manually: `curl -X POST https://your-domain.com/api/admin/moltbot/webhook/YOUR_ORG_ID -H "Content-Type: application/json" -d '{"event_type":"test"}'`

### Need Help?
- MoltBot Documentation: https://molt-bot.live/docs
- MoltBot GitHub: https://github.com/moltbot/moltbot

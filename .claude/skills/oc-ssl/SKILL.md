---
name: oc-ssl
description: "Set up SSL/HTTPS certificates using Let's Encrypt certbot. Use when the user says 'setup ssl', 'get certificate', 'enable https', 'certbot', 'letsencrypt', or wants to secure their ClawedBack instance with HTTPS on a public domain."
allowed-tools: "Read Write Edit Bash Grep"
---

# SSL Certificate Setup

Obtain a free SSL certificate from Let's Encrypt using certbot, configure ClawedBack to use it, and set up auto-renewal.

## Prerequisites

Before starting, confirm:
1. The user has a **domain name** pointing to this server (e.g., `claude.example.com`)
2. **Port 80** is open and not in use (certbot needs it for verification)
3. The user is running as **root** (Mode B or C) — certbot requires root to bind port 80

Check these:
```bash
# Are we root?
id -u

# Is port 80 free?
ss -tlnp | grep ':80 ' || echo "Port 80 is free"

# Can the domain resolve to us?
# Ask the user for their domain first
```

Ask the user: **"What domain name points to this server?"** (e.g., `claude.example.com`)

Store the domain for use throughout this skill. Call it `$DOMAIN`.

## Step 1: Install certbot

```bash
which certbot 2>/dev/null && echo "already installed" || apt install -y certbot
```

If not on Debian/Ubuntu:
```bash
# Fedora/RHEL
dnf install -y certbot
# Arch
pacman -S --noconfirm certbot
```

## Step 2: Stop the ClawedBack server temporarily

Certbot standalone needs port 80. If the ClawedBack server is running on port 80 or 8080, it won't conflict (certbot uses 80, we use 8080). But if something else is on port 80, stop it:

```bash
# Check if our server is on port 80
ss -tlnp | grep ':80 '
# If something is there, note what it is and stop it temporarily
```

## Step 3: Request the certificate

```bash
certbot certonly --standalone --non-interactive --agree-tos --email "$USER_EMAIL" -d "$DOMAIN"
```

Ask the user for their **email address** for Let's Encrypt notifications (expiry warnings, etc.).

If certbot succeeds, certificates are at:
- **Certificate**: `/etc/letsencrypt/live/$DOMAIN/fullchain.pem`
- **Private key**: `/etc/letsencrypt/live/$DOMAIN/privkey.pem`

Verify they exist:
```bash
ls -la /etc/letsencrypt/live/$DOMAIN/
```

## Step 4: Set up auto-renewal

Certbot installs a systemd timer or cron job by default. Verify:

```bash
systemctl list-timers | grep certbot || crontab -l | grep certbot || echo "No auto-renewal found"
```

If no auto-renewal is set up:
```bash
# Add a cron job to renew twice daily (certbot only renews when close to expiry)
echo "0 3,15 * * * certbot renew --quiet --deploy-hook 'systemctl restart clawedback-server 2>/dev/null || true'" | crontab -
```

The `--deploy-hook` restarts the server after renewal so it picks up the new cert.

## Step 5: Update the server start command

Read the current CLAUDE.md to find the server start command, then update it to use SSL with the cert paths.

Find and update the server start line in CLAUDE.md:

The commands section should include:
```bash
# Start server (HTTPS with Let's Encrypt)
cd .claude/skills/oc-poll/scripts && source ../.venv/bin/activate && python main.py --public /etc/letsencrypt/live/$DOMAIN/fullchain.pem --private /etc/letsencrypt/live/$DOMAIN/privkey.pem
```

For Mode C (no venv):
```bash
cd .claude/skills/oc-poll/scripts && python3 main.py --public /etc/letsencrypt/live/$DOMAIN/fullchain.pem --private /etc/letsencrypt/live/$DOMAIN/privkey.pem
```

Also append this to the Rules section of CLAUDE.md:

```markdown

### SSL Configuration
This instance uses Let's Encrypt SSL certificates for HTTPS.
- Domain: $DOMAIN
- Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem
- Private key: /etc/letsencrypt/live/$DOMAIN/privkey.pem
- Auto-renewal: certbot renew runs automatically
- Always start the server with `--public` and `--private` flags pointing to the cert paths above.
```

## Step 6: Restart the server with SSL

Kill the existing server and restart with SSL:

```bash
# Kill existing server (pkill catches the actual process, not just the nohup wrapper)
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2

# Restart with SSL
cd $PROJECT_ROOT/.claude/skills/oc-poll/scripts
nohup python3 main.py --public /etc/letsencrypt/live/$DOMAIN/fullchain.pem --private /etc/letsencrypt/live/$DOMAIN/privkey.pem > $PROJECT_ROOT/data/logs/server.log 2>&1 &
sleep 1 && pgrep -f "python3 main.py" | tail -1 > $PROJECT_ROOT/data/server.pid
```

Verify:
```bash
sleep 2 && curl -sk https://$DOMAIN:8080/api/health
```

## Step 7: Summary

Tell the user:

```
SSL is configured!

Domain: $DOMAIN
URL: https://$DOMAIN:8080
Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem
Auto-renewal: Active (certbot renew runs automatically)

Your ClawedBack instance is now accessible via HTTPS.
CLAUDE.md has been updated to always start with SSL.
```

## Troubleshooting

**"certbot: command not found"** — install with `apt install certbot` or `snap install certbot --classic`

**"Port 80 already in use"** — stop whatever is on port 80 (`ss -tlnp | grep :80`), run certbot, then restart it. Or use `certbot certonly --webroot` if you have a web server you want to keep running.

**"Domain does not resolve"** — the DNS A record must point to this server's public IP. Check with `dig $DOMAIN` or `nslookup $DOMAIN`.

**"Permission denied"** — certbot needs root. Use Mode B or C.

**Certificate renewal failed** — check `certbot renew --dry-run` for errors. Common issue: port 80 blocked by firewall.

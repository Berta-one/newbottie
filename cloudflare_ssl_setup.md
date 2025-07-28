
# 🌐 Cloudflare DNS + SSL Setup

## Step 1: Add A Record in Cloudflare
- Name: bot
- Type: A
- Content: 139.59.133.243
- Proxy: Off (gray cloud)

## Step 2: Install Let's Encrypt
```bash
sudo apt update && sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d bot.sntax.com
```

## Step 3: Enable Auto-Renewal
```bash
sudo crontab -e
# Add:
0 3 * * * certbot renew --quiet
```

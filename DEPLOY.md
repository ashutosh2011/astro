# Deploy to Production

1. **Create `.env.production`:**
```bash
cat > .env.production << EOF
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
REDIS_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
OPENAI_API_KEY=YOUR_KEY_HERE
VITE_API_URL=https://astro.ashuj.com/api
EOF
```
Then edit `.env.production` to add your OpenAI key.

2. **Setup Caddy:**
```bash
sudo cp Caddyfile /etc/caddy/sites-available/astro
sudo systemctl reload caddy
```

3. **Deploy:**
```bash
./deploy.sh build
```

## Commands
- `./deploy.sh start` - Start
- `./deploy.sh stop` - Stop  
- `./deploy.sh logs` - View logs
- `./deploy.sh backup` - Backup DB


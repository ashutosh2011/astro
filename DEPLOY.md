# Deploy to Production

1. **Create `.env.production`:**
```bash
cat > .env.production << 'EOF'
SECRET_KEY=YOUR_32_CHAR_SECRET
JWT_SECRET_KEY=YOUR_32_CHAR_JWT_SECRET
ENCRYPTION_KEY=YOUR_32_CHAR_ENCRYPTION_KEY
POSTGRES_DB=astro_db
POSTGRES_USER=astro_user
POSTGRES_PASSWORD=YOUR_SECURE_DB_PASSWORD
REDIS_PASSWORD=YOUR_SECURE_REDIS_PASSWORD
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
VITE_API_URL=https://astro.ashuj.com/api
EOF
```
Generate secure keys: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
Then edit `.env.production` with your actual values.

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


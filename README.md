# WooMMO Web — Setup Guide A-Z

## Yeu cau
- VPS Ubuntu 20.04+, toi thieu 2GB RAM
- Docker + Docker Compose

## Buoc 1: Cai Docker
```bash
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin
```

## Buoc 2: Clone repo
```bash
git clone https://github.com/blackmmo6868/wooupload.git
cd wooupload
```

## Buoc 3: Tao file .env
```bash
cp .env.example .env
nano .env
# Sua: POSTGRES_PASSWORD, SECRET_KEY, ADMIN_PASSWORD
```

## Buoc 4: Doi port frontend tranh xung dot voi Nginx
```bash
sed -i 's/"80:80"/"8080:80"/' docker-compose.yml
```

## Buoc 5: Build va chay
```bash
docker compose up -d --build
```

## Buoc 6: Import database
```bash
cat db_backup.sql | docker compose exec -T postgres psql -U woommo woommo
```

## Buoc 7: Cai Nginx SSL
```bash
apt install nginx certbot python3-certbot-nginx -y

cat > /etc/nginx/sites-available/woommo << NGINX
server {
    listen 80;
    server_name your.domain.com;
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 500M;
        proxy_read_timeout 300s;
    }
}
NGINX

ln -s /etc/nginx/sites-available/woommo /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
certbot --nginx -d your.domain.com
```

## Buoc 8: Truy cap
- URL: https://your.domain.com
- Username: admin
- Password: Aa221122@ (neu dung db_backup.sql)

## Buoc 9: Cau hinh sau dang nhap
1. Admin > Quan ly Store - Kiem tra store da co chua
2. Admin > Cai dat - Nhap lai OpenAI API Key
3. Internal Link - Kiem tra link config

## Cac lenh hay dung
```bash
# Update code
cd ~/wooupload && git pull && docker compose up -d --build

# Backup DB va push GitHub
docker compose exec postgres pg_dump -U woommo woommo > db_backup.sql
git add db_backup.sql && git commit -m "Update DB backup" && git push

# Xem log
docker compose logs api -f
docker compose logs worker-upload -f

# Restart
docker compose restart
```

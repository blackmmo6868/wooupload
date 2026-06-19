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
cd /opt
git clone https://github.com/blackmmo6868/wooupload.git
cd wooupload
```

## Buoc 3: Tao file .env
```bash
cp .env.example .env
nano .env
# Sua: POSTGRES_PASSWORD, SECRET_KEY, ADMIN_PASSWORD
```

## Buoc 4: Build va chay
```bash
docker compose up -d --build
```

## Buoc 5: Import database
```bash
cat db_backup.sql | docker compose exec -T postgres psql -U woommo woommo
```

## Buoc 6: Cai Nginx SSL
```bash
apt install nginx certbot python3-certbot-nginx -y

ln -sf /opt/wooupload/nginx.host.conf /etc/nginx/sites-available/wooupload
ln -sf /etc/nginx/sites-available/wooupload /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d upload.diethero.shop
```

## Buoc 7: Truy cap
- URL: https://upload.diethero.shop
- Username: admin
- Password: Aa221122@ (neu dung db_backup.sql)

## Cac lenh hay dung
```bash
# Update code
cd /opt/wooupload && git pull && docker compose up -d --build

# Backup DB va push GitHub
docker compose exec postgres pg_dump -U woommo woommo > db_backup.sql
git add db_backup.sql && git commit -m "Update DB backup" && git push

# Xem log
docker compose logs api -f
docker compose logs worker-upload -f

# Restart
docker compose restart
```

## Lưu ý sau khi chạy Certbot
Certbot sẽ xóa `client_max_body_size` và `proxy_read_timeout` khỏi Nginx config.
Chạy lại lệnh này sau mỗi lần certbot renew:

```bash
sed -i 's|proxy_set_header   X-Forwarded-Proto $scheme;|proxy_set_header   X-Forwarded-Proto $scheme;\n        client_max_body_size 500M;\n        proxy_read_timeout 300s;|' /etc/nginx/sites-available/wooupload
nginx -t && systemctl reload nginx
```

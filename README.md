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

## Buoc 4: Build va chay
```bash
docker compose up -d --build
```

## Buoc 5: Truy cap
- URL: http://YOUR_SERVER_IP
- Username: admin
- Password: gia tri ADMIN_PASSWORD trong .env

## Buoc 6: Cau hinh
1. Admin > Quan ly Store → Them store WooCommerce
2. Admin > Cai dat → Nhap OpenAI API Key
3. Internal Link → Load danh muc → Luu cau hinh

## Cac lenh hay dung
```bash
# Update code
git pull && docker compose up -d --build

# Xem log
docker compose logs api -f
docker compose logs worker-upload -f

# Backup DB
docker compose exec postgres pg_dump -U woommo woommo > backup_$(date +%Y%m%d).sql

# Restore DB
cat backup.sql | docker compose exec -T postgres psql -U woommo woommo
```

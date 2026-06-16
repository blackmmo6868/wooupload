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

## Buoc 5: Import database (quan trong!)
```bash
# Tat ca data cu: users, stores, settings, link_config deu co san
cat db_backup.sql | docker compose exec -T postgres psql -U woommo woommo
```

## Buoc 6: Truy cap
- URL: http://YOUR_SERVER_IP
- Username: admin
- Password: gia tri ADMIN_PASSWORD trong db_backup (Mac dinh: Aa221122@)

## Buoc 7: Cau hinh bo sung
1. Admin > Quan ly Store → Kiem tra store da co chua
2. Admin > Cai dat → Nhap lai OpenAI API Key
3. Internal Link → Kiem tra link config

## Cac lenh hay dung
```bash
# Update code
git pull && docker compose up -d --build

# Backup DB moi nhat
docker compose exec postgres pg_dump -U woommo woommo > db_backup.sql
git add db_backup.sql && git commit -m "Update DB backup" && git push

# Xem log
docker compose logs api -f
docker compose logs worker-upload -f
```

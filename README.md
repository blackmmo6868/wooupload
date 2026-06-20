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
# Sua: GSC_PG_DSN (xem muc "GSC Index Queue" ben duoi)
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

## GSC Index Queue (tab "Submit Index")

Tab "Submit Index" trên web lưu URL vào bảng `queue` của database Postgres riêng `gsc_bot`,
để bot Telegram GSC Index (chạy trên máy Windows/VMware riêng, code `gsc_index_bot.py`) tự
pull và submit lên Google Search Console khi máy đó được bật lên.

### Hạ tầng
- Database `gsc_bot` + user `gsc_user` nằm **chung container Postgres** với app chính
  (`wooupload-postgres-1`), nhưng là database riêng biệt — không lẫn data với `woommo`.
- Port `5432` của container này đã được **expose ra ngoài** (`0.0.0.0:5432` trong
  `docker-compose.yml`, service `postgres`) để bot Windows kết nối từ xa được.
- `ufw` đã mở `5432/tcp` public. Đây là port public ra internet — nếu cần an toàn hơn,
  giới hạn lại bằng cách thêm rule UFW theo đúng IP của máy Windows/VMware thay vì
  `Anywhere`, ví dụ: `ufw delete allow 5432/tcp` rồi `ufw allow from <IP_VMware> to any port 5432`.
- Connection string nằm trong biến `GSC_PG_DSN` ở `backend/.env`:
  ```
  GSC_PG_DSN=postgresql://gsc_user:<password>@<ip_server>:5432/gsc_bot
  ```
- Trên máy Windows/VMware chạy bot, file `.env` của bot (`PG_DSN`) phải trỏ **cùng**
  connection string này (cùng user/pass/host/db) để 2 bên đọc/ghi chung 1 hàng đợi.

### Tạo lại DB/bảng nếu mất (vd sau khi recreate container Postgres)
Việc đổi `docker-compose.yml` (vd thêm `ports`) làm Docker **recreate** container —
các role/database tạo thủ công qua `psql` trước đó **sẽ mất** nếu recreate xảy ra trước
khi backup/migration được lưu lại. Kiểm tra nhanh:
```bash
docker exec -it wooupload-postgres-1 psql -U woommo -d woommo -c "\du"   # check user gsc_user còn không
docker exec -it wooupload-postgres-1 psql -U woommo -d woommo -l        # check database gsc_bot còn không
```
Nếu mất, tạo lại:
```bash
docker exec -it wooupload-postgres-1 psql -U woommo -d woommo -c "CREATE USER gsc_user WITH PASSWORD '<password>';"
docker exec -it wooupload-postgres-1 psql -U woommo -d woommo -c "CREATE DATABASE gsc_bot OWNER gsc_user;"
docker exec -it wooupload-postgres-1 psql -U gsc_user -d gsc_bot -c "
CREATE TABLE IF NOT EXISTS queue (
    id SERIAL PRIMARY KEY, site_id TEXT NOT NULL DEFAULT 'default', url TEXT NOT NULL,
    priority INTEGER DEFAULT 0, status TEXT DEFAULT 'pending', result TEXT,
    retry_count INTEGER DEFAULT 0, added_at TIMESTAMP DEFAULT NOW(), processed_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS daily_count (
    site_id TEXT NOT NULL DEFAULT 'default', day DATE NOT NULL, count INTEGER DEFAULT 0,
    PRIMARY KEY (site_id, day)
);
CREATE TABLE IF NOT EXISTS indexed_history (
    site_id TEXT NOT NULL DEFAULT 'default', url TEXT NOT NULL, indexed_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (site_id, url)
);
"
```
(Bot Windows cũng tự tạo các bảng này khi khởi động lần đầu, nhờ `init_db()` trong
`gsc_index_bot.py` — nên nếu bot start trước, không cần chạy tay đoạn trên.)

### Cơ chế site_id
`site_id` được **tự động suy ra** từ domain của URL submit, không cần cấu hình tay:
`https://printedaura.com/product/abc/` → `site_id = sc-domain:printedaura.com`.
Vậy cùng 1 tab Submit Index dùng được cho mọi store (breaktees, printedaura, ontoptee...),
miễn URL dán vào đúng domain tương ứng.

### Cơ chế check trùng (chống submit lại link đã xong)
Một URL bị **bỏ qua** (không add lại vào `queue`) nếu:
- Đã có trong `indexed_history` (Google đã index thành công), hoặc
- Đang `pending` hoặc đã `done` trong `queue` (đang chờ xử lý hoặc đã xử lý xong)

URL có status `failed` (lỗi sau khi bot đã thử hết `MAX_RETRIES` lần) **vẫn được add lại**
bình thường để bot thử submit lại.

### Code liên quan
- Backend route: `backend/app/routers/gsc.py`
- Frontend tab: `frontend/src/pages/SubmitIndexPage.jsx`
- Bot Windows: file riêng `gsc_index_bot.py` (không nằm trong repo này, chạy trên máy VMware)

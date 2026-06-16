--
-- PostgreSQL database dump
--

\restrict JjzAK0R8wIqDdJWtMx05yWG4j5SnH4IP2F7ujYftObsiYpJn4JU6gqh8rfILufC

-- Dumped from database version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: woommo
--

CREATE TABLE public.jobs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    job_type character varying(32) NOT NULL,
    status character varying(32),
    celery_id character varying(255),
    params json,
    result json,
    log text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.jobs OWNER TO woommo;

--
-- Name: jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: woommo
--

CREATE SEQUENCE public.jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.jobs_id_seq OWNER TO woommo;

--
-- Name: jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: woommo
--

ALTER SEQUENCE public.jobs_id_seq OWNED BY public.jobs.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: woommo
--

CREATE TABLE public.settings (
    id integer NOT NULL,
    key character varying(128) NOT NULL,
    value text
);


ALTER TABLE public.settings OWNER TO woommo;

--
-- Name: settings_id_seq; Type: SEQUENCE; Schema: public; Owner: woommo
--

CREATE SEQUENCE public.settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.settings_id_seq OWNER TO woommo;

--
-- Name: settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: woommo
--

ALTER SEQUENCE public.settings_id_seq OWNED BY public.settings.id;


--
-- Name: stores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.stores (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    wc_url character varying(255) NOT NULL,
    wp_username character varying(255) DEFAULT ''::character varying,
    wp_app_password character varying(255) DEFAULT ''::character varying,
    store_name character varying(255) DEFAULT ''::character varying,
    shortcode character varying(255) DEFAULT '[thien_display_single_image]'::character varying,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.stores OWNER TO postgres;

--
-- Name: stores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.stores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stores_id_seq OWNER TO postgres;

--
-- Name: stores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.stores_id_seq OWNED BY public.stores.id;


--
-- Name: user_stores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_stores (
    id integer NOT NULL,
    user_id integer NOT NULL,
    store_id integer NOT NULL,
    wp_username character varying(255) DEFAULT ''::character varying,
    wp_app_password character varying(255) DEFAULT ''::character varying,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.user_stores OWNER TO postgres;

--
-- Name: user_stores_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_stores_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_stores_id_seq OWNER TO postgres;

--
-- Name: user_stores_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_stores_id_seq OWNED BY public.user_stores.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: woommo
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(255) NOT NULL,
    hashed_pw character varying(255) NOT NULL,
    is_admin boolean,
    is_active boolean,
    created_at timestamp without time zone,
    wp_username character varying(255) DEFAULT ''::character varying,
    wp_app_password character varying(255) DEFAULT ''::character varying,
    store_id integer,
    note text DEFAULT ''::text
);


ALTER TABLE public.users OWNER TO woommo;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: woommo
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO woommo;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: woommo
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: jobs id; Type: DEFAULT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.jobs ALTER COLUMN id SET DEFAULT nextval('public.jobs_id_seq'::regclass);


--
-- Name: settings id; Type: DEFAULT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.settings ALTER COLUMN id SET DEFAULT nextval('public.settings_id_seq'::regclass);


--
-- Name: stores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stores ALTER COLUMN id SET DEFAULT nextval('public.stores_id_seq'::regclass);


--
-- Name: user_stores id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_stores ALTER COLUMN id SET DEFAULT nextval('public.user_stores_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: woommo
--

COPY public.jobs (id, user_id, job_type, status, celery_id, params, result, log, created_at, updated_at) FROM stdin;
1515	3	seo	done	\N	{"product_ids": [21923, 21926, 21929], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 3, "done": 3, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: Panama National Team 2026 Hoodie Red...\n✓ Description done (4570 chars)\n🤖 Generating snippet: Panama National Team 2026 Hoodie Red...\n✓ Snippet done (156 chars)\n📡 Updating WooCommerce #21929...\n✅ Done: Panama National Team 2026 Hoodie Red (est. score ~85)\n✅ [1/3] Done: Panama National Team 2026 Hoodie Red\n🤖 Generating description: Panama National Team 2026 Hoodie Blue...\n✓ Description done (5042 chars)\n🤖 Generating snippet: Panama National Team 2026 Hoodie Blue...\n✓ Snippet done (144 chars)\n📡 Updating WooCommerce #21926...\n✅ Done: Panama National Team 2026 Hoodie Blue (est. score ~85)\n✅ [2/3] Done: Panama National Team 2026 Hoodie Blue\n🤖 Generating description: Panama National Team 2026 Hoodie...\n✓ Description done (4604 chars)\n🤖 Generating snippet: Panama National Team 2026 Hoodie...\n✓ Snippet done (153 chars)\n📡 Updating WooCommerce #21923...\n✅ Done: Panama National Team 2026 Hoodie (est. score ~85)\n✅ [3/3] Done: Panama National Team 2026 Hoodie\n✅ SEO hoàn thành: 3/3 sản phẩm\n🌐 Auto publish 3 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:44:09.891546	2026-06-16 08:45:56.524088
1517	3	seo	done	\N	{"product_ids": [21932, 21935], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 2, "done": 2, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: Adirondack Thunder Threads 2026 Custom Hockey Jersey...\n✓ Description done (5010 chars)\n🤖 Generating snippet: Adirondack Thunder Threads 2026 Custom Hockey Jersey...\n✓ Snippet done (149 chars)\n📡 Updating WooCommerce #21935...\n✅ Done: Adirondack Thunder Threads 2026 Custom Hockey Jersey (est. score ~85)\n✅ [1/2] Done: Adirondack Thunder Threads 2026 Custom Hockey Jersey\n🤖 Generating description: Adirondack Thunder From The Woods To The Ice Custom Hockey Jersey...\n✓ Description done (4972 chars)\n🤖 Generating snippet: Adirondack Thunder From The Woods To The Ice Custom Hockey Jersey...\n✓ Snippet done (148 chars)\n📡 Updating WooCommerce #21932...\n✅ Done: Adirondack Thunder From The Woods To The Ice Custom Hockey Jersey (est. score ~85)\n✅ [2/2] Done: Adirondack Thunder From The Woods To The Ice Custom Hockey Jersey\n✅ SEO hoàn thành: 2/2 sản phẩm\n🌐 Auto publish 2 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:49:58.401396	2026-06-16 08:51:02.712712
1507	3	upload	done	\N	{"filename": "2  - T - Shirt.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 3, "successful": 3, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Louisville Kings New Era 2026 Champions Shirt", "url": "https://printedaura.com/product/louisville-kings-new-era-2026-champions-shirt/", "id": 21899}, {"title": "Panama National Team 2026 Shirt", "url": "https://printedaura.com/product/panama-national-team-2026-shirt/", "id": 21902}, {"title": "San Francisco Giants Jesus Won Shirt", "url": "https://printedaura.com/product/san-francisco-giants-jesus-won-shirt/", "id": 21906}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 930 (10 trang)\n✅ Đã tải 930 sản phẩm — bắt đầu upload...\n[1/3] Đang upload: Louisville Kings New Era 2026 Champions Shirt\n[2/3] Đang upload: Panama National Team 2026 Shirt\n[3/3] Đang upload: San Francisco Giants Jesus Won Shirt\nHoàn thành!\n⭐ Set primary category ID=132...\n⭐ Primary category: 3 OK, 0 lỗi\n⭐ Set primary category ID=132...\n⭐ Primary category: 3 OK, 0 lỗi\n✅ Hoàn thành: 3/3 SP\n🤖 Auto SEO job đã vào hàng đợi (3 SP)\n	2026-06-16 08:29:47.676739	2026-06-16 08:31:00.478281
1516	3	upload	done	\N	{"filename": "6 - Hockey Jersey.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 2, "successful": 2, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Adirondack Thunder From The Woods To The Ice Custom Hockey Jersey", "url": "https://printedaura.com/product/adirondack-thunder-from-the-woods-to-the-ice-custom-hockey-jersey/", "id": 21932}, {"title": "Adirondack Thunder Threads 2026 Custom Hockey Jersey", "url": "https://printedaura.com/product/adirondack-thunder-threads-2026-custom-hockey-jersey/", "id": 21935}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 942 (10 trang)\n✅ Đã tải 942 sản phẩm — bắt đầu upload...\n[1/2] Đang upload: Adirondack Thunder From The Woods To The Ice Custom Hockey Jersey\n[2/2] Đang upload: Adirondack Thunder Threads 2026 Custom Hockey Jersey\nHoàn thành!\n⭐ Set primary category ID=127...\n⭐ Primary category: 2 OK, 0 lỗi\n⭐ Set primary category ID=127...\n⭐ Primary category: 2 OK, 0 lỗi\n✅ Hoàn thành: 2/2 SP\n🤖 Auto SEO job đã vào hàng đợi (2 SP)\n	2026-06-16 08:49:20.5174	2026-06-16 08:49:58.388876
1508	1	upload	done	\N	{"filename": "test printedaura.rar", "uploader": "admin", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 1, "successful": 1, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Simple Plan Bigger Than You Think Tour Air Force 1 Shoes", "url": "https://printedaura.com/product/simple-plan-bigger-than-you-think-tour-air-force-1-shoes/", "id": 21908}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nDang xu ly anh (nen + metadata)...\n============================================================\n🚀 Bắt đầu xử lý ảnh...\n============================================================\n\n📁 Simple Plan Bigger Than You Think Tour Air Force 1 Shoes\n  ── Compress + Metadata ──\n  ✓ Simple-Plan-Bigger-Than-You-Think-Tour-Air-Force-1-Shoes-2.jpg  (↓8.2%)\n============================================================\n✅ Xử lý ảnh xong — 1 file, 0 lỗi\n============================================================\nXu ly anh xong: 1 file, 0 loi\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 933 (10 trang)\n✅ Đã tải 933 sản phẩm — bắt đầu upload...\n[1/1] Đang upload: Simple Plan Bigger Than You Think Tour Air Force 1 Shoes\nHoàn thành!\n⭐ Set primary category ID=3011...\n⭐ Primary category: 1 OK, 0 lỗi\n⭐ Set primary category ID=3011...\n⭐ Primary category: 1 OK, 0 lỗi\n✅ Hoàn thành: 1/1 SP\n	2026-06-16 08:30:37.954631	2026-06-16 08:31:29.724072
1518	3	upload	done	\N	{"filename": "7  - Football Jersey.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 5, "successful": 5, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Collingwood Football Club 2026 Personalized Home Guernsey", "url": "https://printedaura.com/product/collingwood-football-club-2026-personalized-home-guernsey/", "id": 21937}, {"title": "Fremantle Football Club 2026 Personalized Home Guernsey", "url": "https://printedaura.com/product/fremantle-football-club-2026-personalized-home-guernsey/", "id": 21939}, {"title": "Geelong Cats 2026 Personalized Home Guernsey", "url": "https://printedaura.com/product/geelong-cats-2026-personalized-home-guernsey/", "id": 21941}, {"title": "Hawthorn Hawks 2026 Personalized Home Guernsey", "url": "https://printedaura.com/product/hawthorn-hawks-2026-personalized-home-guernsey/", "id": 21943}, {"title": "Sydney Swans 2026 Personalized Home Guernsey", "url": "https://printedaura.com/product/sydney-swans-2026-personalized-home-guernsey/", "id": 21945}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 944 (10 trang)\n✅ Đã tải 944 sản phẩm — bắt đầu upload...\n[1/5] Đang upload: Collingwood Football Club 2026 Personalized Home Guernsey\n[2/5] Đang upload: Fremantle Football Club 2026 Personalized Home Guernsey\n[3/5] Đang upload: Geelong Cats 2026 Personalized Home Guernsey\n[4/5] Đang upload: Hawthorn Hawks 2026 Personalized Home Guernsey\n[5/5] Đang upload: Sydney Swans 2026 Personalized Home Guernsey\nHoàn thành!\n⭐ Set primary category ID=3012...\n⭐ Primary category: 5 OK, 0 lỗi\n⭐ Set primary category ID=3012...\n⭐ Primary category: 5 OK, 0 lỗi\n✅ Hoàn thành: 5/5 SP\n🤖 Auto SEO job đã vào hàng đợi (5 SP)\n	2026-06-16 08:58:49.837436	2026-06-16 08:59:55.283019
1509	3	seo	done	\N	{"product_ids": [21899, 21902, 21906], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 3, "done": 3, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: San Francisco Giants Jesus Won Shirt...\n✓ Description done (4789 chars)\n🤖 Generating snippet: San Francisco Giants Jesus Won Shirt...\n✓ Snippet done (150 chars)\n📡 Updating WooCommerce #21906...\n✅ Done: San Francisco Giants Jesus Won Shirt (est. score ~85)\n✅ [1/3] Done: San Francisco Giants Jesus Won Shirt\n🤖 Generating description: Panama National Team 2026 Shirt...\n✓ Description done (4611 chars)\n🤖 Generating snippet: Panama National Team 2026 Shirt...\n✓ Snippet done (148 chars)\n📡 Updating WooCommerce #21902...\n✅ Done: Panama National Team 2026 Shirt (est. score ~85)\n✅ [2/3] Done: Panama National Team 2026 Shirt\n🤖 Generating description: Louisville Kings New Era 2026 Champions Shirt...\n✓ Description done (5231 chars)\n🤖 Generating snippet: Louisville Kings New Era 2026 Champions Shirt...\n✓ Snippet done (154 chars)\n📡 Updating WooCommerce #21899...\n✅ Done: Louisville Kings New Era 2026 Champions Shirt (est. score ~85)\n✅ [3/3] Done: Louisville Kings New Era 2026 Champions Shirt\n✅ SEO hoàn thành: 3/3 sản phẩm\n🌐 Auto publish 3 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:31:00.486643	2026-06-16 08:33:38.245789
1519	3	seo	done	\N	{"product_ids": [21937, 21939, 21941, 21943, 21945], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 5, "done": 5, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: Sydney Swans 2026 Personalized Home Guernsey...\n✓ Description done (4223 chars)\n🤖 Generating snippet: Sydney Swans 2026 Personalized Home Guernsey...\n✓ Snippet done (142 chars)\n📡 Updating WooCommerce #21945...\n✅ Done: Sydney Swans 2026 Personalized Home Guernsey (est. score ~85)\n✅ [1/5] Done: Sydney Swans 2026 Personalized Home Guernsey\n🤖 Generating description: Hawthorn Hawks 2026 Personalized Home Guernsey...\n✓ Description done (5259 chars)\n🤖 Generating snippet: Hawthorn Hawks 2026 Personalized Home Guernsey...\n✓ Snippet done (146 chars)\n📡 Updating WooCommerce #21943...\n✅ Done: Hawthorn Hawks 2026 Personalized Home Guernsey (est. score ~85)\n✅ [2/5] Done: Hawthorn Hawks 2026 Personalized Home Guernsey\n🤖 Generating description: Geelong Cats 2026 Personalized Home Guernsey...\n✓ Description done (5185 chars)\n🤖 Generating snippet: Geelong Cats 2026 Personalized Home Guernsey...\n✓ Snippet done (150 chars)\n📡 Updating WooCommerce #21941...\n✅ Done: Geelong Cats 2026 Personalized Home Guernsey (est. score ~85)\n✅ [3/5] Done: Geelong Cats 2026 Personalized Home Guernsey\n🤖 Generating description: Fremantle Football Club 2026 Personalized Home Guernsey...\n✓ Description done (4686 chars)\n🤖 Generating snippet: Fremantle Football Club 2026 Personalized Home Guernsey...\n✓ Snippet done (146 chars)\n📡 Updating WooCommerce #21939...\n✅ Done: Fremantle Football Club 2026 Personalized Home Guernsey (est. score ~85)\n✅ [4/5] Done: Fremantle Football Club 2026 Personalized Home Guernsey\n🤖 Generating description: Collingwood Football Club 2026 Personalized Home Guernsey...\n✓ Description done (4983 chars)\n🤖 Generating snippet: Collingwood Football Club 2026 Personalized Home Guernsey...\n✓ Snippet done (154 chars)\n📡 Updating WooCommerce #21937...\n✅ Done: Collingwood Football Club 2026 Personalized Home Guernsey (est. score ~85)\n✅ [5/5] Done: Collingwood Football Club 2026 Personalized Home Guernsey\n✅ SEO hoàn thành: 5/5 sản phẩm\n🌐 Auto publish 5 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:59:55.290155	2026-06-16 09:04:14.023584
1510	3	upload	done	\N	{"filename": "3  - Air Force 1 Shoes.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 5, "successful": 5, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Ariana Grande Petal 2026 Edition Air Force 1", "url": "https://printedaura.com/product/ariana-grande-petal-2026-edition-air-force-1/", "id": 21910}, {"title": "Ariana Grande The Eternal Sunshine Tour 2026 Custom AF1 Sneaker", "url": "https://printedaura.com/product/ariana-grande-the-eternal-sunshine-tour-2026-custom-af1-sneaker/", "id": 21912}, {"title": "Geelong Cats Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/geelong-cats-custom-air-force-1-shoes/", "id": 21914}, {"title": "Hawthorn Hawks Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/hawthorn-hawks-custom-air-force-1-shoes/", "id": 21916}, {"title": "New York Knicks Special New 2026 Air Force 1 Shoes", "url": "https://printedaura.com/product/new-york-knicks-special-new-2026-air-force-1-shoes/", "id": 21918}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 933 (10 trang)\n✅ Đã tải 933 sản phẩm — bắt đầu upload...\n[1/5] Đang upload: Ariana Grande Petal 2026 Edition Air Force 1\n[2/5] Đang upload: Ariana Grande The Eternal Sunshine Tour 2026 Custom AF1 Sneaker\n[3/5] Đang upload: Geelong Cats Custom Air Force 1 Shoes\n[4/5] Đang upload: Hawthorn Hawks Custom Air Force 1 Shoes\n[5/5] Đang upload: New York Knicks Special New 2026 Air Force 1 Shoes\nHoàn thành!\n⭐ Set primary category ID=3011...\n⭐ Primary category: 5 OK, 0 lỗi\n⭐ Set primary category ID=3011...\n⭐ Primary category: 5 OK, 0 lỗi\n✅ Hoàn thành: 5/5 SP\n🤖 Auto SEO job đã vào hàng đợi (5 SP)\n	2026-06-16 08:35:40.596889	2026-06-16 08:36:41.990791
1520	3	upload	done	\N	{"filename": "8  -Polo Shirt.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 3, "successful": 2, "failed": 1, "skipped": 0, "errors": [{"product": "Panama National Team 2026 White Polo Shirt", "error": "500 Server Error: Internal Server Error for url: https://printedaura.com/wp-json/wp/v2/media"}], "retried_ok": [], "product_urls": [{"title": "Panama National Team 2026 Blue Polo Shirt", "url": "https://printedaura.com/product/panama-national-team-2026-blue-polo-shirt/", "id": 21948}, {"title": "Panama National Team 2026 Red Polo Shirt", "url": "https://printedaura.com/product/panama-national-team-2026-red-polo-shirt/", "id": 21951}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 949 (10 trang)\n✅ Đã tải 949 sản phẩm — bắt đầu upload...\n[1/3] Đang upload: Panama National Team 2026 Blue Polo Shirt\n[2/3] Đang upload: Panama National Team 2026 Red Polo Shirt\n[3/3] Đang upload: Panama National Team 2026 White Polo Shirt\nHoàn thành!\n⭐ Set primary category ID=3021...\n⭐ Primary category: 0 OK, 2 lỗi\n⚠️ 1 SP lỗi, retry sau 10s...\n⭐ Set primary category ID=3021...\n⭐ Primary category: 0 OK, 2 lỗi\n✅ Hoàn thành: 2/3 SP\n🤖 Auto SEO job đã vào hàng đợi (2 SP)\n	2026-06-16 09:05:05.411359	2026-06-16 09:06:08.78502
1521	3	seo	done	\N	{"product_ids": [21948, 21951], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 0, "done": 0, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n✅ SEO hoàn thành: 0/0 sản phẩm\n🌐 Auto publish 2 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 09:06:08.796797	2026-06-16 09:06:09.244321
1511	3	seo	done	\N	{"product_ids": [21910, 21912, 21914, 21916, 21918], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 5, "done": 5, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: New York Knicks Special New 2026 Air Force 1 Shoes...\n✓ Description done (4609 chars)\n🤖 Generating snippet: New York Knicks Special New 2026 Air Force 1 Shoes...\n✓ Snippet done (142 chars)\n📡 Updating WooCommerce #21918...\n✅ Done: New York Knicks Special New 2026 Air Force 1 Shoes (est. score ~85)\n✅ [1/5] Done: New York Knicks Special New 2026 Air Force 1 Shoes\n🤖 Generating description: Hawthorn Hawks Custom Air Force 1 Shoes...\n✓ Description done (4382 chars)\n🤖 Generating snippet: Hawthorn Hawks Custom Air Force 1 Shoes...\n✓ Snippet done (146 chars)\n📡 Updating WooCommerce #21916...\n✅ Done: Hawthorn Hawks Custom Air Force 1 Shoes (est. score ~85)\n✅ [2/5] Done: Hawthorn Hawks Custom Air Force 1 Shoes\n🤖 Generating description: Geelong Cats Custom Air Force 1 Shoes...\n✓ Description done (5086 chars)\n🤖 Generating snippet: Geelong Cats Custom Air Force 1 Shoes...\n✓ Snippet done (142 chars)\n📡 Updating WooCommerce #21914...\n✅ Done: Geelong Cats Custom Air Force 1 Shoes (est. score ~85)\n✅ [3/5] Done: Geelong Cats Custom Air Force 1 Shoes\n🤖 Generating description: Ariana Grande The Eternal Sunshine Tour 2026 Custom AF1 Sneaker...\n✓ Description done (4700 chars)\n🤖 Generating snippet: Ariana Grande The Eternal Sunshine Tour 2026 Custom AF1 Sneaker...\n✓ Snippet done (154 chars)\n📡 Updating WooCommerce #21912...\n✅ Done: Ariana Grande The Eternal Sunshine Tour 2026 Custom AF1 Sneaker (est. score ~85)\n✅ [4/5] Done: Ariana Grande The Eternal Sunshine Tour 2026 Custom AF1 Sneaker\n🤖 Generating description: Ariana Grande Petal 2026 Edition Air Force 1...\n✓ Description done (4613 chars)\n🤖 Generating snippet: Ariana Grande Petal 2026 Edition Air Force 1...\n✓ Snippet done (142 chars)\n📡 Updating WooCommerce #21910...\n✅ Done: Ariana Grande Petal 2026 Edition Air Force 1 (est. score ~85)\n✅ [5/5] Done: Ariana Grande Petal 2026 Edition Air Force 1\n✅ SEO hoàn thành: 5/5 sản phẩm\n🌐 Auto publish 5 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:36:41.997256	2026-06-16 08:38:39.479421
1514	3	upload	done	\N	{"filename": "5  Hoodie.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 3, "successful": 3, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Panama National Team 2026 Hoodie", "url": "https://printedaura.com/product/panama-national-team-2026-hoodie/", "id": 21923}, {"title": "Panama National Team 2026 Hoodie Blue", "url": "https://printedaura.com/product/panama-national-team-2026-hoodie-blue/", "id": 21926}, {"title": "Panama National Team 2026 Hoodie Red", "url": "https://printedaura.com/product/panama-national-team-2026-hoodie-red/", "id": 21929}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 939 (10 trang)\n✅ Đã tải 939 sản phẩm — bắt đầu upload...\n[1/3] Đang upload: Panama National Team 2026 Hoodie\n[2/3] Đang upload: Panama National Team 2026 Hoodie Blue\n[3/3] Đang upload: Panama National Team 2026 Hoodie Red\nHoàn thành!\n⭐ Set primary category ID=133...\n⭐ Primary category: 3 OK, 0 lỗi\n⭐ Set primary category ID=133...\n⭐ Primary category: 3 OK, 0 lỗi\n✅ Hoàn thành: 3/3 SP\n🤖 Auto SEO job đã vào hàng đợi (3 SP)\n	2026-06-16 08:43:06.806203	2026-06-16 08:44:09.883663
1512	3	upload	done	\N	{"filename": "4  - Air Jodan 1.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 1, "successful": 1, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Ariana Grande Petal 2026 Edition Air Jordan 1", "url": "https://printedaura.com/product/ariana-grande-petal-2026-edition-air-jordan-1/", "id": 21920}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 938 (10 trang)\n✅ Đã tải 938 sản phẩm — bắt đầu upload...\n[1/1] Đang upload: Ariana Grande Petal 2026 Edition Air Jordan 1\nHoàn thành!\n⭐ Set primary category ID=3007...\n⭐ Primary category: 1 OK, 0 lỗi\n⭐ Set primary category ID=3007...\n⭐ Primary category: 1 OK, 0 lỗi\n✅ Hoàn thành: 1/1 SP\n🤖 Auto SEO job đã vào hàng đợi (1 SP)\n	2026-06-16 08:38:48.282298	2026-06-16 08:39:15.373901
1513	3	seo	done	\N	{"product_ids": [21920], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 1, "done": 1, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: Ariana Grande Petal 2026 Edition Air Jordan 1...\n✓ Description done (4936 chars)\n🤖 Generating snippet: Ariana Grande Petal 2026 Edition Air Jordan 1...\n✓ Snippet done (146 chars)\n📡 Updating WooCommerce #21920...\n✅ Done: Ariana Grande Petal 2026 Edition Air Jordan 1 (est. score ~85)\n✅ [1/1] Done: Ariana Grande Petal 2026 Edition Air Jordan 1\n✅ SEO hoàn thành: 1/1 sản phẩm\n🌐 Auto publish 1 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:39:15.38119	2026-06-16 08:39:57.783408
1505	3	seo	done	\N	{"product_ids": [21882, 21885, 21887, 21889, 21891, 21893, 21895, 21897], "uploader": "auto-pipeline", "auto_publish": true, "wc_url": "https://printedaura.com", "wc_username": "seller.mhung", "wc_app_password": "V5Pc hGXg 6PaO BOm6 TDwi R7I6", "store_id": 3}	{"total": 8, "done": 8, "failed": 0, "skipped": 0, "errors": []}	🤖 Khởi động SEO generator...\n🏪 Store name: PrintedAura\n📦 Đang lấy danh sách sản phẩm từ WooCommerce...\n🤖 Generating description: San Diego Padres x Ninja Turtles x Demon Slayer Limited Jersey...\n✓ Description done (5059 chars)\n🤖 Generating snippet: San Diego Padres x Ninja Turtles x Demon Slayer Limited Jersey...\n✓ Snippet done (152 chars)\n📡 Updating WooCommerce #21897...\n✅ Done: San Diego Padres x Ninja Turtles x Demon Slayer Limited Jersey (est. score ~85)\n✅ [1/8] Done: San Diego Padres x Ninja Turtles x Demon Slayer Limited Jersey\n🤖 Generating description: Norfolk Tides Pride Night 2026 Custom Jersey...\n✓ Description done (5322 chars)\n🤖 Generating snippet: Norfolk Tides Pride Night 2026 Custom Jersey...\n✓ Snippet done (144 chars)\n📡 Updating WooCommerce #21895...\n✅ Done: Norfolk Tides Pride Night 2026 Custom Jersey (est. score ~85)\n✅ [2/8] Done: Norfolk Tides Pride Night 2026 Custom Jersey\n🤖 Generating description: LADodgers x Hoppers Movie Limited Baseball Jersey...\n✓ Description done (4958 chars)\n🤖 Generating snippet: LADodgers x Hoppers Movie Limited Baseball Jersey...\n✓ Snippet done (148 chars)\n📡 Updating WooCommerce #21893...\n✅ Done: LADodgers x Hoppers Movie Limited Baseball Jersey (est. score ~85)\n✅ [3/8] Done: LADodgers x Hoppers Movie Limited Baseball Jersey\n🤖 Generating description: LA Dodgers x Super Mario Baseball Jersey...\n✓ Description done (4619 chars)\n🤖 Generating snippet: LA Dodgers x Super Mario Baseball Jersey...\n✓ Snippet done (140 chars)\n📡 Updating WooCommerce #21891...\n✅ Done: LA Dodgers x Super Mario Baseball Jersey (est. score ~85)\n✅ [4/8] Done: LA Dodgers x Super Mario Baseball Jersey\n🤖 Generating description: Boston Red Sox x Toy Story Special Jersey...\n✓ Description done (5424 chars)\n🤖 Generating snippet: Boston Red Sox x Toy Story Special Jersey...\n✓ Snippet done (148 chars)\n📡 Updating WooCommerce #21889...\n✅ Done: Boston Red Sox x Toy Story Special Jersey (est. score ~85)\n✅ [5/8] Done: Boston Red Sox x Toy Story Special Jersey\n🤖 Generating description: Boston Red Sox USA 250th Anniversary Special Baseballl Jersey...\n✓ Description done (5020 chars)\n🤖 Generating snippet: Boston Red Sox USA 250th Anniversary Special Baseballl Jersey...\n✓ Snippet done (147 chars)\n📡 Updating WooCommerce #21887...\n✅ Done: Boston Red Sox USA 250th Anniversary Special Baseballl Jersey (est. score ~80)\n✅ [6/8] Done: Boston Red Sox USA 250th Anniversary Special Baseballl Jersey\n🤖 Generating description: Boston Red Sox 2026 Haitian Heritage Celebration Night Custom Baseballl Jersey...\n✓ Description done (4792 chars)\n🤖 Generating snippet: Boston Red Sox 2026 Haitian Heritage Celebration Night Custom Baseballl Jersey...\n✓ Snippet done (155 chars)\n📡 Updating WooCommerce #21885...\n✅ Done: Boston Red Sox 2026 Haitian Heritage Celebration Night Custom Baseballl Jersey (est. score ~80)\n✅ [7/8] Done: Boston Red Sox 2026 Haitian Heritage Celebration Night Custom Baseballl Jersey\n🤖 Generating description: Boston Red Sox 2026 AAPI Heritage Night Special Baseballl Jersey...\n✓ Description done (5232 chars)\n🤖 Generating snippet: Boston Red Sox 2026 AAPI Heritage Night Special Baseballl Jersey...\n✓ Snippet done (146 chars)\n📡 Updating WooCommerce #21882...\n✅ Done: Boston Red Sox 2026 AAPI Heritage Night Special Baseballl Jersey (est. score ~80)\n✅ [8/8] Done: Boston Red Sox 2026 AAPI Heritage Night Special Baseballl Jersey\n✅ SEO hoàn thành: 8/8 sản phẩm\n🌐 Auto publish 8 SP...\n✅ Đã publish tất cả SP\n	2026-06-16 08:25:27.018385	2026-06-16 08:29:29.01374
1504	3	upload	done	\N	{"filename": "1  - Baseball Jersey.rar", "uploader": "seller.mhung", "store_id": 3, "store_url": "https://printedaura.com"}	{"total": 8, "successful": 8, "failed": 0, "skipped": 0, "errors": [], "retried_ok": [], "product_urls": [{"title": "Boston Red Sox 2026 AAPI Heritage Night Special Baseballl Jersey", "url": "https://printedaura.com/product/boston-red-sox-2026-aapi-heritage-night-special-baseballl-jersey/", "id": 21882}, {"title": "Boston Red Sox 2026 Haitian Heritage Celebration Night Custom Baseballl Jersey", "url": "https://printedaura.com/product/boston-red-sox-2026-haitian-heritage-celebration-night-custom-baseballl-jersey/", "id": 21885}, {"title": "Boston Red Sox USA 250th Anniversary Special Baseballl Jersey", "url": "https://printedaura.com/product/boston-red-sox-usa-250th-anniversary-special-baseballl-jersey/", "id": 21887}, {"title": "Boston Red Sox x Toy Story Special Jersey", "url": "https://printedaura.com/product/boston-red-sox-x-toy-story-special-jersey/", "id": 21889}, {"title": "LA Dodgers x Super Mario Baseball Jersey", "url": "https://printedaura.com/product/la-dodgers-x-super-mario-baseball-jersey/", "id": 21891}, {"title": "LADodgers x Hoppers Movie Limited Baseball Jersey", "url": "https://printedaura.com/product/ladodgers-x-hoppers-movie-limited-baseball-jersey/", "id": 21893}, {"title": "Norfolk Tides Pride Night 2026 Custom Jersey", "url": "https://printedaura.com/product/norfolk-tides-pride-night-2026-custom-jersey/", "id": 21895}, {"title": "San Diego Padres x Ninja Turtles x Demon Slayer Limited Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-ninja-turtles-x-demon-slayer-limited-jersey/", "id": 21897}]}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 922 (10 trang)\n✅ Đã tải 922 sản phẩm — bắt đầu upload...\n[1/8] Đang upload: Boston Red Sox 2026 AAPI Heritage Night Special Baseballl Jersey\n[2/8] Đang upload: Boston Red Sox 2026 Haitian Heritage Celebration Night Custom Baseballl Jersey\n[3/8] Đang upload: Boston Red Sox USA 250th Anniversary Special Baseballl Jersey\n[4/8] Đang upload: Boston Red Sox x Toy Story Special Jersey\n[5/8] Đang upload: LA Dodgers x Super Mario Baseball Jersey\n[6/8] Đang upload: LADodgers x Hoppers Movie Limited Baseball Jersey\n[7/8] Đang upload: Norfolk Tides Pride Night 2026 Custom Jersey\n[8/8] Đang upload: San Diego Padres x Ninja Turtles x Demon Slayer Limited Jersey\nHoàn thành!\n⭐ Set primary category ID=3010...\n⭐ Primary category: 8 OK, 0 lỗi\n⭐ Set primary category ID=3010...\n⭐ Primary category: 8 OK, 0 lỗi\n✅ Hoàn thành: 8/8 SP\n🤖 Auto SEO job đã vào hàng đợi (8 SP)\n	2026-06-16 08:23:31.1492	2026-06-16 08:25:27.006504
1506	1	upload	done	\N	{"filename": "test printedaura.rar", "uploader": "admin", "store_id": 1, "store_url": "https://breaktees.com"}	{"total": 1, "successful": 1, "failed": 0, "skipped": 1, "errors": [{"product": "Simple Plan Bigger Than You Think Tour Air Force 1 Shoes", "error": "\\u26a0 Tr\\u00f9ng slug: 'simple-plan-bigger-than-you-think-tour-air-force-1-shoes' \\u2014 \\u0111\\u00e3 b\\u1ecf qua"}], "retried_ok": ["Simple Plan Bigger Than You Think Tour Air Force 1 Shoes"], "product_urls": []}	🚀 Bắt đầu upload...\nĐang giải nén ZIP...\nDang xu ly anh (nen + metadata)...\n============================================================\n🚀 Bắt đầu xử lý ảnh...\n============================================================\n\n📁 Simple Plan Bigger Than You Think Tour Air Force 1 Shoes\n  ── Compress + Metadata ──\n  ✓ Simple-Plan-Bigger-Than-You-Think-Tour-Air-Force-1-Shoes-2.jpg  (↓8.2%)\n============================================================\n✅ Xử lý ảnh xong — 1 file, 0 lỗi\n============================================================\nXu ly anh xong: 1 file, 0 loi\nĐang phân tích cấu trúc folder...\n🔍 Đang tải danh sách sản phẩm hiện có...\n  📦 Tổng sản phẩm hiện có: 4853 (49 trang)\n✅ Đã tải 4853 sản phẩm — bắt đầu upload...\n[1/1] Đang upload: Simple Plan Bigger Than You Think Tour Air Force 1 Shoes\n⚠ [1/1] Bỏ qua (trùng slug): Simple Plan Bigger Than You Think Tour Air Force 1 Shoes\nHoàn thành!\n⚠️ 1 SP lỗi, retry sau 10s...\n  ✅ Retry OK: Simple Plan Bigger Than You Think Tour Air Force 1 Shoes\n✅ Hoàn thành: 1/1 SP\n	2026-06-16 08:27:43.104834	2026-06-16 08:29:10.442457
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: woommo
--

COPY public.settings (id, key, value) FROM stdin;
1	openai_key	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
2	openai_model	gpt-4o-mini
3	serper_key	e50fb116a3c46ae42f4b67f350ac896afcf1e80d
4	store_name	BreakTees
5	custom_shortcode	[thien_display_single_image]
6	link_config	{"mode":"category","category_links":[]}
11	link_config_user_3_store_1	{"mode": "category", "category_links": [{"name": "3D Hoodie", "url": "https://breaktees.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://breaktees.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://breaktees.com/accessories/"}, {"name": "Air Force 1", "url": "https://breaktees.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://breaktees.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://breaktees.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://breaktees.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://breaktees.com/trending/anime/"}, {"name": "APPAREL", "url": "https://breaktees.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://breaktees.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://breaktees.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://breaktees.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://breaktees.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://breaktees.com/apparel/bomber-jacket/"}, {"name": "Canvas / Poster", "url": "https://breaktees.com/apparel/canvas-poster/"}, {"name": "Christmas Gifts", "url": "https://breaktees.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://breaktees.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://breaktees.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://breaktees.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://breaktees.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://breaktees.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://breaktees.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://breaktees.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://breaktees.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://breaktees.com/apparel/hockey-jersey/"}, {"name": "Hoodie", "url": "https://breaktees.com/apparel/hoodie/"}, {"name": "Long Sleeve", "url": "https://breaktees.com/apparel/long-sleeve/"}, {"name": "Mother's Day Gifts", "url": "https://breaktees.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://breaktees.com/trending/movie/"}, {"name": "Music", "url": "https://breaktees.com/trending/music/"}, {"name": "Political", "url": "https://breaktees.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://breaktees.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://breaktees.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://breaktees.com/special-occasions/st-patricks-day-gifts/"}, {"name": "Sweatshirt", "url": "https://breaktees.com/apparel/sweatshirt/"}, {"name": "T-Shirt", "url": "https://breaktees.com/apparel/t-shirt/"}, {"name": "Thanksgiving Gifts", "url": "https://breaktees.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://breaktees.com/trending/"}, {"name": "Tumbler", "url": "https://breaktees.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://breaktees.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://breaktees.com/special-occasions/veterans-day-gifts/"}], "product_pool": []}
13	link_config_user_1_store_1	{"mode": "category", "category_links": [{"name": "3D Hoodie", "url": "https://breaktees.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://breaktees.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://breaktees.com/accessories/"}, {"name": "Air Force 1", "url": "https://breaktees.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://breaktees.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://breaktees.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://breaktees.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://breaktees.com/trending/anime/"}, {"name": "APPAREL", "url": "https://breaktees.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://breaktees.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://breaktees.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://breaktees.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://breaktees.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://breaktees.com/apparel/bomber-jacket/"}, {"name": "Canvas / Poster", "url": "https://breaktees.com/apparel/canvas-poster/"}, {"name": "Christmas Gifts", "url": "https://breaktees.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://breaktees.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://breaktees.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://breaktees.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://breaktees.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://breaktees.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://breaktees.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://breaktees.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://breaktees.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://breaktees.com/apparel/hockey-jersey/"}, {"name": "Hoodie", "url": "https://breaktees.com/apparel/hoodie/"}, {"name": "Long Sleeve", "url": "https://breaktees.com/apparel/long-sleeve/"}, {"name": "Mother's Day Gifts", "url": "https://breaktees.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://breaktees.com/trending/movie/"}, {"name": "Music", "url": "https://breaktees.com/trending/music/"}, {"name": "Political", "url": "https://breaktees.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://breaktees.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://breaktees.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://breaktees.com/special-occasions/st-patricks-day-gifts/"}, {"name": "Sweatshirt", "url": "https://breaktees.com/apparel/sweatshirt/"}, {"name": "T-Shirt", "url": "https://breaktees.com/apparel/t-shirt/"}, {"name": "Thanksgiving Gifts", "url": "https://breaktees.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://breaktees.com/trending/"}, {"name": "Tumbler", "url": "https://breaktees.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://breaktees.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://breaktees.com/special-occasions/veterans-day-gifts/"}], "product_pool": []}
7	link_config_user_2	{"mode": "product", "category_links": [{"name": "3D Hoodie", "url": "https://www.breaktees.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://www.breaktees.com/apparel/3d-t-shirt/"}, {"name": "Air Force 1", "url": "https://www.breaktees.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://www.breaktees.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://www.breaktees.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://www.breaktees.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://www.breaktees.com/trending/anime/"}, {"name": "APPAREL", "url": "https://www.breaktees.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://www.breaktees.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://www.breaktees.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://www.breaktees.com/sports-gifts/basketball-gifts/"}, {"name": "Canvas / Poster", "url": "https://www.breaktees.com/apparel/canvas-poster/"}, {"name": "Christmas Gifts", "url": "https://www.breaktees.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://www.breaktees.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://www.breaktees.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://www.breaktees.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://www.breaktees.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://www.breaktees.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://www.breaktees.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://www.breaktees.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://www.breaktees.com/sports-gifts/hockey-gifts/"}, {"name": "Hoodie", "url": "https://www.breaktees.com/apparel/hoodie/"}, {"name": "Long Sleeve", "url": "https://www.breaktees.com/apparel/long-sleeve/"}, {"name": "Mother's Day Gifts", "url": "https://www.breaktees.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://www.breaktees.com/trending/movie/"}, {"name": "Music", "url": "https://www.breaktees.com/trending/music/"}, {"name": "Political", "url": "https://www.breaktees.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://www.breaktees.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://www.breaktees.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://www.breaktees.com/special-occasions/st-patricks-day-gifts/"}, {"name": "T-Shirt", "url": "https://www.breaktees.com/apparel/t-shirt/"}, {"name": "Thanksgiving Gifts", "url": "https://www.breaktees.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://www.breaktees.com/trending/"}, {"name": "Valentine's Day Gifts", "url": "https://www.breaktees.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://www.breaktees.com/special-occasions/veterans-day-gifts/"}], "product_pool": [{"title": "Melanie Martinez Tour 2026 Air Force 1 Shoes", "url": "https://www.breaktees.com/product/melanie-martinez-tour-2026/"}, {"title": "Don't Get Greedy - Tate Mcrae Air Jordan 13 Shoes", "url": "https://www.breaktees.com/product/dont-get-greedy-tate-mcrae-air-jordan-13-shoes/"}, {"title": "Baby Don't Get Greedy - Tate Mcrae Air Jordan 11 Shoes", "url": "https://www.breaktees.com/product/baby-dont-get-greedy-tate-mcrae-air-jordan-11-shoes/"}, {"title": "Avenged Sevenfold Tour 2026 Custom Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/avenged-sevenfold-tour-2026-custom-air-jordan-1-shoes/"}, {"title": "World Tour - BTS World Tour 2026 Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/world-tour-bts-world-tour-2026-air-jordan-1-shoes/"}, {"title": "Avenged Sevenfold Tour 2026 Custom Air Force 1 Shoes", "url": "https://www.breaktees.com/product/avenged-sevenfold-tour-2026-custom-air-force-1-shoes/"}, {"title": "Olivia Rodrigo Swing Embroidered 2026 Custom Air Force 1 Shoes", "url": "https://www.breaktees.com/product/olivia-rodrigo-swing-embroidered-2026-custom-air-force-1-shoes/"}, {"title": "Out of breath hiking society be there in a minute raccoon T-Shirt", "url": "https://www.breaktees.com/product/out-of-breath-hiking-society-be-there-in-a-minute-raccoon-t-shirt/"}, {"title": "Bini Signature World Tour 2026 Custom Air Force 1 Black Shoes", "url": "https://www.breaktees.com/product/bini-signature-world-tour-2026/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Limited Edition Air Jordan 1 White Custom Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-limited-edition-air-jordan-1-white-custom-shoes/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Limited Edition Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-limited-edition-air-jordan-1-shoes-2/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Custom Name Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-custom-name-air-jordan-1-shoes/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Custom Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-custom-air-jordan-1-shoes/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Limited Edition Custom Air Force 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-limited-edition-custom-air-force-1-shoes/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Limited Edition Air Force 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-limited-edition-air-force-1-shoes-2/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Limited Edition Air Force 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-limited-edition-air-force-1-shoes/"}, {"title": "Jeremiyah Love Arizona Cardinals love is in the air T-Shirt", "url": "https://www.breaktees.com/product/jeremiyah-love-arizona-cardinals-love-is-in-the-air-t-shirt/"}, {"title": "Jordy Bahl Nebraska Cornhuskers Black 90s Retro T-Shirt", "url": "https://www.breaktees.com/product/jordy-bahl-nebraska-cornhuskers-black-90s-retro-t-shirt/"}, {"title": "Viajando Por El Mundo Tropitour 2026 Limited Edition Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/viajando-por-el-mundo-tropitour-2026-limited-edition-air-jordan-1-shoes/"}, {"title": "Ace Frehley Kiss Band Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/ace-frehley-kiss-band-air-jordan-1-shoes/"}, {"title": "Ariana Grande Wicked For Good Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/ariana-grande-wicked-for-good-air-jordan-1-shoes/"}, {"title": "Karol G - Nos Vamos de Tour Limited Edition Signature - Pink Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/karol-g-nos-vamos-de-tour-limited-edition-signature-pink-air-jordan-1-shoes/"}, {"title": "Bini Signal World Tour 2026 Custom Air Force 1 Shoes", "url": "https://www.breaktees.com/product/bini-signal-world-tour-2026-custom-air-force-1-shoes/"}, {"title": "Bruno Mars The Romantic North America Tour 2026 Air Force 1 Shoes", "url": "https://www.breaktees.com/product/bruno-mars-the-romantic-north-america-tour-2026-air-force-1-shoes/"}, {"title": "Karol G Mundial Custom Nike Air Force 1 Shoes", "url": "https://www.breaktees.com/product/karol-g-mundial-custom-nike-air-force-1-shoes/"}, {"title": "Karol G Fan Custom Name Air Force 1 Shoes", "url": "https://www.breaktees.com/product/karol-g-fan-custom-name-air-force-1-shoes/"}, {"title": "Shakira Las Mujeres Ya No Lloran World Tour 2026 Custom Name Air Force 1 Shoes", "url": "https://www.breaktees.com/product/shakira-las-mujeres-ya-no-lloran-world-tour-2026-custom-name-air-force-1-shoes/"}, {"title": "Karol G Mundial Custom Nike Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/karol-g-mundial-custom-nike-air-jordan-1-shoes/"}, {"title": "Ariana Grande The Eternal Sunshine Tour 2026 Air Force 1 Shoes", "url": "https://www.breaktees.com/product/ariana-grande-the-eternal-sunshine-tour-2026-air-force-1-shoes/"}, {"title": "Ariana Grande The Eternal Sunshine Tour 2026 Air Force 1 Sneakers", "url": "https://www.breaktees.com/product/ariana-grande-the-eternal-sunshine-tour-2026-air-force-1-sneakers/"}, {"title": "Ariana Grande The Eternal Sunshine Tour 2026 Custom Air Force 1 Shoes", "url": "https://www.breaktees.com/product/ariana-grande-the-eternal-sunshine-tour-2026-custom-air-force-1-shoes/"}, {"title": "Ariana Grande The Eternal Sunshine Tour 2026 Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/ariana-grande-the-eternal-sunshine-tour-2026-air-jordan-1-shoes/"}, {"title": "Ariana Grande The Eternal Sunshine Tour Custom Air Jordan 1 Shoes", "url": "https://www.breaktees.com/product/ariana-grande-the-eternal-sunshine-tour-custom-air-jordan-1-shoes/"}, {"title": "Sonny Styles No Matter What NFL Shirt", "url": "https://www.breaktees.com/product/sonny-styles-no-matter-what-nfl-shirt/"}, {"title": "Sonny Styles Ohio state NFL Shirt", "url": "https://www.breaktees.com/product/sonny-styles-ohio-state-nfl-shirt/"}, {"title": "Washington Redskins NFL Air Jordan 13 Shoes", "url": "https://www.breaktees.com/product/washington-redskins-nfl-air-jordan-13-shoes/"}, {"title": "Washington Redskins NFL White Brown Logo Air Jordan 13 Shoes", "url": "https://www.breaktees.com/product/washington-redskins-nfl-white-brown-logo-air-jordan-13-shoes/"}, {"title": "DeMar DeRozan Sacramento Kings NBA T-Shirt", "url": "https://www.breaktees.com/product/demar-derozan-sacramento-kings-nba-t-shirt/"}, {"title": "Paraguay North America Soccer Tournament 2026 T-Shirt", "url": "https://www.breaktees.com/product/paraguay-north-america-soccer-tournament-2026-t-shirt/"}, {"title": "Miami Hurricanes Legacy On Lock NCAA Fan T-Shirt", "url": "https://www.breaktees.com/product/miami-hurricanes-legacy-on-lock-ncaa-fan-t-shirt/"}, {"title": "Celticsy Boston Basketball Fan T-Shirt", "url": "https://www.breaktees.com/product/celticsy-boston-basketball-fan-t-shirt/"}, {"title": "Jaylen Brown Boston Celtics Playoff Basketball Fan T-Shirt", "url": "https://www.breaktees.com/product/jaylen-brown-boston-celtics-playoff-basketball-fan-t-shirt/"}, {"title": "Luka Doncic #77 Lakers Purple and Gold Shirt - NBA Fantasy Concept Graphic Tee", "url": "https://www.breaktees.com/product/luka-doncic-77-lakers-purple-and-gold/"}, {"title": "Ultimate Duke Basketball ACC Conference Champions 2026 T-Shirt", "url": "https://www.breaktees.com/product/duke-basketball-acc-conference-champions-2026-t-shirt/"}]}
12	link_config_user_3_store_3	{"mode": "product", "category_links": [{"name": "2D T-Shirt", "url": "https://printedaura.com/apparel/2d-t-shirt/"}, {"name": "3D Hoodie", "url": "https://printedaura.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://printedaura.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://printedaura.com/accessories/"}, {"name": "Air Force 1", "url": "https://printedaura.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://printedaura.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://printedaura.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://printedaura.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://printedaura.com/trending/anime/"}, {"name": "APPAREL", "url": "https://printedaura.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://printedaura.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://printedaura.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://printedaura.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://printedaura.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://printedaura.com/apparel/bomber-jacket/"}, {"name": "Christmas Gifts", "url": "https://printedaura.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://printedaura.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://printedaura.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://printedaura.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://printedaura.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://printedaura.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://printedaura.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://printedaura.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://printedaura.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://printedaura.com/apparel/hockey-jersey/"}, {"name": "Mother's Day Gifts", "url": "https://printedaura.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://printedaura.com/trending/movie/"}, {"name": "Music", "url": "https://printedaura.com/trending/music/"}, {"name": "Political", "url": "https://printedaura.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://printedaura.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://printedaura.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://printedaura.com/special-occasions/st-patricks-day-gifts/"}, {"name": "Thanksgiving Gifts", "url": "https://printedaura.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://printedaura.com/trending/"}, {"name": "Tumbler", "url": "https://printedaura.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://printedaura.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://printedaura.com/special-occasions/veterans-day-gifts/"}], "product_pool": [{"title": "San Diego Padres x Taylor Swift x TS5 Special Hoodie", "url": "https://printedaura.com/product/san-diego-padres-x-taylor-swift-x-ts5-special-hoodie/"}, {"title": "San Diego Padres x Filipino Heritage Night 2026 Hoodie", "url": "https://printedaura.com/product/san-diego-padres-x-filipino-heritage-night-2026-hoodie/"}, {"title": "San Diego Padres x Taylor Swift x TS5 Special Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-taylor-swift-x-ts5-special-jersey/"}, {"title": "San Diego Padres x House of The Dragon 2026 Special Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-house-of-the-dragon-2026-special-jersey/"}, {"title": "San Diego Padres x El Salvadoran Heritage Night 2026 Baseball Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-el-salvadoran-heritage-night-2026-baseball-jersey/"}, {"title": "San Diego Padres x Fuerza Regida This Is Our Dream Stadium Tour 2026 Baseball Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-fuerza-regida-this-is-our-dream-stadium-tour-2026-baseball-jersey/"}, {"title": "San Diego Padres x Toy Story Night Baseball Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-toy-story-night-baseball-jersey/"}, {"title": "San Diego Padres x Lady Gagas MAYHEM Album Jersey", "url": "https://printedaura.com/product/san-diego-padres-x-lady-gagas-mayhem-album-jersey/"}]}
8	link_config_user_1	{"mode": "product", "category_links": [{"name": "3D Hoodie", "url": "https://breaktees.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://breaktees.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://breaktees.com/accessories/"}, {"name": "Air Force 1", "url": "https://breaktees.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://breaktees.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://breaktees.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://breaktees.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://breaktees.com/trending/anime/"}, {"name": "APPAREL", "url": "https://breaktees.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://breaktees.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://breaktees.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://breaktees.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://breaktees.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://breaktees.com/apparel/bomber-jacket/"}, {"name": "Canvas / Poster", "url": "https://breaktees.com/apparel/canvas-poster/"}, {"name": "Christmas Gifts", "url": "https://breaktees.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://breaktees.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://breaktees.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://breaktees.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://breaktees.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://breaktees.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://breaktees.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://breaktees.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://breaktees.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://breaktees.com/apparel/hockey-jersey/"}, {"name": "Hoodie", "url": "https://breaktees.com/apparel/hoodie/"}, {"name": "Long Sleeve", "url": "https://breaktees.com/apparel/long-sleeve/"}, {"name": "Mother's Day Gifts", "url": "https://breaktees.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://breaktees.com/trending/movie/"}, {"name": "Music", "url": "https://breaktees.com/trending/music/"}, {"name": "Political", "url": "https://breaktees.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://breaktees.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://breaktees.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://breaktees.com/special-occasions/st-patricks-day-gifts/"}, {"name": "T-Shirt", "url": "https://breaktees.com/apparel/t-shirt/"}, {"name": "Thanksgiving Gifts", "url": "https://breaktees.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://breaktees.com/trending/"}, {"name": "Tumbler", "url": "https://breaktees.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://breaktees.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://breaktees.com/special-occasions/veterans-day-gifts/"}], "product_pool": [{"title": "Binghamton Black Bears 2026 FPHL Champions Three-Peat Limited Edition Hockey Jersey", "url": "https://breaktees.com/product/binghamton-black-bears-2026-fphl-champions-three-peat-limited-edition-hockey-jersey/"}, {"title": "Binghamton Black Bears 2026 FPHL Champions Three-Peat Design Hockey Jersey", "url": "https://breaktees.com/product/binghamton-black-bears-2026-fphl-champions-three-peat-design-hockey-jersey/"}, {"title": "Binghamton Black Bears 2026 FPHL Champions Three-Peat Limited Edition Cap", "url": "https://breaktees.com/product/binghamton-black-bears-2026-fphl-champions-three-peat-limited-edition-cap/"}, {"title": "San Diego Padres Day of The Dead City Connect Custom Air Force 1", "url": "https://breaktees.com/product/san-diego-padres-day-of-the-dead-city-connect-custom-air-force-1/"}, {"title": "Marc Mrquez Ducati Lenovo Team AF1 Sneaker", "url": "https://breaktees.com/product/marc-mrquez-ducati-lenovo-team-af1-sneaker/"}, {"title": "Cody Rhodes Nightmare Legacy Air Force 1 Sneaker", "url": "https://breaktees.com/product/cody-rhodes-nightmare-legacy-air-force-1-sneaker/"}, {"title": "Baltimore Ravens The Next Flight 2026 Custom Air Force 1 Sneaker", "url": "https://breaktees.com/product/baltimore-ravens-the-next-flight-2026-custom-air-force-1-sneaker/"}, {"title": "Washington Commanders Raise Hail Custom Air Jordan 1 Sneaker", "url": "https://breaktees.com/product/washington-commanders-raise-hail-custom-air-jordan-1-sneaker/"}, {"title": "Seattle Seahawks Special New 2026 Air Jordan 1 Sneaker", "url": "https://breaktees.com/product/seattle-seahawks-special-new-2026-air-jordan-1-sneaker/"}, {"title": "Baltimore Ravens The Next Flight 2026 Custom Air Jordan 1 Sneaker", "url": "https://breaktees.com/product/baltimore-ravens-the-next-flight-2026-custom-air-jordan-1-sneaker/"}, {"title": "Oliver Tree Love You Madly World Tour Chaos Baseball Jersey", "url": "https://breaktees.com/product/oliver-tree-love-you-madly-world-tour-chaos-baseball-jersey/"}, {"title": "BRITPOP World Tour - Australia &amp; New Zealand Baseball Jersey", "url": "https://breaktees.com/product/britpop-world-tour-australia-new-zealand-baseball-jersey/"}, {"title": "Avenged Sevenfold Tour 2026 Baseball Jersey", "url": "https://breaktees.com/product/avenged-sevenfold-tour-2026-baseball-jersey/"}, {"title": "Worcester Red Sox x The Art of The Woo Baseball Jersey", "url": "https://breaktees.com/product/worcester-red-sox-x-the-art-of-the-woo-baseball-jersey/"}, {"title": "Tulsa Drillers x Star Wars Night Mandalorian Grogu Custom Baseball Jersey", "url": "https://breaktees.com/product/tulsa-drillers-x-star-wars-night-mandalorian-grogu-custom-baseball-jersey/"}, {"title": "Springfield Cardinals x Star Wars Night Game R2-D2 Design Custom Jersey", "url": "https://breaktees.com/product/springfield-cardinals-x-star-wars-night-game-r2-d2-design-custom-jersey/"}, {"title": "Seattle Seahawks x Star Wars The power of The Dark Side Special Baseball Jersey", "url": "https://breaktees.com/product/seattle-seahawks-x-star-wars-the-power-of-the-dark-side-special-baseball-jersey/"}, {"title": "Los Angeles Dodgers x Japanese Heritage Night Jersey", "url": "https://breaktees.com/product/los-angeles-dodgers-x-japanese-heritage-night-jersey/"}, {"title": "LA Dodgers x Japanese Heritage Night 2026 Special Baseball Jersey", "url": "https://breaktees.com/product/la-dodgers-x-japanese-heritage-night-2026-special-baseball-jersey/"}, {"title": "Kannapolis Cannon Ballers Barbie Night Game Custom Baseball Jersey", "url": "https://breaktees.com/product/kannapolis-cannon-ballers-barbie-night-game-custom-baseball-jersey/"}, {"title": "Houston Astros Care Bears Night Custom Baseball Jersey", "url": "https://breaktees.com/product/houston-astros-care-bears-night-custom-baseball-jersey/"}, {"title": "Frisco RoughRiders x Toy Story Night Custom Baseball Jersey", "url": "https://breaktees.com/product/frisco-roughriders-x-toy-story-night-custom-baseball-jersey/"}, {"title": "Frisco RoughRiders x Teenage Mutant Ninja Turtles Night Custom Baseball Jersey", "url": "https://breaktees.com/product/frisco-roughriders-x-teenage-mutant-ninja-turtles-night-custom-baseball-jersey/"}, {"title": "Fayetteville Woodpeckers x Military Appreciation Camo Custom Jersey", "url": "https://breaktees.com/product/fayetteville-woodpeckers-x-military-appreciation-camo-custom-jersey/"}, {"title": "Fayetteville Woodpeckers 2026 Star Wars Night Custom Baseball Jersey", "url": "https://breaktees.com/product/fayetteville-woodpeckers-2026-star-wars-night-custom-baseball-jersey/"}, {"title": "El Paso Chihuahuas Chucotown Custom Baseball Jersey", "url": "https://breaktees.com/product/el-paso-chihuahuas-chucotown-custom-baseball-jersey/"}, {"title": "Diablos Rojos del Mexico x Star Wars Night Baseball Jersey", "url": "https://breaktees.com/product/diablos-rojos-del-mexico-x-star-wars-night-baseball-jersey/"}, {"title": "Boston Red Sox x One Piece Grand Voyage Sunset 2026 Baseball Jersey", "url": "https://breaktees.com/product/boston-red-sox-x-one-piece-grand-voyage-sunset-2026-baseball-jersey/"}, {"title": "Portland Fire Rose City Custom Basketball Jersey", "url": "https://breaktees.com/product/portland-fire-rose-city-custom-basketball-jersey/"}, {"title": "Kacey Musgraves Middle of Nowhere Tour Basketball Jersey", "url": "https://breaktees.com/product/kacey-musgraves-middle-of-nowhere-tour-basketball-jersey/"}, {"title": "Inter Milan CAMPIONI D'ITALIA 25-26 Custom Air Force 1", "url": "https://breaktees.com/product/inter-milan-campioni-ditalia-25-26-custom-air-force-1/"}, {"title": "West Ham United Till I Die 125th Anniversary Air Force 1 Shoes", "url": "https://breaktees.com/product/west-ham-united-till-i-die-125th-anniversary-air-force-1-shoes/"}, {"title": "FC Barcelona x Olivia Rodrigo Signature Custom Air Jordan 1", "url": "https://breaktees.com/product/fc-barcelona-x-olivia-rodrigo-signature-custom-air-jordan-1/"}, {"title": "Washington Mystics 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/washington-mystics-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Toronto Tempo 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/toronto-tempo-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Texas Rangers x Dallas Wings Night Paige Bueckers Signature Custom Basketball Jersey", "url": "https://breaktees.com/product/texas-rangers-x-dallas-wings-night-paige-bueckers-signature-custom-basketball-jersey/"}, {"title": "Seattle Storm 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/seattle-storm-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Portland 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/portland-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Phoenix Mercury 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/phoenix-mercury-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "New York Liberty 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/new-york-liberty-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Minnesota Lynx 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/minnesota-lynx-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Los Angeles Sparks 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/los-angeles-sparks-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Las Vegas Aces 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/las-vegas-aces-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Indiana Fever 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/indiana-fever-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Golden State Valkyries 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/golden-state-valkyries-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Dallas Wings 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/dallas-wings-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Connecticut Sun 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/connecticut-sun-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Chicago Sky 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/chicago-sky-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "Atlanta Dream 2026 WNBA x Pride Day Limited Edition Jersey", "url": "https://breaktees.com/product/atlanta-dream-2026-wnba-x-pride-day-limited-edition-jersey/"}, {"title": "CORTIS x NBA All-Stars 2026 Customize Basketball Jersey", "url": "https://breaktees.com/product/cortis-x-nba-all-stars-2026-customize-basketball-jersey/"}, {"title": "Billie Eilish Hit Me Hard and Soft Tour 2026 Basketball Jersey  Pink", "url": "https://breaktees.com/product/billie-eilish-hit-me-hard-and-soft-tour-2026-basketball-jersey-pink/"}, {"title": "Billie Eilish Hit Me Hard and Soft Tour 2026 Basketball Jersey", "url": "https://breaktees.com/product/billie-eilish-hit-me-hard-and-soft-tour-2026-basketball-jersey/"}, {"title": "Stephen Sanchez The Lover Down Under Tour Special Baseball Jersey", "url": "https://breaktees.com/product/stephen-sanchez-the-lover-down-under-tour-special-baseball-jersey/"}, {"title": "Sevendust 2026 Europe UK Tour Special Baseball Jersey", "url": "https://breaktees.com/product/sevendust-2026-europe-uk-tour-special-baseball-jersey/"}, {"title": "Olivia Rodrigo The Unraveled Tour 2026 Pretty Sad in Love Baseball Jersey", "url": "https://breaktees.com/product/olivia-rodrigo-the-unraveled-tour-2026-pretty-sad-in-love-baseball-jersey/"}, {"title": "Foster The People THE GOOD MOURNING SUNSHINE TOUR Special Baseball Jersey", "url": "https://breaktees.com/product/foster-the-people-the-good-mourning-sunshine-tour-special-baseball-jersey/"}, {"title": "BUNT In The Round Tour 2026 Baseball Jersey", "url": "https://breaktees.com/product/bunt-in-the-round-tour-2026-baseball-jersey/"}, {"title": "BINI Signals World Tour 2026 Special Baseball Jersey", "url": "https://breaktees.com/product/bini-signals-world-tour-2026-special-baseball-jersey/"}, {"title": "Toledo Mud Hens x Backyard Baseball Custom Jersey", "url": "https://breaktees.com/product/toledo-mud-hens-x-backyard-baseball-custom-jersey/"}, {"title": "Texas Rangers x Dallas Wings Night Custom Baseball Jersey", "url": "https://breaktees.com/product/texas-rangers-x-dallas-wings-night-custom-baseball-jersey/"}, {"title": "Sugar Land Space Cowboys Happy Mothers Day Custom Baseball Jersey", "url": "https://breaktees.com/product/sugar-land-space-cowboys-happy-mothers-day-custom-baseball-jersey/"}, {"title": "Pittsburgh Pirates x Bob Skinner In Memoriam Signature Baseball Jersey", "url": "https://breaktees.com/product/pittsburgh-pirates-x-bob-skinner-in-memoriam-signature-baseball-jersey/"}, {"title": "Myke Towers 2026 Tour Baseball Jersey", "url": "https://breaktees.com/product/myke-towers-2026-tour-baseball-jersey/"}, {"title": "Miami Marlins 2026 Nurse Appreciation Baseball Jersey", "url": "https://breaktees.com/product/miami-marlins-2026-nurse-appreciation-baseball-jersey/"}, {"title": "Memphis Redbirds Dos de Mayo Special Baseball Jersey", "url": "https://breaktees.com/product/memphis-redbirds-dos-de-mayo-special-baseball-jersey/"}, {"title": "Los Angeles Angels x Pepe Aguilar  En Concierto USA 2026 Baseball Jersey", "url": "https://breaktees.com/product/los-angeles-angels-x-pepe-aguilar-en-concierto-usa-2026-baseball-jersey/"}, {"title": "Los Angeles Angels x Christmas in June Baseball Jersey", "url": "https://breaktees.com/product/los-angeles-angels-x-christmas-in-june-baseball-jersey/"}, {"title": "Los Angeles Angels x Alesso 2026 USA Tour Baseball Jersey", "url": "https://breaktees.com/product/los-angeles-angels-x-alesso-2026-usa-tour-baseball-jersey/"}, {"title": "Iowa Cubs 2026 Armed Forces Custom Baseball Jersey", "url": "https://breaktees.com/product/iowa-cubs-2026-armed-forces-custom-baseball-jersey/"}, {"title": "El Paso Chihuahuas x Star Wars Maul Shadow Lord Special Baseball Jersey", "url": "https://breaktees.com/product/el-paso-chihuahuas-x-star-wars-maul-shadow-lord-special-baseball-jersey/"}, {"title": "El Paso Chihuahuas x Backyard Baseball Custom Jersey", "url": "https://breaktees.com/product/el-paso-chihuahuas-x-backyard-baseball-custom-jersey/"}, {"title": "Durham Bulls Toros Bravos De Durham Custom Baseball Jersey", "url": "https://breaktees.com/product/durham-bulls-toros-bravos-de-durham-custom-baseball-jersey/"}, {"title": "Durham Bulls AAPI Night Special Baseball Jersey", "url": "https://breaktees.com/product/durham-bulls-aapi-night-special-baseball-jersey/"}, {"title": "Charleston RiverDogs x Star Wars Night Custom Baseball Jersey", "url": "https://breaktees.com/product/charleston-riverdogs-x-star-wars-night-custom-baseball-jersey/"}, {"title": "Buffalo Bisons Cheerios Night at the Ballpark Special Baseball Jersey", "url": "https://breaktees.com/product/buffalo-bisons-cheerios-night-at-the-ballpark-special-baseball-jersey/"}, {"title": "San Francisco 49ers Karol G Viajando Por El Mundo Tropitour 2026 Football Jersey", "url": "https://breaktees.com/product/san-francisco-49ers-karol-g-viajando-por-el-mundo-tropitour-2026-football-jersey/"}, {"title": "Karol G Houston Texans Viajando Por El Mundo Football Jersey", "url": "https://breaktees.com/product/karol-g-houston-texans-viajando-por-el-mundo-football-jersey/"}, {"title": "Dallas Cowboys Karol G Viajando Por El Mundo Tropitour 2026 Football Jersey", "url": "https://breaktees.com/product/dallas-cowboys-karol-g-viajando-por-el-mundo-tropitour-2026-football-jersey/"}, {"title": "Atlanta Falcons x Karol G Viajando Por El Mundo 2026 Football Jersey", "url": "https://breaktees.com/product/atlanta-falcons-x-karol-g-viajando-por-el-mundo-2026-football-jersey/"}, {"title": "New York Mets x Karol G Viajando Por El Mundo 2026 White Baseball Jersey", "url": "https://breaktees.com/product/new-york-mets-x-karol-g-viajando-por-el-mundo-2026-white-baseball-jersey/"}, {"title": "Los Angeles Dodgers x Karol G Viajando Por El Mundo 2026 White Baseball Jersey", "url": "https://breaktees.com/product/los-angeles-dodgers-x-karol-g-viajando-por-el-mundo-2026-white-baseball-jersey/"}, {"title": "Karol G 2026 Viajando Por El Mundo Tropitour White Baseball Jersey", "url": "https://breaktees.com/product/karol-g-2026-viajando-por-el-mundo-tropitour-white-baseball-jersey/"}, {"title": "Karol G 2026 Viajando Por El Mundo Tropitour Black Baseball Jersey", "url": "https://breaktees.com/product/karol-g-2026-viajando-por-el-mundo-tropitour-black-baseball-jersey/"}, {"title": "Karol G 2026 Viajando Por El Mundo Tropitour Baseball Jersey", "url": "https://breaktees.com/product/karol-g-2026-viajando-por-el-mundo-tropitour-baseball-jersey/"}, {"title": "Houston Astros x Karol G Viajando Por El Mundo 2026 White Baseball Jersey", "url": "https://breaktees.com/product/houston-astros-x-karol-g-viajando-por-el-mundo-2026-white-baseball-jersey/"}, {"title": "Boston Red Sox x Karol G Viajando Por El Mundo 2026 White Baseball Jersey", "url": "https://breaktees.com/product/boston-red-sox-x-karol-g-viajando-por-el-mundo-2026-white-baseball-jersey/"}, {"title": "Owen Sound Attack Custom Air Jordan 1 Sneaker", "url": "https://breaktees.com/product/owen-sound-attack-custom-air-jordan-1-sneaker/"}, {"title": "Los Angeles Rams Back in Black Special Air Jordan 1", "url": "https://breaktees.com/product/los-angeles-rams-back-in-black-special-air-jordan-1/"}, {"title": "Everyone Watches Womens Sports Unrivaled Air Jordan 1", "url": "https://breaktees.com/product/everyone-watches-womens-sports-unrivaled-air-jordan-1/"}, {"title": "Phoenix Suns x Hello Kitty Special Air Force 1", "url": "https://breaktees.com/product/phoenix-suns-x-hello-kitty-special-air-force-1/"}, {"title": "New York Yankees x Hamilton 2026 Special Air Force 1 Sneaker", "url": "https://breaktees.com/product/new-york-yankees-x-hamilton-2026-special-air-force-1-sneaker/"}, {"title": "Oklahoma Sooners Special New 2026 Air Force 1 Sneaker", "url": "https://breaktees.com/product/oklahoma-sooners-special-new-2026-air-force-1-sneaker/"}, {"title": "Minnesota Timberwolves x Hello Kitty Night 2026 Special Air Force 1 Sneaker", "url": "https://breaktees.com/product/minnesota-timberwolves-x-hello-kitty-night-2026-special-air-force-1-sneaker/"}, {"title": "GDragon x World Cup 2026 Peaceminusone Korea Jersey T-Shirt", "url": "https://breaktees.com/product/gdragon-x-world-cup-2026-peaceminusone-korea-jersey-t-shirt/"}, {"title": "Chicago Bulls x Hello Kitty Special Air Force 1", "url": "https://breaktees.com/product/chicago-bulls-x-hello-kitty-special-air-force-1/"}, {"title": "Alabama Crimson Tide Special New 2026 Air Force 1 Sneaker", "url": "https://breaktees.com/product/alabama-crimson-tide-special-new-2026-air-force-1-sneaker/"}, {"title": "Melanie Martinez Tour 2026 Air Force 1 Shoes", "url": "https://breaktees.com/product/melanie-martinez-tour-2026/"}, {"title": "St. Paul Saints Peanuts Night MiLB 2026 Personalized Baseball Jersey", "url": "https://breaktees.com/product/st-paul-saints-peanuts-night-milb-2026-personalized-baseball-jersey/"}, {"title": "Salt Lake Bees Peanuts Night MiLB 2026 Personalized Baseball Jersey", "url": "https://breaktees.com/product/salt-lake-bees-peanuts-night-milb-2026-personalized-baseball-jersey/"}, {"title": "Rochester Redwings Peanuts Night MiLB 2026 Personalized Baseball Jersey", "url": "https://breaktees.com/product/rochester-redwings-peanuts-night-milb-2026-personalized-baseball-jersey/"}]}
9	link_config_user_3	{"mode": "category", "category_links": [{"name": "3D Hoodie", "url": "https://breaktees.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://breaktees.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://breaktees.com/accessories/"}, {"name": "Air Force 1", "url": "https://breaktees.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://breaktees.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://breaktees.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://breaktees.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://breaktees.com/trending/anime/"}, {"name": "APPAREL", "url": "https://breaktees.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://breaktees.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://breaktees.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://breaktees.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://breaktees.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://breaktees.com/apparel/bomber-jacket/"}, {"name": "Canvas / Poster", "url": "https://breaktees.com/apparel/canvas-poster/"}, {"name": "Christmas Gifts", "url": "https://breaktees.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://breaktees.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://breaktees.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://breaktees.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://breaktees.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://breaktees.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://breaktees.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://breaktees.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://breaktees.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://breaktees.com/apparel/hockey-jersey/"}, {"name": "Hoodie", "url": "https://breaktees.com/apparel/hoodie/"}, {"name": "Long Sleeve", "url": "https://breaktees.com/apparel/long-sleeve/"}, {"name": "Mother's Day Gifts", "url": "https://breaktees.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://breaktees.com/trending/movie/"}, {"name": "Music", "url": "https://breaktees.com/trending/music/"}, {"name": "Political", "url": "https://breaktees.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://breaktees.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://breaktees.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://breaktees.com/special-occasions/st-patricks-day-gifts/"}, {"name": "Sweatshirt", "url": "https://breaktees.com/apparel/sweatshirt/"}, {"name": "T-Shirt", "url": "https://breaktees.com/apparel/t-shirt/"}, {"name": "Thanksgiving Gifts", "url": "https://breaktees.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://breaktees.com/trending/"}, {"name": "Tumbler", "url": "https://breaktees.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://breaktees.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://breaktees.com/special-occasions/veterans-day-gifts/"}], "product_pool": []}
10	link_config_user_3_store_0	{"mode": "category", "category_links": [{"name": "3D Hoodie", "url": "https://breaktees.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://breaktees.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://breaktees.com/accessories/"}, {"name": "Air Force 1", "url": "https://breaktees.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://breaktees.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://breaktees.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://breaktees.com/footwear/air-jordan-13/"}, {"name": "Anime", "url": "https://breaktees.com/trending/anime/"}, {"name": "APPAREL", "url": "https://breaktees.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://breaktees.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://breaktees.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://breaktees.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://breaktees.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://breaktees.com/apparel/bomber-jacket/"}, {"name": "Canvas / Poster", "url": "https://breaktees.com/apparel/canvas-poster/"}, {"name": "Christmas Gifts", "url": "https://breaktees.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://breaktees.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://breaktees.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://breaktees.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://breaktees.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://breaktees.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://breaktees.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://breaktees.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://breaktees.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://breaktees.com/apparel/hockey-jersey/"}, {"name": "Hoodie", "url": "https://breaktees.com/apparel/hoodie/"}, {"name": "Long Sleeve", "url": "https://breaktees.com/apparel/long-sleeve/"}, {"name": "Mother's Day Gifts", "url": "https://breaktees.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://breaktees.com/trending/movie/"}, {"name": "Music", "url": "https://breaktees.com/trending/music/"}, {"name": "Political", "url": "https://breaktees.com/trending/political/"}, {"name": "Special Occasions​", "url": "https://breaktees.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://breaktees.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://breaktees.com/special-occasions/st-patricks-day-gifts/"}, {"name": "Sweatshirt", "url": "https://breaktees.com/apparel/sweatshirt/"}, {"name": "T-Shirt", "url": "https://breaktees.com/apparel/t-shirt/"}, {"name": "Thanksgiving Gifts", "url": "https://breaktees.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://breaktees.com/trending/"}, {"name": "Tumbler", "url": "https://breaktees.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://breaktees.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://breaktees.com/special-occasions/veterans-day-gifts/"}], "product_pool": []}
14	link_config_user_1_store_3	{"mode": "category", "category_links": [{"name": "2D T-Shirt", "url": "https://printedaura.com/apparel/2d-t-shirt/"}, {"name": "3D Hoodie", "url": "https://printedaura.com/apparel/3d-hoodie/"}, {"name": "3D T-Shirt", "url": "https://printedaura.com/apparel/3d-t-shirt/"}, {"name": "Accessories", "url": "https://printedaura.com/accessories/"}, {"name": "Air Force 1", "url": "https://printedaura.com/footwear/air-force-1/"}, {"name": "Air Jordan 1", "url": "https://printedaura.com/footwear/air-jordan-1/"}, {"name": "Air Jordan 11", "url": "https://printedaura.com/footwear/air-jordan-11/"}, {"name": "Air Jordan 13", "url": "https://printedaura.com/footwear/air-jordan-13/"}, {"name": "APPAREL", "url": "https://printedaura.com/apparel/"}, {"name": "Baseball Gifts", "url": "https://printedaura.com/sports-gifts/baseball-gifts/"}, {"name": "Baseball Jersey", "url": "https://printedaura.com/apparel/baseball-jersey/"}, {"name": "Basketball Gifts", "url": "https://printedaura.com/sports-gifts/basketball-gifts/"}, {"name": "Basketball Jersey", "url": "https://printedaura.com/apparel/basketball-jersey/"}, {"name": "Bomber Jacket", "url": "https://printedaura.com/apparel/bomber-jacket/"}, {"name": "Christmas Gifts", "url": "https://printedaura.com/special-occasions/christmas-gifts/"}, {"name": "College Football Gifts", "url": "https://printedaura.com/sports-gifts/college-football-gifts/"}, {"name": "Father's Day Gifts", "url": "https://printedaura.com/special-occasions/fathers-day-gifts/"}, {"name": "Football Gifts", "url": "https://printedaura.com/sports-gifts/football-gifts/"}, {"name": "Football Jersey", "url": "https://printedaura.com/apparel/football-jersey/"}, {"name": "Footwear", "url": "https://printedaura.com/footwear/"}, {"name": "Halloween Gifts", "url": "https://printedaura.com/special-occasions/halloween-gifts/"}, {"name": "Hawaiian Shirt", "url": "https://printedaura.com/apparel/hawaiian-shirt/"}, {"name": "Hockey Gifts", "url": "https://printedaura.com/sports-gifts/hockey-gifts/"}, {"name": "Hockey Jersey", "url": "https://printedaura.com/apparel/hockey-jersey/"}, {"name": "Mother's Day Gifts", "url": "https://printedaura.com/special-occasions/mothers-day-gifts/"}, {"name": "Movie", "url": "https://printedaura.com/trending/movie/"}, {"name": "Music", "url": "https://printedaura.com/trending/music/"}, {"name": "Political", "url": "https://printedaura.com/trending/political/"}, {"name": "Polo Shirt", "url": "https://printedaura.com/apparel/polo-shirt/"}, {"name": "Special Occasions​", "url": "https://printedaura.com/special-occasions/"}, {"name": "SPORTS GIFTS", "url": "https://printedaura.com/sports-gifts/"}, {"name": "St Patrick’s Day Gifts", "url": "https://printedaura.com/special-occasions/st-patricks-day-gifts/"}, {"name": "Sweatshirt", "url": "https://printedaura.com/apparel/sweatshirt/"}, {"name": "Thanksgiving Gifts", "url": "https://printedaura.com/special-occasions/thanksgiving-gifts/"}, {"name": "TRENDING", "url": "https://printedaura.com/trending/"}, {"name": "Tumbler", "url": "https://printedaura.com/accessories/tumbler/"}, {"name": "Valentine's Day Gifts", "url": "https://printedaura.com/special-occasions/valentines-day-gifts/"}, {"name": "Veterans Day Gifts", "url": "https://printedaura.com/special-occasions/veterans-day-gifts/"}], "product_pool": [{"title": "Haebang Yong Guk Red Shadow World Tour 2026 Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/haebang-yong-guk-red-shadow-world-tour-2026-custom-air-force-1-shoes/"}, {"title": "Riley Green Cowboy As It Gets Tour 2026 Custom Air Force 1 Sneaker", "url": "https://printedaura.com/product/riley-green-cowboy-as-it-gets-tour-2026-custom-air-force-1-sneaker/"}, {"title": "Nothing but Thieves Stray Dogs Tour 2026 Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/nothing-but-thieves-stray-dogs-tour-2026-custom-air-force-1-shoes/"}, {"title": "Madonna Confessions II Custom AF1 Shoes", "url": "https://printedaura.com/product/madonna-confessions-ii-custom-af1-shoes/"}, {"title": "Kehlani Midnight Memories World Tour Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/kehlani-midnight-memories-world-tour-custom-air-force-1-shoes/"}, {"title": "CORTIS Put Your Phone Down Tour 2026 Custom Air Force 1 Sneaker", "url": "https://printedaura.com/product/cortis-put-your-phone-down-tour-2026-custom-air-force-1-sneaker/"}, {"title": "Madonna Confessions II Custom AJ1 Shoes", "url": "https://printedaura.com/product/madonna-confessions-ii-custom-aj1-shoes/"}, {"title": "Knocked Loose Hive Mind Tour 2026 Custom AF1 Sneaker", "url": "https://printedaura.com/product/knocked-loose-hive-mind-tour-2026-custom-af1-sneaker/"}, {"title": "San Francisco Giants 'Gigantes' 2026 Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/san-francisco-giants-gigantes-2026-custom-air-force-1-shoes/"}, {"title": "Los Angeles Dodgers x One Piece Night 2026 Custom AF1 Shoes", "url": "https://printedaura.com/product/los-angeles-dodgers-x-one-piece-night-2026-custom-af1-shoes/"}, {"title": "Zayn Malik The Konnakol Tour 2026 Custom AF1 Sneaker", "url": "https://printedaura.com/product/zayn-malik-the-konnakol-tour-2026-custom-af1-sneaker/"}, {"title": "Gracie Abrams Daughter from Hell Custom AF1 Shoes", "url": "https://printedaura.com/product/gracie-abrams-daughter-from-hell-custom-af1-shoes/"}, {"title": "Kidd Voodoo Euforia World Tour 2026 Custom AJ1 Sneaker", "url": "https://printedaura.com/product/kidd-voodoo-euforia-world-tour-2026-custom-aj1-sneaker/"}, {"title": "Gracie Abrams Daughter from Hell Custom AJ1 Shoes", "url": "https://printedaura.com/product/gracie-abrams-daughter-from-hell-custom-aj1-shoes/"}, {"title": "Westlife 25th Anniversary World Tour Custom Air Force 1 Shoes", "url": "https://printedaura.com/product/westlife-25th-anniversary-world-tour-custom-air-force-1-shoes/"}, {"title": "FC Barcelona x Olivia Rodrigo Signature Custom Air Force 1", "url": "https://printedaura.com/product/fc-barcelona-x-olivia-rodrigo-signature-custom-air-force-1/"}, {"title": "Drake Iceman 2026 Custom Air Jordan 1 Shoes", "url": "https://printedaura.com/product/drake-iceman-2026-custom-air-jordan-1-shoes/"}]}
\.


--
-- Data for Name: stores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.stores (id, name, wc_url, wp_username, wp_app_password, store_name, shortcode, created_at) FROM stdin;
1	BreakTees	https://breaktees.com	michael	cTjF 4dWW 3oaz gji7 RqvV BGtO	BreakTees	[thien_display_single_image]	2026-05-13 09:37:41.06791
3	PrintedAura	https://printedaura.com	michael	6dWe PqMM 41z7 R820 bPM0 l9Oa	PrintedAura	[thien_display_single_image]	2026-05-18 04:55:39.954453
\.


--
-- Data for Name: user_stores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_stores (id, user_id, store_id, wp_username, wp_app_password, created_at) FROM stdin;
3	1	1	michael	cTjF 4dWW 3oaz gji7 RqvV BGtO	2026-05-18 09:55:07.94597
8	3	1	seller.mhung	Lzf0 lcTi Mb3K U3UQ lNqf PXhp	2026-05-18 13:54:46.888045
9	3	3	seller.mhung	V5Pc hGXg 6PaO BOm6 TDwi R7I6	2026-05-18 13:54:59.280396
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: woommo
--

COPY public.users (id, username, email, hashed_pw, is_admin, is_active, created_at, wp_username, wp_app_password, store_id, note) FROM stdin;
3	seller.mhung	hunghungg277@gmail.com	$2b$12$.KMZe7cEnS3.NOm6tfof4OKwzw1w2s6Lmr1VZogP9xmFaRoHyY9Ei	f	t	2026-05-07 03:41:38.670449	seller.mhung	kO7U 4q2Y gD6q v2u9 71Sp qmjv	\N	
1	admin	admin@breaktees.com	$2b$12$GtcNSkzzTqfBf247ZF/IVOdsq/P7epZ63lf4F3jrlaNKzyDFxhEA.	t	t	2026-05-05 07:09:28.343375	michael	cTjF 4dWW 3oaz gji7 RqvV BGtO	\N	
\.


--
-- Name: jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: woommo
--

SELECT pg_catalog.setval('public.jobs_id_seq', 1521, true);


--
-- Name: settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: woommo
--

SELECT pg_catalog.setval('public.settings_id_seq', 14, true);


--
-- Name: stores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.stores_id_seq', 3, true);


--
-- Name: user_stores_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_stores_id_seq', 9, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: woommo
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: settings settings_key_key; Type: CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_key_key UNIQUE (key);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: stores stores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stores
    ADD CONSTRAINT stores_pkey PRIMARY KEY (id);


--
-- Name: user_stores user_stores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_stores
    ADD CONSTRAINT user_stores_pkey PRIMARY KEY (id);


--
-- Name: user_stores user_stores_user_id_store_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_stores
    ADD CONSTRAINT user_stores_user_id_store_id_key UNIQUE (user_id, store_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_jobs_id; Type: INDEX; Schema: public; Owner: woommo
--

CREATE INDEX ix_jobs_id ON public.jobs USING btree (id);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: woommo
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: woommo
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: jobs jobs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_stores user_stores_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_stores
    ADD CONSTRAINT user_stores_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.stores(id) ON DELETE CASCADE;


--
-- Name: user_stores user_stores_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_stores
    ADD CONSTRAINT user_stores_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_store_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: woommo
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_store_id_fkey FOREIGN KEY (store_id) REFERENCES public.stores(id);


--
-- Name: TABLE stores; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.stores TO woommo;


--
-- Name: SEQUENCE stores_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.stores_id_seq TO woommo;


--
-- Name: TABLE user_stores; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.user_stores TO woommo;


--
-- Name: SEQUENCE user_stores_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.user_stores_id_seq TO woommo;


--
-- PostgreSQL database dump complete
--

\unrestrict JjzAK0R8wIqDdJWtMx05yWG4j5SnH4IP2F7ujYftObsiYpJn4JU6gqh8rfILufC


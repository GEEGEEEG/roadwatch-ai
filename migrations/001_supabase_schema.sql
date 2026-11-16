-- ============================================================================
-- RoadWatch AI v5.0 — Khởi tạo Cơ sở dữ liệu Supabase PostgreSQL + PostGIS
-- Hướng dẫn: Mở Supabase Dashboard -> SQL Editor -> New Query -> Dán & Bấm RUN
-- ============================================================================

-- 1. Bật tiện ích không gian địa lý PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Bảng quản lý tài khoản cán bộ & phân quyền (RBAC + chống Brute-force)
CREATE TABLE IF NOT EXISTS public.officers (
    username        TEXT PRIMARY KEY,
    password_hash   TEXT NOT NULL,
    full_name       TEXT DEFAULT '',
    unit            TEXT DEFAULT '',
    role            TEXT DEFAULT 'officer' CHECK (role IN ('admin', 'officer', 'field_team')),
    active          INTEGER DEFAULT 1,
    failed_attempts INTEGER DEFAULT 0,
    locked_until    TEXT DEFAULT NULL,
    created_at      TEXT,
    last_login      TEXT
);

-- 3. Bảng hồ sơ phản ánh hư hỏng mặt đường
CREATE TABLE IF NOT EXISTS public.reports (
    id                TEXT PRIMARY KEY,
    created_at        TEXT NOT NULL,
    image_hash        TEXT UNIQUE,
    dhash_64          TEXT DEFAULT '',
    color_vec         TEXT DEFAULT '',
    image_file        TEXT DEFAULT '',
    annotated_file    TEXT DEFAULT '',
    location_name     TEXT DEFAULT '',
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    geom              GEOGRAPHY(Point, 4326),
    gps_source        TEXT DEFAULT '',
    gps_accuracy_m    DOUBLE PRECISION,
    captured_at       TEXT,
    status            TEXT DEFAULT 'pending',
    source            TEXT DEFAULT 'citizen',
    capture_method    TEXT DEFAULT 'upload',
    contact           TEXT DEFAULT '',
    consent           INTEGER DEFAULT 0,
    total_boxes       INTEGER DEFAULT 0,
    "count_D00"       INTEGER DEFAULT 0,
    "count_D10"       INTEGER DEFAULT 0,
    "count_D20"       INTEGER DEFAULT 0,
    "count_D40"       INTEGER DEFAULT 0,
    avg_confidence    DOUBLE PRECISION DEFAULT 0.0,
    bbox_union_pct    DOUBLE PRECISION DEFAULT 0.0,
    damage_area_m2    DOUBLE PRECISION DEFAULT 0.0,
    damage_volume_l   DOUBLE PRECISION DEFAULT 0.0,
    damage_depth_desc TEXT DEFAULT '',
    ai_level          TEXT DEFAULT '',
    ai_score          DOUBLE PRECISION DEFAULT 0.0,
    final_level       TEXT DEFAULT '',
    final_score       DOUBLE PRECISION DEFAULT 0.0,
    road_type         TEXT DEFAULT '',
    road_score        DOUBLE PRECISION DEFAULT 0.0,
    note              TEXT DEFAULT '',
    quality_flags     TEXT DEFAULT '',
    screen_flags      TEXT DEFAULT '',
    detections_json   TEXT DEFAULT '[]',
    elapsed_ms        DOUBLE PRECISION DEFAULT 0.0,
    reviewed_by       TEXT DEFAULT '',
    reviewed_at       TEXT,
    reject_reason     TEXT DEFAULT '',
    assigned_to       TEXT DEFAULT '',
    due_date          TEXT,
    fixed_at          TEXT,
    after_image_file  TEXT,
    after_boxes       INTEGER,
    merged_into       TEXT
);

-- Tự động cập nhật cột không gian PostGIS (geom) mỗi khi ghi/sửa tọa độ
CREATE OR REPLACE FUNCTION public.fn_reports_sync_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL
       AND NEW.latitude BETWEEN -90 AND 90
       AND NEW.longitude BETWEEN -180 AND 180 THEN
        NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    ELSE
        NEW.geom := NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_reports_sync_geom ON public.reports;
CREATE TRIGGER trg_reports_sync_geom
BEFORE INSERT OR UPDATE OF latitude, longitude ON public.reports
FOR EACH ROW EXECUTE FUNCTION public.fn_reports_sync_geom();

-- 4. Bảng lịch sử thẩm định & luân chuyển trạng thái (Audit Trail)
CREATE TABLE IF NOT EXISTS public.report_history (
    id          BIGSERIAL PRIMARY KEY,
    report_id   TEXT NOT NULL REFERENCES public.reports(id) ON DELETE CASCADE,
    ts          TEXT NOT NULL,
    status      TEXT NOT NULL,
    actor       TEXT DEFAULT '',
    note        TEXT DEFAULT ''
);

-- 5. Bảng cấu hình hệ thống động (lưu ma trận AHP, đơn giá vật tư...)
CREATE TABLE IF NOT EXISTS public.app_settings (
    key         TEXT PRIMARY KEY,
    value_json  TEXT NOT NULL,
    updated_at  TEXT,
    updated_by  TEXT DEFAULT ''
);

-- 6. Các chỉ mục tối ưu tốc độ truy vấn & bản đồ không gian
CREATE INDEX IF NOT EXISTS idx_reports_status ON public.reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at);
CREATE INDEX IF NOT EXISTS idx_reports_merged_into ON public.reports(merged_into);
CREATE INDEX IF NOT EXISTS idx_reports_geom ON public.reports USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_report_history_report_id ON public.report_history(report_id);

-- 7. Khởi tạo Bucket lưu trữ ảnh (nếu chưa tạo trên giao diện Storage)
INSERT INTO storage.buckets (id, name, public)
VALUES ('roadwatch-data', 'roadwatch-data', true)
ON CONFLICT (id) DO NOTHING;

-- 8. Bảo mật Row Level Security (RLS)
-- Khuyến nghị đặt SUPABASE_SERVICE_ROLE_KEY trong Streamlit Secrets (chỉ chạy phía Server).
-- Service Role tự động vượt qua RLS một cách an toàn tuyệt đối.
ALTER TABLE public.officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY;

-- Cho phép đọc công khai các điểm đã xác minh trên REST nếu cần tích hợp bên ngoài:
DROP POLICY IF EXISTS "public_read_verified_reports" ON public.reports;
CREATE POLICY "public_read_verified_reports"
ON public.reports FOR SELECT
TO anon
USING (status IN ('verified', 'assigned', 'fixed'));

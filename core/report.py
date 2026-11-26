"""Báo cáo hành chính cho cán bộ (RoadWatch AI v5.0):
1. Phiếu giao việc & kiểm tra hiện trường (1 điểm nóng) — PDF / Word .docx / Markdown
2. Báo cáo tổng hợp định kỳ (tuần / tháng / khoảng ngày) — PDF / Word .docx / CSV
3. Biên bản nghiệm thu sau sửa chữa (Trước / Sau) — PDF / Word .docx
Tích hợp nhận xét hỗ trợ từ Gemini REST (chỉ diễn giải, không bịa số liệu).
"""
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from .config import PROJECT_ROOT, cfg, now_vn, today_vn
from .constants import ACTIVE_STATUSES, DISCLAIMER
from .docx_export import AdminDocxBuilder

GEMINI_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
DEFAULT_GEMINI_MODELS = ('gemini-4-hydrogen', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite')
GEMINI_SYSTEM = (
    'Bạn là trợ lý kỹ thuật hỗ trợ cán bộ quản lý duy tu đường bộ đô thị tại Việt Nam. '
    'Viết tiếng Việt, văn phong hành chính - kỹ thuật, ngắn gọn, tự nhiên, rõ ràng. '
    'Quy tắc bắt buộc: '
    '(1) Chỉ dùng các con số có sẵn trong hồ sơ; tuyệt đối không bịa thêm số liệu, kích thước, nguyên nhân hay chi phí; '
    '(2) Luôn dùng từ "hư hỏng" cho mặt đường, tuyệt đối không dùng từ y khoa như "tổn thương"; '
    '(3) Không đệm số 0 trước số đếm (viết "1 vùng", "3 ổ gà", không viết "01 vùng", "03 ổ gà"); '
    '(4) Thống nhất dùng dấu chấm "." cho số thập phân như trong hồ sơ (ví dụ 0.78, 22.5%), không trộn dấu phẩy; '
    '(5) Viết văn bản thuần dễ chỉnh sửa, không dùng ký tự Markdown như ** hoặc #; '
    '(6) Nêu rõ nội dung chỉ là khuyến nghị hỗ trợ, không phải kết luận kỹ thuật.'
)
GEMINI_TASK = (
    'Dựa trên hồ sơ dưới đây, viết đúng 4 mục văn bản thuần (không dùng ** hay #), '
    'mỗi mục có 1 dòng tiêu đề rồi 1-3 gạch đầu dòng bắt đầu bằng "- ":\n'
    'Nhận định tình trạng:\n'
    'Mức độ rủi ro giao thông:\n'
    'Phương án xử lý đề xuất: (gợi ý theo phần dự toán vật tư sơ bộ nếu có)\n'
    'Mức khẩn cấp kiểm tra: (chọn một: Trong 24 giờ / Trong 3 ngày / Trong 7 ngày / Theo kế hoạch định kỳ)\n'
    'Không chép lại nguyên văn hồ sơ.'
)
GEMINI_PERIODIC_TASK = (
    'Dựa trên số liệu tổng hợp kỳ báo cáo dưới đây, viết Tóm tắt điều hành văn bản thuần (không dùng ** hay #) '
    'gồm đúng 3 mục, mỗi mục 2-3 gạch đầu dòng bắt đầu bằng "- ":\n'
    'Đánh giá chung tiến độ kỳ báo cáo:\n'
    'Điểm hư hỏng & cảnh báo cần lưu ý:\n'
    'Đề xuất phân bổ nguồn lực kỳ tới:\n'
    'Chỉ sử dụng đúng con số trong bảng số liệu, không bịa thêm số liệu.'
)
GEMINI_ACCEPTANCE_TASK = (
    'Dựa trên biên bản đối chiếu trước/sau sửa chữa dưới đây, viết văn bản thuần (không dùng ** hay #) '
    'gồm đúng 2 mục, mỗi mục 1-2 gạch đầu dòng bắt đầu bằng "- ":\n'
    'Nhận xét kết quả đối chiếu trước/sau:\n'
    'Lưu ý nghiệm thu tại hiện trường: (nhắc kiểm tra độ phẳng, bám dính mép vá và an toàn giao thông)\n'
    'Nêu rõ nhận xét tự động chỉ mang tính hỗ trợ, kết luận nghiệm thu do cán bộ thực địa chịu trách nhiệm.'
)


class GeminiError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(f'HTTP {code}: {message}')
        self.code = int(code)
        self.message = str(message or '')


def gemini_models() -> list[str]:
    """Model chain: optional ROADWATCH_GEMINI_MODEL first, then current defaults."""
    custom = cfg('ROADWATCH_GEMINI_MODEL', '').strip()
    chain = [custom] if custom else []
    chain += [m for m in DEFAULT_GEMINI_MODELS if m != custom]
    return chain


def _gemini_call(model: str, key: str, prompt: str, timeout: int = 45, thinking: bool = True) -> str:
    body = {
        'systemInstruction': {'parts': [{'text': GEMINI_SYSTEM}]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
    }
    if thinking:
        body['generationConfig'] = {'thinkingConfig': {'thinkingLevel': 'low'}}
    req = urllib.request.Request(
        GEMINI_ENDPOINT.format(model=urllib.parse.quote(model, safe='-._')),
        data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': key},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='ignore')
        try:
            msg = (json.loads(raw).get('error') or {}).get('message', '')
        except Exception:
            msg = raw
        raise GeminiError(exc.code, (msg or str(exc))[:240]) from exc
    cands = data.get('candidates') or [{}]
    parts = (cands[0].get('content') or {}).get('parts') or []
    return '\n'.join(p['text'] for p in parts if p.get('text') and not p.get('thought')).strip()


def _explain_gemini_error(e: GeminiError, key: str) -> str:
    msg = e.message.replace(key, '***') if key else e.message
    low = msg.lower()
    if e.code == 400 and ('api key' in low or 'api_key' in low):
        return 'HTTP 400 - GEMINI_API_KEY không hợp lệ'
    if e.code in (401, 403):
        return f'HTTP {e.code} - key không có quyền hoặc chưa bật Generative Language API'
    if e.code == 404:
        return 'HTTP 404 - model không tồn tại hoặc đã ngừng hỗ trợ'
    if e.code == 429:
        return 'HTTP 429 - hết hạn mức (quota) miễn phí, thử lại sau'
    if e.code == 503:
        return 'HTTP 503 - máy chủ model đang quá tải tạm thời'
    return f'HTTP {e.code} - {msg[:160]}'


def _run_gemini(prompt: str, gemini_key: str = '') -> tuple[str | None, str]:
    """Run Gemini REST with model fallback; returns (note_or_None, status_label)."""
    key = (gemini_key or '').strip()
    if not key:
        return None, 'Mẫu cố định (không có Gemini API)'
    last = 'không có model khả dụng'
    for model in gemini_models():
        try:
            try:
                note = _gemini_call(model, key, prompt)
            except GeminiError as e:
                if e.code == 400 and 'thinking' in e.message.lower():
                    note = _gemini_call(model, key, prompt, thinking=False)
                else:
                    raise
        except GeminiError as e:
            last = f'{model}: {_explain_gemini_error(e, key)}'
            if e.code in (404, 429, 500, 502, 503, 504) or (
                e.code == 400 and 'model' in e.message.lower() and 'key' not in e.message.lower()
            ):
                continue
            return None, f'Mẫu cố định (Gemini lỗi {last})'
        except (urllib.error.URLError, TimeoutError, OSError):
            return None, 'Mẫu cố định (Gemini không kết nối được mạng hoặc quá thời gian chờ)'
        if note:
            return note.replace('**', ''), f'Gemini ({model}) + mẫu số liệu cố định'
        last = f'{model} trả về nội dung trống'
    return None, f'Mẫu cố định (Gemini lỗi {last})'


def _vnd(x) -> str:
    return f'{int(round(float(x or 0))):,} VNĐ'.replace(',', '.')


def _num(v) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.0
    return f if f == f else 0.0


def _vn_date_str(city: str = 'Đà Nẵng') -> str:
    now = now_vn()
    return f'{city}, ngày {now.day:02d} tháng {now.month:02d} năm {now.year}'


# ── 1. PHIẾU GIAO VIỆC & KIỂM TRA HIỆN TRƯỜNG (1 ĐIỂM NÓNG) ───────────────

def hotspot_record(hs_row, reports_df):
    """Gộp điểm nóng + bản ghi nặng nhất thành dict dùng cho báo cáo."""
    worst = reports_df[reports_df.id == hs_row['worst_report_id']].iloc[0].to_dict()
    members = reports_df[reports_df.id.isin(hs_row['member_ids'])]
    rec = {**worst, **{k: hs_row[k] for k in (
        'hotspot_id', 'report_count', 'priority_score', 'priority_rank', 'ranking_reason', 'trend_bonus',
        'weather_bonus', 'first_seen', 'last_seen')}}
    rec['location_name'] = hs_row['location_name']
    rec['latitude'], rec['longitude'] = hs_row['latitude'], hs_row['longitude']
    rec['notes'] = list(dict.fromkeys(n.strip() for n in members.note.fillna('').tolist() if n.strip()))
    rec['member_ids'] = list(hs_row['member_ids'])
    return rec


def cost_for_hotspot(rec, reports_df, custom_prices=None) -> dict:
    """Preliminary material/labour estimate for all verified reports of the hotspot."""
    from .cost_estimation import estimate_maintenance_cost
    ids = rec.get('member_ids') or [rec.get('id')]
    members = reports_df[reports_df.id.isin(ids)]
    if members.empty:
        area, vol = 0.15, 5.0
    else:
        area = float(pd.to_numeric(members['damage_area_m2'], errors='coerce').fillna(0.15).clip(lower=0.05).sum())
        vol = float(pd.to_numeric(members['damage_volume_l'], errors='coerce').fillna(5.0).clip(lower=0.0).sum())
    return estimate_maintenance_cost(area, vol, point_count=len(members) or 1, custom_prices=custom_prices)


def report_sections(r):
    n = lambda k: int(float(r.get(k, 0) or 0))
    obs_lines = [
        f"D00 (nứt dọc): {n('count_D00')} vùng; D10 (nứt ngang): {n('count_D10')} vùng.",
        f"D20 (nứt mạng): {n('count_D20')} vùng; D40 (ổ gà): {n('count_D40')} vùng.",
        f"Độ tin cậy trung bình các vùng phát hiện: {r['avg_confidence']}.",
        f"Tỷ lệ vùng hư hỏng trên ảnh: {r['bbox_union_pct']}%.",
    ]
    area = _num(r.get('damage_area_m2'))
    if area > 0:
        vol = _num(r.get('damage_volume_l'))
        obs_lines.append(
            f"Diện tích hư hỏng ước tính từ ảnh: {area:.2f} m²; thể tích vá ước tính: {vol:.1f} lít ({str(r.get('damage_depth_desc') or 'chưa phân loại').replace('Tổn thương', 'Hư hỏng')})."
        )

    road_clean = str(r.get('road_type') or '').replace(' (minh họa)', '')
    sections = [
        ('Thông tin điểm hư hỏng', [
            f"Mã phản ánh trọng tâm: {r['id']}", f"Thời điểm ghi nhận: {r['created_at']}",
            f"Vị trí: {r['location_name']}", f"Tọa độ: {r['latitude']}, {r['longitude']} (nguồn: {r['gps_source']})",
            f"Số phản ánh đã xác minh tại điểm: {n('report_count')} ({r.get('first_seen')} đến {r.get('last_seen')})"]),
        ('1. Quan sát từ mô hình nhận diện', obs_lines),
        ('2. Đánh giá sơ bộ và xếp hạng', [
            f"Gợi ý sơ bộ từ quy tắc: {r['ai_level']}. Mức do cán bộ xác nhận: {r['final_level']}.",
            f"Điểm mức độ: {r['final_score']}/100. Cấp đường: {road_clean} (điểm {r['road_score']}).",
            f"Điểm ưu tiên: {r['priority_score']}/100; thứ hạng: {n('priority_rank')}.",
            f"Cách tính: {r['ranking_reason']}."]),
    ]
    est = r.get('cost_estimate')
    if est:
        sections.append(('Dự toán vật tư sơ bộ (tham khảo)', [
            f"Diện tích vá dự kiến: {est['area_m2']} m² · {est['point_count']} vị trí.",
            f"Phương án vật tư: {est['material_detail']}.",
            f"Vật tư: {_vnd(est['material_cost_vnd'])} · Nhân công & máy: {_vnd(est['labor_cost_vnd'])}.",
            f"Tổng dự toán sơ bộ: {est['formatted_total']} (đơn giá theo cấu hình Quản trị; cần bóc tách khối lượng thực tế).",
        ]))
    sections += [
        ('3. Hành động đề xuất', [
            'Đề nghị cán bộ kỹ thuật kiểm tra hiện trường trước khi kết luận và chọn phương án xử lý.',
            'Không dựa riêng vào ảnh 2D để đo độ sâu ổ gà, diện tích thực, rủi ro tai nạn hay chi phí.']),
        ('Ghi chú', r.get('notes') or ['(không có)']),
    ]
    return sections


def template_markdown(r):
    parts = ['# ROADWATCH AI — PHIẾU ĐỀ XUẤT KIỂM TRA HIỆN TRƯỜNG\n']
    for title, lines in report_sections(r):
        parts.append(f'## {title}\n' + '\n'.join(f'- {x}' for x in lines) + '\n')
    parts.append(f'**Trạng thái:** {DISCLAIMER}\n')
    return '\n'.join(parts)


def generate_report(r, gemini_key=''):
    fixed = template_markdown(r)
    note, method = _run_gemini(GEMINI_TASK + '\n\nHỒ SƠ:\n' + fixed, gemini_key)
    if note:
        return fixed + '\n## 4. Gợi ý diễn giải từ Gemini (cần người duyệt)\n' + note, method
    return fixed, method


# ── SHARED PDF HELPERS ────────────────────────────────────────────────────

def _pdf_ctx():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape

    font_pairs = [
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('/usr/share/fonts/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'),
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
    ]
    pair = next(((a, b) for a, b in font_pairs if os.path.isfile(a) and os.path.isfile(b)), None)
    if pair is None:
        raise RuntimeError('Không tìm thấy font hệ thống hỗ trợ tiếng Việt. Cài fonts-dejavu-core trên máy chủ.')
    if 'DejaVu' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVu', pair[0]))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', pair[1]))

    styles = {
        'body': ParagraphStyle('b', fontName='DejaVu', fontSize=9.5, leading=13.5),
        'small': ParagraphStyle('sm', fontName='DejaVu', fontSize=8.5, leading=11.5, textColor=colors.HexColor('#334155')),
        'center': ParagraphStyle('c', fontName='DejaVu', fontSize=9.5, leading=13, alignment=TA_CENTER),
        'center_b': ParagraphStyle('cb', fontName='DejaVu-Bold', fontSize=9.5, leading=13, alignment=TA_CENTER),
        'h1': ParagraphStyle('h1', fontName='DejaVu-Bold', fontSize=13.5, leading=18, alignment=TA_CENTER, spaceBefore=8, spaceAfter=4),
        'h2': ParagraphStyle('h2', fontName='DejaVu-Bold', fontSize=11, leading=14.5, spaceBefore=8, spaceAfter=3, textColor=colors.HexColor('#0F172A')),
        'th': ParagraphStyle('th', fontName='DejaVu-Bold', fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.white),
        'td': ParagraphStyle('td', fontName='DejaVu', fontSize=8.5, leading=11.5),
    }
    return {
        'A4': A4, 'cm': cm, 'colors': colors, 'escape': escape,
        'RLImage': RLImage, 'Paragraph': Paragraph, 'SimpleDocTemplate': SimpleDocTemplate,
        'Spacer': Spacer, 'Table': Table, 'TableStyle': TableStyle, 'styles': styles,
    }


def _pdf_admin_header(ctx, meta: dict) -> list:
    P, T, TS, s, cm, esc = ctx['Paragraph'], ctx['Table'], ctx['TableStyle'], ctx['styles'], ctx['cm'], ctx['escape']
    parent = (meta.get('parent_org') or 'SỞ XÂY DỰNG / BAN QUẢN LÝ HẠ TẦNG ĐÔ THỊ').upper()
    unit = (meta.get('unit') or 'ĐỘI QUẢN LÝ & DUY TU ĐƯỜNG BỘ').upper()
    doc_no = meta.get('doc_no') or 'Số: .../RW-BC'
    city = meta.get('city') or 'Đà Nẵng'
    date_str = meta.get('date_str') or _vn_date_str(city)
    left = [
        P(esc(parent), s['center']),
        P(esc(unit), s['center_b']),
        P(esc(doc_no), s['center']),
    ]
    right = [
        P('CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', s['center_b']),
        P('Độc lập - Tự do - Hạnh phúc', s['center_b']),
        P('--------------', s['center']),
        P(esc(date_str), s['center']),
    ]
    tbl = T([[left, right]], colWidths=[8.0 * cm, 9.0 * cm])
    tbl.setStyle(TS([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return [tbl, ctx['Spacer'](1, 6)]


def _pdf_signature(ctx, left_title: str, left_name: str, right_title: str, right_name: str) -> list:
    P, T, TS, s, cm, esc = ctx['Paragraph'], ctx['Table'], ctx['TableStyle'], ctx['styles'], ctx['cm'], ctx['escape']
    left = [
        P(esc(left_title.upper()), s['center_b']),
        P('(Ký, ghi rõ họ tên)', s['center']),
        ctx['Spacer'](1, 34),
        P(esc(left_name or '.................................'), s['center_b'] if left_name else s['center']),
    ]
    right = [
        P(esc(right_title.upper()), s['center_b']),
        P('(Ký, ghi rõ họ tên)', s['center']),
        ctx['Spacer'](1, 34),
        P(esc(right_name or '.................................'), s['center_b'] if right_name else s['center']),
    ]
    tbl = T([[left, right]], colWidths=[8.5 * cm, 8.5 * cm])
    tbl.setStyle(TS([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    return [ctx['Spacer'](1, 10), tbl]


def _pdf_extra_block(ctx, heading: str, extra_text: str) -> list:
    if not extra_text or not str(extra_text).strip():
        return []
    P, s, esc = ctx['Paragraph'], ctx['styles'], ctx['escape']
    out = [P(esc(heading), s['h2'])]
    for line in str(extra_text).splitlines():
        txt = line.strip().replace('**', '')
        if not txt:
            continue
        if txt[:2] in ('- ', '* '):
            txt = '• ' + txt[2:]
        out.append(P(esc(txt), s['body']))
    return out


def _pdf_fit_image(ctx, image_path, max_w_cm: float, max_h_cm: float = 9.5):
    if not image_path or not Path(image_path).is_file():
        return None
    from PIL import Image as PILImage
    with PILImage.open(image_path) as im:
        w, h = im.size
    cm = ctx['cm']
    width = max_w_cm * cm
    height = width * h / max(1, w)
    if height > max_h_cm * cm:
        scale = (max_h_cm * cm) / height
        width *= scale
        height *= scale
    return ctx['RLImage'](str(image_path), width=width, height=height)


def _pdf_data_table(ctx, headers: list[str], rows: list[list[str]], col_widths_cm: list[float]):
    P, T, TS, s, cm, c, esc = ctx['Paragraph'], ctx['Table'], ctx['TableStyle'], ctx['styles'], ctx['cm'], ctx['colors'], ctx['escape']
    data = [[P(esc(h), s['th']) for h in headers]]
    for row in rows:
        data.append([P(esc(str(v)), s['td']) for v in row])
    tbl = T(data, colWidths=[w * cm for w in col_widths_cm], repeatRows=1)
    tbl.setStyle(TS([
        ('BACKGROUND', (0, 0), (-1, 0), c.HexColor('#1E3A5F')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [c.white, c.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.4, c.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _parse_edited_markdown(md_text: str) -> list[tuple[str, list[str]]]:
    """Parse edited Markdown into (heading, lines) sections for PDF/DOCX export."""
    sections: list[tuple[str, list[str]]] = []
    cur_title = ''
    cur_lines: list[str] = []
    for raw in str(md_text or '').splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith('# ') and not s.startswith('## '):
            continue
        if s.startswith('**Trạng thái:**'):
            continue
        if s.startswith('## '):
            if cur_title or cur_lines:
                sections.append((cur_title or 'Nội dung phiếu', cur_lines))
            cur_title = s[3:].strip()
            cur_lines = []
        else:
            clean = s[2:].strip() if s[:2] in ('- ', '* ') else s
            cur_lines.append(clean.replace('**', ''))
    if cur_title or cur_lines:
        sections.append((cur_title or 'Nội dung phiếu', cur_lines))
    return sections


def build_pdf(r, image_path=None, extra_text='', meta: dict | None = None, edited_markdown: str | None = None):
    """PDF tiếng Việt cho Phiếu giao việc & kiểm tra hiện trường (1 điểm nóng)."""
    ctx = _pdf_ctx()
    P, s, cm, esc = ctx['Paragraph'], ctx['styles'], ctx['cm'], ctx['escape']
    buf = io.BytesIO()
    doc = ctx['SimpleDocTemplate'](buf, pagesize=ctx['A4'], leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    story = []
    if meta:
        story += _pdf_admin_header(ctx, meta)
        story.append(P('PHIẾU GIAO VIỆC &amp; KIỂM TRA HIỆN TRƯỜNG', s['h1']))
        assign_rows = [
            ['Đơn vị / Đội thực hiện', meta.get('assignee') or '(Chưa phân công)'],
            ['Hạn hoàn thành kiểm tra', meta.get('due_date') or '(Theo kế hoạch)'],
            ['Mã hồ sơ trọng tâm', str(r.get('id') or '')],
            ['Địa điểm hiện trường', str(r.get('location_name') or '')],
        ]
        story.append(_pdf_data_table(ctx, ['Hạng mục điều phối', 'Nội dung'], assign_rows, [5.5, 11.5]))
        story.append(ctx['Spacer'](1, 6))
    else:
        story.append(P('ROADWATCH AI — PHIẾU ĐỀ XUẤT KIỂM TRA HIỆN TRƯỜNG', s['h1']))

    use_edited = bool(edited_markdown and str(edited_markdown).strip())
    sections = _parse_edited_markdown(edited_markdown) if use_edited else report_sections(r)
    img_placed = False
    for title, lines in sections:
        story.append(P(esc(title), s['h2']))
        for line in lines:
            story.append(P('• ' + esc(str(line)), s['body']))
        if not img_placed and title.startswith('1.'):
            img = _pdf_fit_image(ctx, image_path, 13.5, 8.8)
            if img is not None:
                story += [ctx['Spacer'](1, 5), img]
                img_placed = True
    if not img_placed:
        img = _pdf_fit_image(ctx, image_path, 13.5, 8.8)
        if img is not None:
            story += [ctx['Spacer'](1, 5), img]

    if not use_edited:
        story += _pdf_extra_block(ctx, 'Gợi ý diễn giải từ Gemini (cần người duyệt)', extra_text)
    story += [ctx['Spacer'](1, 8), P(esc(DISCLAIMER.replace('**', '')), s['small'])]
    if meta:
        story += _pdf_signature(
            ctx,
            'Người lập phiếu', meta.get('prepared_by', ''),
            'Lãnh đạo phê duyệt', meta.get('approver', ''),
        )
    doc.build(story)
    return buf.getvalue()


def build_work_order_docx(r, image_path=None, extra_text='', meta: dict | None = None, edited_markdown: str | None = None) -> bytes:
    """Word .docx chuẩn hành chính cho Phiếu giao việc & kiểm tra hiện trường (1 điểm nóng)."""
    m = meta or {}
    doc = AdminDocxBuilder()
    doc.add_admin_header(
        parent_org=m.get('parent_org') or 'SỞ XÂY DỰNG / BAN QUẢN LÝ HẠ TẦNG ĐÔ THỊ',
        unit_name=m.get('unit') or 'ĐỘI QUẢN LÝ & DUY TU ĐƯỜNG BỘ',
        doc_no=m.get('doc_no') or 'Số: .../RW-GV',
        city=m.get('city') or 'Đà Nẵng',
    )
    doc.add_title('PHIẾU GIAO VIỆC & KIỂM TRA HIỆN TRƯỜNG', f"Mã hồ sơ: {r.get('id', '')}")
    doc.add_kv_table([
        ('Đơn vị / Đội thực hiện', m.get('assignee') or '(Chưa phân công)'),
        ('Hạn hoàn thành kiểm tra', m.get('due_date') or '(Theo kế hoạch)'),
        ('Vị trí hiện trường', str(r.get('location_name') or '')),
        ('Tọa độ GPS', f"{r.get('latitude')}, {r.get('longitude')} ({r.get('gps_source')})"),
    ])
    use_edited = bool(edited_markdown and str(edited_markdown).strip())
    sections = _parse_edited_markdown(edited_markdown) if use_edited else report_sections(r)
    img_placed = False
    for title, lines in sections:
        doc.add_heading(title)
        doc.add_bullets([str(x) for x in lines])
        if not img_placed and title.startswith('1.') and image_path:
            doc.add_image(image_path, caption=f"Ảnh AI đánh dấu vùng hư hỏng ({r.get('id', '')})")
            img_placed = True
    if not img_placed and image_path:
        doc.add_image(image_path, caption=f"Ảnh AI đánh dấu vùng hư hỏng ({r.get('id', '')})")
    if not use_edited and extra_text and str(extra_text).strip():
        doc.add_heading('4. Gợi ý diễn giải từ Gemini (cần người duyệt)')
        for line in str(extra_text).splitlines():
            s = line.strip().replace('**', '')
            if not s:
                continue
            if s[:2] in ('- ', '* '):
                doc.add_bullets([s[2:]])
            else:
                doc.add_paragraph(s, bold=True)
    doc.add_paragraph(DISCLAIMER.replace('**', ''), italic=True, size_pt=9.5)
    doc.add_signature_block(
        left_title='Người lập phiếu',
        left_name=m.get('prepared_by', ''),
        right_title='Lãnh đạo phê duyệt',
        right_name=m.get('approver', ''),
    )
    return doc.to_bytes()


# ── 2. BÁO CÁO TỔNG HỢP ĐỊNH KỲ (TUẦN / THÁNG / KHOẢNG NGÀY) ──────────────

def build_periodic_summary(df: pd.DataFrame, hs: pd.DataFrame, start_date, end_date, custom_prices=None) -> dict:
    """Tổng hợp số liệu vận hành và dự toán duy tu trong một khoảng thời gian."""
    d = df.copy() if df is not None and not df.empty else pd.DataFrame()
    if not d.empty:
        created = pd.to_datetime(d['created_at'], errors='coerce')
        mask = (created.dt.date >= start_date) & (created.dt.date <= end_date)
        d_period = d[mask].copy()
    else:
        d_period = pd.DataFrame()

    total = len(d_period)
    by_status = d_period['status'].value_counts().to_dict() if not d_period.empty else {}
    n_pending = int(by_status.get('pending', 0))
    n_verified = int(by_status.get('verified', 0))
    n_assigned = int(by_status.get('assigned', 0))
    n_fixed = int(by_status.get('fixed', 0))
    n_rejected = int(by_status.get('rejected', 0))
    n_merged = int(by_status.get('merged', 0))

    denom = n_verified + n_assigned + n_fixed
    completion_pct = round(100.0 * n_fixed / denom, 1) if denom > 0 else 0.0

    # Số hồ sơ đang giao bị quá hạn SLA
    overdue_count = 0
    if not d.empty and 'due_date' in d.columns:
        assigned = d[d['status'] == 'assigned']
        if not assigned.empty:
            due = pd.to_datetime(assigned['due_date'], errors='coerce').dt.date
            overdue_count = int((due < today_vn()).sum())

    defects = {}
    for code in ('D00', 'D10', 'D20', 'D40'):
        col = f'count_{code}'
        defects[code] = int(pd.to_numeric(d_period[col], errors='coerce').fillna(0).sum()) if (not d_period.empty and col in d_period.columns) else 0

    # Bảng Top điểm nóng đang hoạt động (kèm dự toán)
    top_rows = []
    tot_area = 0.0
    tot_cost = 0
    if hs is not None and not hs.empty and df is not None and not df.empty:
        for h in hs.itertuples():
            rec = hotspot_record(h._asdict(), df)
            est = cost_for_hotspot(rec, df, custom_prices=custom_prices)
            tot_area += est['area_m2']
            tot_cost += est['total_estimate_vnd']
            top_rows.append({
                'Hạng': int(h.priority_rank),
                'Vị trí / Tuyến đường': str(h.location_name),
                'Mức độ': str(h.severity_label),
                'Số phản ánh': int(h.report_count),
                'Điểm ưu tiên': round(float(h.priority_score), 1),
                'Diện tích (m²)': est['area_m2'],
                'Phương án vật tư': est['material_detail'],
                'Dự toán (VNĐ)': est['formatted_total'],
                '_cost_vnd': est['total_estimate_vnd'],
            })

    table_df = pd.DataFrame(top_rows).drop(columns=['_cost_vnd'], errors='ignore') if top_rows else pd.DataFrame(
        columns=['Hạng', 'Vị trí / Tuyến đường', 'Mức độ', 'Số phản ánh', 'Điểm ưu tiên', 'Diện tích (m²)', 'Phương án vật tư', 'Dự toán (VNĐ)']
    )

    return {
        'start_date': str(start_date),
        'end_date': str(end_date),
        'total_reports': total,
        'pending': n_pending,
        'verified': n_verified,
        'assigned': n_assigned,
        'fixed': n_fixed,
        'rejected': n_rejected,
        'merged': n_merged,
        'completion_pct': completion_pct,
        'overdue_count': overdue_count,
        'defects': defects,
        'active_hotspots': len(top_rows),
        'total_area_m2': round(tot_area, 2),
        'total_cost_vnd': int(tot_cost),
        'formatted_total_cost': _vnd(tot_cost),
        'top_rows': top_rows,
        'table_df': table_df,
    }


def periodic_summary_text(summary: dict) -> str:
    d = summary['defects']
    lines = [
        f"Kỳ báo cáo: từ {summary['start_date']} đến {summary['end_date']}",
        f"- Tổng số phản ánh tiếp nhận trong kỳ: {summary['total_reports']} hồ sơ.",
        f"- Phân trạng thái: Chờ xác minh {summary['pending']} | Đã xác minh {summary['verified']} | Đang giao duy tu {summary['assigned']} | Đã hoàn thành sửa chữa {summary['fixed']} | Từ chối {summary['rejected']} | Đã gộp trùng {summary['merged']}.",
        f"- Tỷ lệ hoàn thành xử lý trên tổng hồ sơ hợp lệ: {summary['completion_pct']}%.",
        f"- Số nhiệm vụ đang giao bị quá hạn SLA hiện tại: {summary['overdue_count']} hồ sơ.",
        f"- Cơ cấu hư hỏng AI ghi nhận trong kỳ: D00 (nứt dọc)={d['D00']}, D10 (nứt ngang)={d['D10']}, D20 (nứt mạng)={d['D20']}, D40 (ổ gà)={d['D40']}.",
        f"- Điểm nóng đang cần xử lý: {summary['active_hotspots']} điểm; tổng diện tích vá ước tính {summary['total_area_m2']} m²; tổng kinh phí dự toán sơ bộ {summary['formatted_total_cost']}.",
    ]
    if summary['top_rows']:
        lines.append('- Top 5 điểm ưu tiên hàng đầu:')
        for r in summary['top_rows'][:5]:
            lines.append(f"  + #{r['Hạng']} {r['Vị trí / Tuyến đường']} ({r['Mức độ']}, điểm {r['Điểm ưu tiên']}/100, {r['Số phản ánh']} phản ánh, dự toán {r['Dự toán (VNĐ)']}).")
    return '\n'.join(lines)


def generate_periodic_note(summary: dict, gemini_key: str = '') -> tuple[str, str]:
    ctx_txt = periodic_summary_text(summary)
    note, method = _run_gemini(GEMINI_PERIODIC_TASK + '\n\nSỐ LIỆU KỲ BÁO CÁO:\n' + ctx_txt, gemini_key)
    if note:
        return note, method
    fallback = (
        'Đánh giá chung tiến độ kỳ báo cáo:\n'
        f"- Trong kỳ ({summary['start_date']} đến {summary['end_date']}), hệ thống tiếp nhận {summary['total_reports']} phản ánh, hoàn thành sửa chữa {summary['fixed']} điểm (tỷ lệ {summary['completion_pct']}%).\n"
        'Điểm hư hỏng & cảnh báo cần lưu ý:\n'
        f"- Hiện còn {summary['active_hotspots']} điểm hư hỏng đang mở và {summary['overdue_count']} nhiệm vụ quá hạn cần đôn đốc.\n"
        'Đề xuất phân bổ nguồn lực kỳ tới:\n'
        f"- Dự trù kinh phí sơ bộ cho các điểm đang mở khoảng {summary['formatted_total_cost']} (cần rà soát khối lượng thực địa trước khi phê duyệt)."
    )
    return fallback, method


def build_periodic_pdf(summary: dict, exec_note: str = '', meta: dict | None = None) -> bytes:
    ctx = _pdf_ctx()
    P, s, cm, esc = ctx['Paragraph'], ctx['styles'], ctx['cm'], ctx['escape']
    m = meta or {}
    buf = io.BytesIO()
    doc = ctx['SimpleDocTemplate'](buf, pagesize=ctx['A4'], leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    story = _pdf_admin_header(ctx, m)
    story.append(P('BÁO CÁO TỔNG HỢP CÔNG TÁC GIÁM SÁT &amp; DUY TU MẶT ĐƯỜNG', s['h1']))
    story.append(P(esc(f"Kỳ báo cáo: từ ngày {summary['start_date']} đến ngày {summary['end_date']}"), s['center']))
    story.append(ctx['Spacer'](1, 8))

    story.append(P('1. Tổng hợp chỉ tiêu vận hành trong kỳ', s['h2']))
    d = summary['defects']
    kpi_rows = [
        ['Tổng phản ánh tiếp nhận', str(summary['total_reports']), 'Chờ xác minh', str(summary['pending'])],
        ['Đã xác minh / Đang giao', f"{summary['verified']} / {summary['assigned']}", 'Đã hoàn thành sửa chữa', f"{summary['fixed']} ({summary['completion_pct']}%)"],
        ['Từ chối / Đã gộp trùng', f"{summary['rejected']} / {summary['merged']}", 'Quá hạn SLA hiện tại', str(summary['overdue_count'])],
        ['Điểm nóng đang mở', str(summary['active_hotspots']), 'Tổng dự toán sơ bộ', summary['formatted_total_cost']],
    ]
    story.append(_pdf_data_table(ctx, ['Chỉ tiêu', 'Giá trị', 'Chỉ tiêu', 'Giá trị'], kpi_rows, [4.8, 3.7, 4.8, 4.1]))
    story.append(ctx['Spacer'](1, 4))
    story.append(P(esc(f"Cơ cấu vùng hư hại AI ghi nhận: D00 (nứt dọc): {d['D00']} · D10 (nứt ngang): {d['D10']} · D20 (nứt mạng): {d['D20']} · D40 (ổ gà): {d['D40']}."), s['body']))

    story.append(P('2. Danh sách điểm nóng ưu tiên &amp; dự toán sơ bộ', s['h2']))
    if summary['top_rows']:
        rows_tbl = [
            [str(r['Hạng']), r['Vị trí / Tuyến đường'], r['Mức độ'], str(r['Số phản ánh']), str(r['Điểm ưu tiên']), r['Dự toán (VNĐ)']]
            for r in summary['top_rows'][:15]
        ]
        story.append(_pdf_data_table(
            ctx,
            ['Hạng', 'Vị trí / Tuyến đường', 'Mức độ', 'SL', 'Điểm', 'Dự toán sơ bộ'],
            rows_tbl,
            [1.2, 6.2, 3.0, 1.2, 1.8, 4.0],
        ))
    else:
        story.append(P('• Không có điểm nóng đang hoạt động trong thời điểm tổng hợp.', s['body']))

    story += _pdf_extra_block(ctx, '3. Nhận định & Tóm tắt điều hành (cần người duyệt)', exec_note)
    story += [ctx['Spacer'](1, 8), P(esc(DISCLAIMER.replace('**', '')), s['small'])]
    story += _pdf_signature(
        ctx,
        'Người tổng hợp báo cáo', m.get('prepared_by', ''),
        'Lãnh đạo phê duyệt', m.get('approver', ''),
    )
    doc.build(story)
    return buf.getvalue()


def build_periodic_docx(summary: dict, exec_note: str = '', meta: dict | None = None) -> bytes:
    m = meta or {}
    doc = AdminDocxBuilder()
    doc.add_admin_header(
        parent_org=m.get('parent_org') or 'SỞ XÂY DỰNG / BAN QUẢN LÝ HẠ TẦNG ĐÔ THỊ',
        unit_name=m.get('unit') or 'ĐỘI QUẢN LÝ & DUY TU ĐƯỜNG BỘ',
        doc_no=m.get('doc_no') or 'Số: .../RW-BCTH',
        city=m.get('city') or 'Đà Nẵng',
    )
    doc.add_title(
        'BÁO CÁO TỔNG HỢP CÔNG TÁC GIÁM SÁT & DUY TU MẶT ĐƯỜNG',
        f"Kỳ báo cáo: từ ngày {summary['start_date']} đến ngày {summary['end_date']}",
    )
    doc.add_heading('1. Tổng hợp chỉ tiêu vận hành trong kỳ')
    d = summary['defects']
    doc.add_kv_table([
        ('Tổng phản ánh tiếp nhận', f"{summary['total_reports']} hồ sơ"),
        ('Trạng thái xử lý', f"Chờ duyệt: {summary['pending']} · Đã xác minh: {summary['verified']} · Đang giao: {summary['assigned']} · Đã sửa: {summary['fixed']} · Từ chối: {summary['rejected']} · Gộp: {summary['merged']}"),
        ('Tỷ lệ hoàn thành / Quá hạn SLA', f"{summary['completion_pct']}% · Quá hạn SLA: {summary['overdue_count']} hồ sơ"),
        ('Cơ cấu khuyết tật AI', f"D00 (nứt dọc): {d['D00']} · D10 (nứt ngang): {d['D10']} · D20 (nứt mạng): {d['D20']} · D40 (ổ gà): {d['D40']}"),
        ('Điểm nóng đang mở & Dự toán', f"{summary['active_hotspots']} điểm · ~{summary['total_area_m2']} m² · Tổng dự toán sơ bộ: {summary['formatted_total_cost']}"),
    ])

    doc.add_heading('2. Danh sách điểm nóng ưu tiên & dự toán sơ bộ')
    if summary['top_rows']:
        rows_tbl = [
            [str(r['Hạng']), r['Vị trí / Tuyến đường'], r['Mức độ'], str(r['Số phản ánh']), str(r['Điểm ưu tiên']), r['Dự toán (VNĐ)']]
            for r in summary['top_rows'][:15]
        ]
        doc.add_table(
            ['Hạng', 'Vị trí / Tuyến đường', 'Mức độ', 'SL', 'Điểm', 'Dự toán sơ bộ'],
            rows_tbl,
            col_widths=[700, 3200, 1500, 650, 950, 2360],
        )
    else:
        doc.add_paragraph('Không có điểm nóng đang hoạt động trong thời điểm tổng hợp.')

    if exec_note and str(exec_note).strip():
        doc.add_heading('3. Nhận định & Tóm tắt điều hành (cần người duyệt)')
        for line in str(exec_note).splitlines():
            s = line.strip().replace('**', '')
            if not s:
                continue
            if s[:2] in ('- ', '* '):
                doc.add_bullets([s[2:]])
            else:
                doc.add_paragraph(s, bold=True)

    doc.add_paragraph(DISCLAIMER.replace('**', ''), italic=True, size_pt=9.5)
    doc.add_signature_block(
        left_title='Người tổng hợp báo cáo',
        left_name=m.get('prepared_by', ''),
        right_title='Lãnh đạo phê duyệt',
        right_name=m.get('approver', ''),
    )
    return doc.to_bytes()


# ── 3. BIÊN BẢN NGHIỆM THU SAU SỬA CHỮA (TRƯỚC / SAU) ─────────────────────

def acceptance_record(fixed_row) -> dict:
    r = fixed_row.to_dict() if hasattr(fixed_row, 'to_dict') else dict(fixed_row)
    before_boxes = int(float(r.get('total_boxes') or 0))
    after_boxes = int(float(r.get('after_boxes') or 0))
    reduction_pct = round(100.0 * max(0, before_boxes - after_boxes) / before_boxes, 1) if before_boxes > 0 else (100.0 if after_boxes == 0 else 0.0)
    return {
        'id': str(r.get('id') or ''),
        'location_name': str(r.get('location_name') or ''),
        'latitude': r.get('latitude'),
        'longitude': r.get('longitude'),
        'created_at': str(r.get('created_at') or ''),
        'fixed_at': str(r.get('fixed_at') or ''),
        'assigned_to': str(r.get('assigned_to') or ''),
        'reviewed_by': str(r.get('reviewed_by') or ''),
        'road_type': str(r.get('road_type') or ''),
        'final_level': str(r.get('final_level') or ''),
        'damage_area_m2': round(_num(r.get('damage_area_m2')), 2),
        'before_boxes': before_boxes,
        'after_boxes': after_boxes,
        'reduction_pct': reduction_pct,
        'annotated_file': r.get('annotated_file'),
        'after_image_file': r.get('after_image_file'),
        'note': str(r.get('note') or ''),
    }


def generate_acceptance_note(acc: dict, gemini_key: str = '') -> tuple[str, str]:
    ctx_txt = (
        f"Mã hồ sơ: {acc['id']}\n"
        f"Vị trí: {acc['location_name']} ({acc['road_type']})\n"
        f"Mức độ trước sửa: {acc['final_level']} · Diện tích ước tính: {acc['damage_area_m2']} m²\n"
        f"Đội thi công: {acc['assigned_to'] or '(chưa ghi)'}\n"
        f"Thời điểm ghi nhận: {acc['created_at']} -> Nghiệm thu: {acc['fixed_at']}\n"
        f"Đối chiếu AI: trước sửa {acc['before_boxes']} vùng hư hại -> sau sửa còn {acc['after_boxes']} vùng (giảm {acc['reduction_pct']}%)."
    )
    note, method = _run_gemini(GEMINI_ACCEPTANCE_TASK + '\n\nHỒ SƠ NGHIỆM THU:\n' + ctx_txt, gemini_key)
    if note:
        return note, method
    status_line = (
        'Ảnh sau sửa chữa không còn vùng hư hỏng vượt ngưỡng AI; đề nghị cán bộ xác nhận thực địa để đóng hồ sơ.'
        if acc['after_boxes'] == 0
        else f"Ảnh sau sửa chữa vẫn còn {acc['after_boxes']} vùng AI đánh dấu; cán bộ cần kiểm tra trực tiếp trước khi ký nghiệm thu."
    )
    fallback = (
        'Nhận xét kết quả đối chiếu trước/sau:\n'
        f"- Số vùng hư hỏng ghi nhận giảm từ {acc['before_boxes']} xuống {acc['after_boxes']} vùng (giảm {acc['reduction_pct']}%).\n"
        f"- {status_line}\n"
        'Lưu ý nghiệm thu tại hiện trường:\n'
        '- Kiểm tra độ bằng phẳng bề mặt vá, độ bám dính mép tiếp giáp và vệ sinh hiện trường sau thi công (kết quả tự động chỉ mang tính hỗ trợ).'
    )
    return fallback, method


def build_acceptance_pdf(acc: dict, before_img=None, after_img=None, extra_text: str = '', meta: dict | None = None) -> bytes:
    ctx = _pdf_ctx()
    P, T, TS, s, cm, esc = ctx['Paragraph'], ctx['Table'], ctx['TableStyle'], ctx['styles'], ctx['cm'], ctx['escape']
    m = meta or {}
    buf = io.BytesIO()
    doc = ctx['SimpleDocTemplate'](buf, pagesize=ctx['A4'], leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
    story = _pdf_admin_header(ctx, m)
    story.append(P('BIÊN BẢN NGHIỆM THU KHẮC PHỤC HƯ HỎNG MẶT ĐƯỜNG', s['h1']))
    story.append(P(esc(f"Mã hồ sơ: {acc['id']}"), s['center']))
    story.append(ctx['Spacer'](1, 6))

    story.append(P('1. Thông tin công trình &amp; đối chiếu kết quả', s['h2']))
    info_rows = [
        ['Vị trí / Tuyến đường', acc['location_name']],
        ['Tọa độ GPS / Cấp đường', f"{acc['latitude']}, {acc['longitude']} · {acc['road_type']}"],
        ['Đơn vị thi công / duy tu', m.get('contractor') or acc['assigned_to'] or '(Chưa ghi)'],
        ['Thời điểm ghi nhận / Hoàn thành', f"{acc['created_at']}  ->  {acc['fixed_at'] or '(Chưa ghi)'}"],
        ['Đối chiếu AI Trước / Sau', f"Trước: {acc['before_boxes']} vùng ({acc['final_level']})  |  Sau: {acc['after_boxes']} vùng (giảm {acc['reduction_pct']}%)"],
        ['Kết luận nghiệm thu', m.get('conclusion') or 'Đạt yêu cầu kỹ thuật, đồng ý đóng hồ sơ'],
    ]
    story.append(_pdf_data_table(ctx, ['Hạng mục', 'Nội dung đối chiếu'], info_rows, [5.5, 11.9]))

    story.append(P('2. Hình ảnh hiện trường Trước và Sau sửa chữa', s['h2']))
    img_b = _pdf_fit_image(ctx, before_img, 7.8, 6.8)
    img_a = _pdf_fit_image(ctx, after_img, 7.8, 6.8)
    left_cell = [img_b, P(esc(f"TRƯỚC SỬA ({acc['before_boxes']} vùng AI)"), s['center'])] if img_b else [P('TRƯỚC SỬA: (chưa có ảnh)', s['center'])]
    right_cell = [img_a, P(esc(f"SAU SỬA ({acc['after_boxes']} vùng AI)"), s['center'])] if img_a else [P('SAU SỬA: (chưa có ảnh)', s['center'])]
    pair_tbl = T([[left_cell, right_cell]], colWidths=[8.7 * cm, 8.7 * cm])
    pair_tbl.setStyle(TS([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    story.append(pair_tbl)

    story += _pdf_extra_block(ctx, '3. Nhận xét & Ghi chú nghiệm thu', extra_text)
    story += [ctx['Spacer'](1, 8), P(esc(DISCLAIMER.replace('**', '')), s['small'])]
    story += _pdf_signature(
        ctx,
        'Đại diện đơn vị thi công', m.get('contractor_rep') or acc['assigned_to'],
        'Cán bộ nghiệm thu', m.get('inspector') or m.get('prepared_by', ''),
    )
    doc.build(story)
    return buf.getvalue()


def build_acceptance_docx(acc: dict, before_img=None, after_img=None, extra_text: str = '', meta: dict | None = None) -> bytes:
    m = meta or {}
    doc = AdminDocxBuilder()
    doc.add_admin_header(
        parent_org=m.get('parent_org') or 'SỞ XÂY DỰNG / BAN QUẢN LÝ HẠ TẦNG ĐÔ THỊ',
        unit_name=m.get('unit') or 'ĐỘI QUẢN LÝ & DUY TU ĐƯỜNG BỘ',
        doc_no=m.get('doc_no') or 'Số: .../RW-BBNT',
        city=m.get('city') or 'Đà Nẵng',
    )
    doc.add_title('BIÊN BẢN NGHIỆM THU KHẮC PHỤC HƯ HỎNG MẶT ĐƯỜNG', f"Mã hồ sơ: {acc['id']}")
    doc.add_heading('1. Thông tin công trình & đối chiếu kết quả')
    doc.add_kv_table([
        ('Vị trí / Tuyến đường', acc['location_name']),
        ('Tọa độ GPS / Cấp đường', f"{acc['latitude']}, {acc['longitude']} · {acc['road_type']}"),
        ('Đơn vị thi công / duy tu', m.get('contractor') or acc['assigned_to'] or '(Chưa ghi)'),
        ('Thời điểm ghi nhận / Hoàn thành', f"{acc['created_at']}  →  {acc['fixed_at'] or '(Chưa ghi)'}"),
        ('Đối chiếu AI Trước / Sau', f"Trước: {acc['before_boxes']} vùng ({acc['final_level']}) | Sau: {acc['after_boxes']} vùng (giảm {acc['reduction_pct']}%)"),
        ('Kết luận nghiệm thu', m.get('conclusion') or 'Đạt yêu cầu kỹ thuật, đồng ý đóng hồ sơ'),
    ])
    doc.add_heading('2. Hình ảnh hiện trường Trước và Sau sửa chữa')
    doc.add_image_pair(
        before_img, f"TRƯỚC SỬA ({acc['before_boxes']} vùng AI)",
        after_img, f"SAU SỬA ({acc['after_boxes']} vùng AI)",
    )
    if extra_text and str(extra_text).strip():
        doc.add_heading('3. Nhận xét & Ghi chú nghiệm thu')
        for line in str(extra_text).splitlines():
            s = line.strip().replace('**', '')
            if not s:
                continue
            if s[:2] in ('- ', '* '):
                doc.add_bullets([s[2:]])
            else:
                doc.add_paragraph(s, bold=True)
    doc.add_paragraph(DISCLAIMER.replace('**', ''), italic=True, size_pt=9.5)
    doc.add_signature_block(
        left_title='Đại diện đơn vị thi công',
        left_name=m.get('contractor_rep') or acc['assigned_to'],
        right_title='Cán bộ nghiệm thu',
        right_name=m.get('inspector') or m.get('prepared_by', ''),
    )
    return doc.to_bytes()

"""Báo cáo: mẫu cố định (nguồn sự thật) + đoạn diễn giải Gemini tùy chọn + PDF/Markdown."""
import io
from pathlib import Path

from .config import PROJECT_ROOT, cfg
from .constants import DISCLAIMER


def hotspot_record(hs_row, reports_df):
    """Gộp điểm nóng + bản ghi nặng nhất thành dict dùng cho báo cáo."""
    worst = reports_df[reports_df.id == hs_row['worst_report_id']].iloc[0].to_dict()
    members = reports_df[reports_df.id.isin(hs_row['member_ids'])]
    rec = {**worst, **{k: hs_row[k] for k in (
        'hotspot_id', 'report_count', 'priority_score', 'priority_rank', 'ranking_reason', 'trend_bonus',
        'weather_bonus', 'first_seen', 'last_seen')}}
    rec['location_name'] = hs_row['location_name']
    rec['latitude'], rec['longitude'] = hs_row['latitude'], hs_row['longitude']
    rec['notes'] = [n for n in members.note.fillna('').tolist() if n.strip()]
    rec['member_ids'] = list(hs_row['member_ids'])
    return rec


def report_sections(r):
    n = lambda k: int(float(r.get(k, 0) or 0))
    return [
        ('Thông tin điểm', [
            f"Mã bản ghi nặng nhất: {r['id']}", f"Thời điểm ghi nhận: {r['created_at']}",
            f"Vị trí: {r['location_name']}", f"Tọa độ: {r['latitude']}, {r['longitude']} (nguồn: {r['gps_source']})",
            f"Số báo cáo đã xác minh tại điểm: {n('report_count')} ({r.get('first_seen')} → {r.get('last_seen')})"]),
        ('1. Quan sát từ mô hình nhận diện', [
            f"D00 (nứt dọc): {n('count_D00')} vùng; D10 (nứt ngang): {n('count_D10')} vùng.",
            f"D20 (nứt mạng): {n('count_D20')} vùng; D40 (ổ gà): {n('count_D40')} vùng.",
            f"Độ tin cậy trung bình các vùng phát hiện: {r['avg_confidence']}.",
            f"Diện tích hợp của các khung trên ảnh (proxy): {r['bbox_union_pct']}%."]),
        ('2. Đánh giá sơ bộ và xếp hạng', [
            f"Gợi ý sơ bộ từ quy tắc: {r['ai_level']}. Mức do cán bộ xác nhận: {r['final_level']}.",
            f"Điểm mức độ: {r['final_score']}/100. Cấp đường: {r['road_type']} (điểm {r['road_score']}).",
            f"Điểm ưu tiên: {r['priority_score']}/100; thứ hạng: {n('priority_rank')}.",
            f"Cách tính: {r['ranking_reason']}."]),
        ('3. Hành động đề xuất', [
            'Đề nghị cán bộ kỹ thuật kiểm tra hiện trường trước khi kết luận và chọn phương án xử lý.',
            'Không dựa riêng vào ảnh 2D để đo độ sâu ổ gà, diện tích thực, rủi ro tai nạn hay chi phí.']),
        ('Ghi chú', r.get('notes') or ['(không có)']),
    ]


def template_markdown(r):
    parts = ['# ROADWATCH AI — PHIẾU ĐỀ XUẤT KIỂM TRA HIỆN TRƯỜNG\n']
    for title, lines in report_sections(r):
        parts.append(f'## {title}\n' + '\n'.join(f'- {x}' for x in lines) + '\n')
    parts.append(f'**Trạng thái:** {DISCLAIMER}\n')
    return '\n'.join(parts)


def generate_report(r, gemini_key=''):
    fixed = template_markdown(r)
    if not gemini_key:
        return fixed, 'Mẫu cố định (không có Gemini API)'
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        prompt = ('Viết 2-3 câu tiếng Việt về bước kiểm tra hiện trường cần thực hiện theo hồ sơ này. '
                  'Không nhắc số liệu, không tự suy diễn kích thước, nguyên nhân, chi phí. '
                  'Nêu rõ chỉ là khuyến nghị hỗ trợ, không phải kết luận kỹ thuật.\n' + fixed)
        res = client.models.generate_content(model=cfg('ROADWATCH_GEMINI_MODEL', 'gemini-2.5-flash'), contents=prompt)
        note = getattr(res, 'text', None)
        if not note:
            return fixed, 'Mẫu cố định (Gemini trả về trống)'
        return fixed + '\n## 4. Gợi ý diễn giải từ Gemini (cần người duyệt)\n' + note, 'Gemini + mẫu số liệu cố định'
    except Exception as exc:
        return fixed, 'Mẫu cố định (Gemini chưa hoạt động: ' + type(exc).__name__ + ')'


def build_pdf(r, image_path=None, extra_text=''):
    """PDF tiếng Việt: tìm font có sẵn trong hệ điều hành; không đóng gói font với ứng dụng."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image as RLImage, Paragraph, SimpleDocTemplate, Spacer
    from xml.sax.saxutils import escape

    # DejaVu được cài như font hệ thống bởi packages.txt (fonts-dejavu-core).
    # Không nhúng tệp font vào repository; phát hiện từ Linux/Windows khi chạy.
    import os
    font_pairs = [
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('/usr/share/fonts/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'),
        ('C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf'),
    ]
    pair = next(((a,b) for a,b in font_pairs if os.path.isfile(a) and os.path.isfile(b)), None)
    if pair is None:
        raise RuntimeError('Không tìm thấy font hệ thống hỗ trợ tiếng Việt. Cài fonts-dejavu-core trên máy chủ.')
    if 'DejaVu' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('DejaVu', pair[0]))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', pair[1]))
    body = ParagraphStyle('b', fontName='DejaVu', fontSize=10, leading=14)
    h1 = ParagraphStyle('h1', fontName='DejaVu-Bold', fontSize=15, leading=19, spaceAfter=8)
    h2 = ParagraphStyle('h2', fontName='DejaVu-Bold', fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=3)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm)
    story = [Paragraph('ROADWATCH AI — PHIẾU ĐỀ XUẤT KIỂM TRA HIỆN TRƯỜNG', h1)]
    for title, lines in report_sections(r):
        story.append(Paragraph(escape(title), h2))
        for line in lines:
            story.append(Paragraph('• ' + escape(str(line)), body))
        if title.startswith('1.') and image_path and Path(image_path).is_file():
            from PIL import Image as PILImage
            w, h = PILImage.open(image_path).size
            width = min(14 * cm, 17 * cm)
            story += [Spacer(1, 6), RLImage(str(image_path), width=width, height=width * h / w)]
    if extra_text:
        story += [Paragraph('Gợi ý diễn giải (cần người duyệt)', h2), Paragraph(escape(extra_text), body)]
    story += [Spacer(1, 10), Paragraph(escape(DISCLAIMER.replace('**', '')), body)]
    doc.build(story)
    return buf.getvalue()

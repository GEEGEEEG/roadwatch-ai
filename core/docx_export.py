"""Pure-Python OOXML (.docx) generator for Vietnamese administrative reports.

Zero external dependencies (uses stdlib zipfile + Pillow for image dimensions).
Supports:
- Vietnamese administrative header (Quoc hieu / Tieu ngu, unit, doc number, date)
- Headings, bullet lists, paragraphs, bordered tables
- Single images and side-by-side Before/After photo comparisons
- Two-column signature block
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

from .config import now_vn

FONT_NAME = 'Times New Roman'
PAGE_CONTENT_TWIPS = 9360  # A4 (11906) - left 1440 - right 1106 (~2.5cm / 2.0cm)


def _xml_text(text: str) -> str:
    return escape(str(text or ''))


def _run(text: str, *, bold: bool = False, italic: bool = False, size_pt: float = 12.0, color: str = '111827') -> str:
    sz = int(round(size_pt * 2))
    rpr = [
        f'<w:rFonts w:ascii="{FONT_NAME}" w:hAnsi="{FONT_NAME}" w:cs="{FONT_NAME}"/>',
        f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>',
        f'<w:color w:val="{color}"/>',
    ]
    if bold:
        rpr.append('<w:b/><w:bCs/>')
    if italic:
        rpr.append('<w:i/><w:iCs/>')
    return f'<w:r><w:rPr>{"".join(rpr)}</w:rPr><w:t xml:space="preserve">{_xml_text(text)}</w:t></w:r>'


def _para(
    runs_xml: str,
    *,
    align: str = 'left',
    before: int = 0,
    after: int = 80,
    line: int = 276,
    indent_left: int = 0,
) -> str:
    ppr = [
        f'<w:jc w:val="{align}"/>',
        f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>',
    ]
    if indent_left:
        ppr.append(f'<w:ind w:left="{indent_left}"/>')
    return f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>{runs_xml}</w:p>'


class AdminDocxBuilder:
    """Lightweight Vietnamese administrative .docx builder."""

    def __init__(self):
        self.blocks: list[str] = []
        self._media: list[tuple[str, str, bytes]] = []  # (rid, filename, bytes)
        self._img_seq = 0

    def add_admin_header(
        self,
        *,
        parent_org: str = 'SỞ XÂY DỰNG / BAN QUẢN LÝ HẠ TẦNG ĐÔ THỊ',
        unit_name: str = 'ĐỘI QUẢN LÝ & DUY TU ĐƯỜNG BỘ',
        doc_no: str = 'Số: .../RW-BC',
        city: str = 'Đà Nẵng',
        date_str: str | None = None,
    ) -> None:
        if not date_str:
            now = now_vn()
            date_str = f'{city}, ngày {now.day:02d} tháng {now.month:02d} năm {now.year}'
        w_left = 4300
        w_right = PAGE_CONTENT_TWIPS - w_left
        no_borders = (
            '<w:tblBorders>'
            '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/>'
            '<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
            '</w:tblBorders>'
        )
        left_cell = (
            f'<w:tc><w:tcPr><w:tcW w:w="{w_left}" w:type="dxa"/></w:tcPr>'
            + _para(_run(parent_org.upper(), size_pt=10.5), align='center', after=20, line=240)
            + _para(_run(unit_name.upper(), bold=True, size_pt=10.5), align='center', after=40, line=240)
            + _para(_run(doc_no, size_pt=11), align='center', after=0, line=240)
            + '</w:tc>'
        )
        right_cell = (
            f'<w:tc><w:tcPr><w:tcW w:w="{w_right}" w:type="dxa"/></w:tcPr>'
            + _para(_run('CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', bold=True, size_pt=10.5), align='center', after=20, line=240)
            + _para(_run('Độc lập - Tự do - Hạnh phúc', bold=True, size_pt=11.5), align='center', after=20, line=240)
            + _para(_run('──────────────', size_pt=10, color='334155'), align='center', after=40, line=200)
            + _para(_run(date_str, italic=True, size_pt=11), align='center', after=0, line=240)
            + '</w:tc>'
        )
        tbl = (
            f'<w:tbl><w:tblPr><w:tblW w:w="{PAGE_CONTENT_TWIPS}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>{no_borders}</w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{w_left}"/><w:gridCol w:w="{w_right}"/></w:tblGrid>'
            f'<w:tr>{left_cell}{right_cell}</w:tr></w:tbl>'
        )
        self.blocks.append(tbl)

    def add_title(self, title: str, subtitle: str = '') -> None:
        self.blocks.append(_para(_run(title.upper(), bold=True, size_pt=14.5, color='0F172A'), align='center', before=220, after=60))
        if subtitle:
            self.blocks.append(_para(_run(subtitle, italic=True, size_pt=11.5, color='334155'), align='center', before=0, after=160))

    def add_heading(self, text: str) -> None:
        self.blocks.append(_para(_run(text, bold=True, size_pt=12.5, color='0F172A'), before=160, after=60))

    def add_paragraph(self, text: str, *, bold: bool = False, italic: bool = False, size_pt: float = 11.5) -> None:
        self.blocks.append(_para(_run(text, bold=bold, italic=italic, size_pt=size_pt), after=80))

    def add_bullets(self, items: list[str], *, size_pt: float = 11.5) -> None:
        for item in items:
            s = str(item or '').strip()
            if not s:
                continue
            self.blocks.append(_para(_run(f'•  {s}', size_pt=size_pt), after=50, indent_left=260))

    def add_kv_table(self, pairs: list[tuple[str, str]]) -> None:
        if not pairs:
            return
        w_k = 3000
        w_v = PAGE_CONTENT_TWIPS - w_k
        borders = (
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:left w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:bottom w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:right w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:insideH w:val="single" w:sz="4" w:color="E2E8F0"/>'
            '<w:insideV w:val="single" w:sz="4" w:color="E2E8F0"/>'
            '</w:tblBorders>'
        )
        rows_xml = []
        for k, v in pairs:
            c1 = (
                f'<w:tc><w:tcPr><w:tcW w:w="{w_k}" w:type="dxa"/>'
                '<w:shd w:val="clear" w:fill="F1F5F9"/>'
                '<w:tcMar><w:top w:w="70" w:type="dxa"/><w:bottom w:w="70" w:type="dxa"/>'
                '<w:left w:w="110" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tcMar></w:tcPr>'
                + _para(_run(k, bold=True, size_pt=10.5), after=0, line=240)
                + '</w:tc>'
            )
            c2 = (
                f'<w:tc><w:tcPr><w:tcW w:w="{w_v}" w:type="dxa"/>'
                '<w:tcMar><w:top w:w="70" w:type="dxa"/><w:bottom w:w="70" w:type="dxa"/>'
                '<w:left w:w="110" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tcMar></w:tcPr>'
                + _para(_run(v, size_pt=10.5), after=0, line=240)
                + '</w:tc>'
            )
            rows_xml.append(f'<w:tr>{c1}{c2}</w:tr>')
        self.blocks.append(
            f'<w:tbl><w:tblPr><w:tblW w:w="{PAGE_CONTENT_TWIPS}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>{borders}</w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{w_k}"/><w:gridCol w:w="{w_v}"/></w:tblGrid>'
            f'{"".join(rows_xml)}</w:tbl>'
        )

    def add_table(self, headers: list[str], rows: list[list[str]], col_widths: list[int] | None = None) -> None:
        if not headers:
            return
        n = len(headers)
        if col_widths and len(col_widths) == n:
            widths = col_widths
        else:
            each = PAGE_CONTENT_TWIPS // n
            widths = [each] * (n - 1) + [PAGE_CONTENT_TWIPS - each * (n - 1)]
        borders = (
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="6" w:color="94A3B8"/>'
            '<w:left w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:bottom w:val="single" w:sz="6" w:color="94A3B8"/>'
            '<w:right w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:insideH w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '<w:insideV w:val="single" w:sz="4" w:color="CBD5E1"/>'
            '</w:tblBorders>'
        )
        grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        tr_list = []
        # Header row
        hcells = []
        for idx, htxt in enumerate(headers):
            hcells.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{widths[idx]}" w:type="dxa"/>'
                '<w:shd w:val="clear" w:fill="1E3A5F"/>'
                '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/>'
                '<w:left w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tcMar></w:tcPr>'
                + _para(_run(htxt, bold=True, size_pt=10, color='FFFFFF'), align='center', after=0, line=230)
                + '</w:tc>'
            )
        tr_list.append(f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{"".join(hcells)}</w:tr>')
        for r_i, row in enumerate(rows):
            fill = 'F8FAFC' if r_i % 2 == 1 else 'FFFFFF'
            cells = []
            for idx in range(n):
                val = str(row[idx]) if idx < len(row) else ''
                cells.append(
                    f'<w:tc><w:tcPr><w:tcW w:w="{widths[idx]}" w:type="dxa"/>'
                    f'<w:shd w:val="clear" w:fill="{fill}"/>'
                    '<w:tcMar><w:top w:w="65" w:type="dxa"/><w:bottom w:w="65" w:type="dxa"/>'
                    '<w:left w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tcMar></w:tcPr>'
                    + _para(_run(val, size_pt=10), after=0, line=230)
                    + '</w:tc>'
                )
            tr_list.append(f'<w:tr>{"".join(cells)}</w:tr>')
        self.blocks.append(
            f'<w:tbl><w:tblPr><w:tblW w:w="{PAGE_CONTENT_TWIPS}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>{borders}</w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>{"".join(tr_list)}</w:tbl>'
        )

    def _register_image(self, image_path: str | Path, max_w_cm: float) -> tuple[str, int, int] | None:
        p = Path(image_path)
        if not p.is_file():
            return None
        try:
            with Image.open(p) as im:
                rgb = im.convert('RGB')
                w, h = rgb.size
                if max(w, h) > 1280:
                    scale = 1280.0 / max(w, h)
                    rgb = rgb.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.BILINEAR)
                    w, h = rgb.size
                buf = io.BytesIO()
                rgb.save(buf, format='JPEG', quality=85)
                raw = buf.getvalue()
        except Exception:
            return None
        self._img_seq += 1
        rid = f'rIdImg{self._img_seq}'
        fname = f'image{self._img_seq}.jpg'
        self._media.append((rid, fname, raw))
        cx = int(max_w_cm * 360000)
        cy = int(cx * h / max(1, w))
        max_cy = int(10.5 * 360000)
        if cy > max_cy:
            cx = int(cx * max_cy / cy)
            cy = max_cy
        return rid, cx, cy

    def _inline_drawing(self, rid: str, cx: int, cy: int, name: str) -> str:
        doc_id = self._img_seq
        return (
            '<w:r><w:drawing>'
            '<wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{doc_id}" name="{_xml_text(name)}"/>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:nvPicPr>'
            f'<pic:cNvPr id="{doc_id}" name="{_xml_text(name)}"/>'
            '<pic:cNvPicPr/>'
            '</pic:nvPicPr>'
            '<pic:blipFill>'
            f'<a:blip r:embed="{rid}"/>'
            '<a:stretch><a:fillRect/></a:stretch>'
            '</pic:blipFill>'
            '<pic:spPr>'
            f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '</pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
        )

    def add_image(self, image_path: str | Path | None, caption: str = '', max_w_cm: float = 13.5) -> None:
        if not image_path:
            return
        reg = self._register_image(image_path, max_w_cm)
        if not reg:
            return
        rid, cx, cy = reg
        self.blocks.append(_para(self._inline_drawing(rid, cx, cy, caption or 'photo'), align='center', before=100, after=40))
        if caption:
            self.blocks.append(_para(_run(caption, italic=True, size_pt=10, color='475569'), align='center', after=100))

    def add_image_pair(
        self,
        left_path: str | Path | None,
        left_caption: str,
        right_path: str | Path | None,
        right_caption: str,
    ) -> None:
        w_col = PAGE_CONTENT_TWIPS // 2
        no_borders = (
            '<w:tblBorders>'
            '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/>'
            '<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
            '</w:tblBorders>'
        )

        def _cell(path, cap):
            reg = self._register_image(path, 7.6) if path else None
            if reg:
                rid, cx, cy = reg
                body = (
                    _para(self._inline_drawing(rid, cx, cy, cap), align='center', after=40)
                    + _para(_run(cap, italic=True, size_pt=9.5, color='475569'), align='center', after=0)
                )
            else:
                body = _para(_run(f'{cap}: (chưa có ảnh)', italic=True, size_pt=10, color='64748B'), align='center', after=0)
            return f'<w:tc><w:tcPr><w:tcW w:w="{w_col}" w:type="dxa"/></w:tcPr>{body}</w:tc>'

        self.blocks.append(
            f'<w:tbl><w:tblPr><w:tblW w:w="{PAGE_CONTENT_TWIPS}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>{no_borders}</w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{w_col}"/><w:gridCol w:w="{w_col}"/></w:tblGrid>'
            f'<w:tr>{_cell(left_path, left_caption)}{_cell(right_path, right_caption)}</w:tr></w:tbl>'
        )

    def add_signature_block(
        self,
        *,
        left_title: str = 'NGƯỜI LẬP PHIẾU',
        left_name: str = '',
        right_title: str = 'LÃNH ĐẠO PHÊ DUYỆT',
        right_name: str = '',
    ) -> None:
        w_col = PAGE_CONTENT_TWIPS // 2
        no_borders = (
            '<w:tblBorders>'
            '<w:top w:val="none"/><w:left w:val="none"/><w:bottom w:val="none"/>'
            '<w:right w:val="none"/><w:insideH w:val="none"/><w:insideV w:val="none"/>'
            '</w:tblBorders>'
        )

        def _sig_cell(title: str, name: str) -> str:
            return (
                f'<w:tc><w:tcPr><w:tcW w:w="{w_col}" w:type="dxa"/></w:tcPr>'
                + _para(_run(title.upper(), bold=True, size_pt=11), align='center', before=180, after=20, line=240)
                + _para(_run('(Ký, ghi rõ họ tên)', italic=True, size_pt=10, color='475569'), align='center', after=680, line=240)
                + _para(_run(name or '........................................', bold=bool(name), size_pt=11), align='center', after=0, line=240)
                + '</w:tc>'
            )

        self.blocks.append(
            f'<w:tbl><w:tblPr><w:tblW w:w="{PAGE_CONTENT_TWIPS}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>{no_borders}</w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{w_col}"/><w:gridCol w:w="{w_col}"/></w:tblGrid>'
            f'<w:tr>{_sig_cell(left_title, left_name)}{_sig_cell(right_title, right_name)}</w:tr></w:tbl>'
        )

    def to_bytes(self) -> bytes:
        content_types = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="jpg" ContentType="image/jpeg"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>'
        )
        root_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            '</Relationships>'
        )
        img_rels = ''.join(
            f'<Relationship Id="{rid}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="media/{fname}"/>'
            for rid, fname, _ in self._media
        )
        doc_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{img_rels}</Relationships>'
        )
        sect_pr = (
            '<w:sectPr>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1134" w:right="1106" w:bottom="1134" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
            '</w:sectPr>'
        )
        doc_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document '
            'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
            f'<w:body>{"".join(self.blocks)}{sect_pr}</w:body></w:document>'
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', content_types)
            zf.writestr('_rels/.rels', root_rels)
            zf.writestr('word/_rels/document.xml.rels', doc_rels)
            zf.writestr('word/document.xml', doc_xml)
            for _, fname, raw in self._media:
                zf.writestr(f'word/media/{fname}', raw)
        return buf.getvalue()

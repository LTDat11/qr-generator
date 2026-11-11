from __future__ import annotations

import io
import re

import pandas as pd
import qrcode
import streamlit as st
from openpyxl.styles import Font, PatternFill
from PIL import Image, ImageOps
from qrcode.exceptions import DataOverflowError
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

st.set_page_config(page_title="Bộ công cụ", layout="centered")

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
}

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
}

.block-container {
    max-width: 880px;
    padding-top: 3.5rem;
    padding-bottom: 4rem;
}

.app-title {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0 0 0.35rem 0;
    color: #0f172a;
}

.app-subtitle {
    font-size: 1rem;
    color: #64748b;
    margin: 0 0 2rem 0;
    line-height: 1.5;
}

.section-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #0f172a;
    margin: 0 0 0.75rem 0;
}

.preview-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 260px;
    color: #94a3b8;
    font-size: 0.95rem;
    text-align: center;
    padding: 0 1rem;
}

div[data-testid="stTextInput"] input {
    border-radius: 8px;
    padding: 0.7rem 0.9rem;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px;
}

div[data-testid="stDownloadButton"] button {
    width: 100%;
    border-radius: 8px;
    padding: 0.65rem 1rem;
    font-weight: 600;
}

div[data-testid="stImage"] img {
    border-radius: 8px;
    margin: 0 auto;
}

details {
    border-radius: 10px !important;
}
</style>
"""

ERROR_LEVELS = {
    "Thấp (7%)": ERROR_CORRECT_L,
    "Trung bình (15%)": ERROR_CORRECT_M,
    "Khá cao (25%)": ERROR_CORRECT_Q,
    "Cao (30%)": ERROR_CORRECT_H,
}


def luminance(hex_color: str) -> float:
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(color_a: str, color_b: str) -> float:
    lum_a, lum_b = luminance(color_a), luminance(color_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


@st.cache_data(show_spinner=False)
def build_qr_png(
    data: str,
    fill_color: str,
    back_color: str,
    box_size: int,
    error_level: int,
    bg_bytes: bytes | None = None,
    bg_opacity: float = 0.25,
) -> bytes:
    qr = qrcode.QRCode(
        error_correction=error_level,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Mặt nạ các ô đen của mã QR (255 = ô QR, 0 = nền).
    matrix = qr.make_image(fill_color="black", back_color="white").convert("L")
    modules_mask = matrix.point(lambda p: 255 if p < 128 else 0)
    size = matrix.size

    # Lớp nền: màu nền, có thể pha thêm ảnh chìm ở độ mờ đã chọn.
    canvas = Image.new("RGB", size, back_color)
    if bg_bytes:
        watermark = ImageOps.exif_transpose(Image.open(io.BytesIO(bg_bytes)))
        watermark = ImageOps.fit(
            watermark.convert("RGB"), size, Image.Resampling.LANCZOS
        )
        canvas = Image.blend(canvas, watermark, bg_opacity)

    # Vẽ các ô QR lên trên cùng để luôn rõ nét.
    canvas.paste(Image.new("RGB", size, fill_color), mask=modules_mask)

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()


ID_HEADER = "SỐ CMND/CCCD"
NAME_HEADER = "HỌ TÊN HỌC VIÊN"
TEACHER_HEADER = "GIÁO VIÊN HỒ SƠ"


def id_key(value) -> str:
    """Khóa so khớp số CMND/CCCD: chỉ giữ chữ số và bỏ số 0 đứng đầu,
    để vẫn khớp khi Excel làm mất số 0 ở đầu."""
    return re.sub(r"\D", "", str(value)).lstrip("0")


def clean_name(value) -> str:
    return " ".join(str(value).upper().split())


def parse_pasted(text: str) -> tuple[list[tuple[str, str]], int]:
    """Tách văn bản dán từ Excel thành các cặp (CCCD, họ tên).
    Trả về danh sách hợp lệ và số dòng bị bỏ qua (dòng tiêu đề, dòng thiếu dữ liệu)."""
    rows, skipped = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) < 2:
            parts = line.strip().split(None, 1)
        if len(parts) < 2 or not id_key(parts[0]):
            skipped += 1
            continue
        rows.append((re.sub(r"\D", "", parts[0]), clean_name(parts[1])))
    return rows, skipped


@st.cache_data(show_spinner=False)
def list_sheets(file_bytes: bytes) -> list[str]:
    return pd.ExcelFile(io.BytesIO(file_bytes)).sheet_names


@st.cache_data(show_spinner=False)
def read_sheet(file_bytes: bytes, sheet: str) -> pd.DataFrame:
    # dtype=str để giữ nguyên số 0 đứng đầu của CCCD.
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet, dtype=str)


def build_result_xlsx(result: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        result.to_excel(writer, index=False, sheet_name="Ket qua")
        ws = writer.sheets["Ket qua"]

        header_font = Font(name="Arial", bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor="1E293B")
        body_font = Font(name="Arial")
        missing_fill = PatternFill("solid", fgColor="FFF2CC")

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.font = body_font
            row[0].number_format = "@"  # giữ CCCD dạng văn bản
            if not row[2].value:
                row[2].fill = missing_fill

        for col, width in zip("ABC", (18, 34, 28)):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"
    return buffer.getvalue()


def match_teachers(
    master: pd.DataFrame,
    id_col: str,
    name_col: str,
    teacher_col: str,
    rows: list[tuple[str, str]],
) -> tuple[pd.DataFrame, int]:
    """Lọc trùng theo CCCD (giữ dòng đầu tiên) rồi tra giáo viên hồ sơ trong file danh sách.
    Trả về bảng chi tiết (có cột Trạng thái) và số dòng trùng đã loại."""
    unique, seen = [], set()
    for cccd, name in rows:
        key = id_key(cccd)
        if key not in seen:
            seen.add(key)
            unique.append((cccd, name))
    duplicates = len(rows) - len(unique)

    lookup = master[[id_col, name_col, teacher_col]].dropna(subset=[id_col]).copy()
    lookup["_key"] = lookup[id_col].map(id_key)
    lookup = lookup.drop_duplicates("_key").set_index("_key")

    records = []
    for cccd, name in unique:
        key = id_key(cccd)
        if key in lookup.index:
            found = lookup.loc[key]
            teacher = found[teacher_col]
            teacher = "" if pd.isna(teacher) else str(teacher).strip()
            same_name = clean_name(found[name_col]) == name
            status = "Khớp" if same_name else "Khớp CCCD, tên khác file"
            cccd = str(found[id_col]).strip()
        else:
            teacher, status = "", "Không tìm thấy"
        records.append((cccd, name, teacher, status))

    detail = pd.DataFrame(
        records, columns=[ID_HEADER, NAME_HEADER, TEACHER_HEADER, "Trạng thái"]
    )
    return detail, duplicates


def render_lookup_tool() -> None:
    st.caption(
        "Dán danh sách (số CMND/CCCD và họ tên) từ Excel, tải lên file danh sách học viên "
        "để tra cứu giáo viên hồ sơ, loại bỏ dòng trùng và xuất kết quả ra Excel."
    )

    st.markdown('<p class="section-title">1. File danh sách học viên</p>', unsafe_allow_html=True)
    source = st.file_uploader(
        "File Excel danh sách",
        type=["xlsx"],
        label_visibility="collapsed",
        help="File chứa các cột SỐ CMND/CCCD, HỌ TÊN HỌC VIÊN và GIÁO VIÊN HỒ SƠ. "
        "Không đưa file này lên GitHub vì có thông tin cá nhân.",
    )

    st.markdown('<p class="section-title">2. Dữ liệu cần tra cứu</p>', unsafe_allow_html=True)
    pasted = st.text_area(
        "Dữ liệu dán từ Excel",
        placeholder="Dán 2 cột từ Excel: SỐ CMND/CCCD và HỌ TÊN HỌC VIÊN\n"
        "075304020310\tBÙI TÚ AN",
        height=200,
        label_visibility="collapsed",
    )

    if not source:
        st.info("Tải lên file Excel danh sách học viên để bắt đầu.")
        return
    if not pasted.strip():
        st.info("Dán dữ liệu cần tra cứu vào ô phía trên.")
        return

    file_bytes = source.getvalue()
    try:
        sheets = list_sheets(file_bytes)
        with st.expander("Tùy chọn nguồn dữ liệu"):
            sheet = st.selectbox("Trang tính", sheets)
            master = read_sheet(file_bytes, sheet)
            columns = list(master.columns)

            def pick(label: str, expected: str) -> str:
                lowered = [str(c).strip().upper() for c in columns]
                index = lowered.index(expected) if expected in lowered else 0
                return st.selectbox(label, columns, index=index)

            id_col = pick("Cột số CMND/CCCD", ID_HEADER)
            name_col = pick("Cột họ tên học viên", NAME_HEADER)
            teacher_col = pick("Cột giáo viên hồ sơ", TEACHER_HEADER)
    except Exception:
        st.error("Không đọc được file Excel. Hãy kiểm tra lại định dạng .xlsx.")
        return

    rows, skipped = parse_pasted(pasted)
    if not rows:
        st.error("Không nhận diện được dòng dữ liệu nào. Mỗi dòng cần có số CMND/CCCD và họ tên.")
        return

    detail, duplicates = match_teachers(master, id_col, name_col, teacher_col, rows)
    result = detail[[ID_HEADER, NAME_HEADER, TEACHER_HEADER]]

    not_found = int((detail["Trạng thái"] == "Không tìm thấy").sum())
    name_diff = int((detail["Trạng thái"] == "Khớp CCCD, tên khác file").sum())

    st.markdown('<p class="section-title">3. Kết quả</p>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Dòng đã dán", len(rows))
    m2.metric("Dòng trùng đã loại", duplicates)
    m3.metric("Tìm thấy", len(detail) - not_found)
    m4.metric("Không tìm thấy", not_found)

    if skipped:
        st.caption(f"Đã bỏ qua {skipped} dòng không hợp lệ (dòng tiêu đề hoặc thiếu dữ liệu).")
    if not_found:
        st.warning(
            f"{not_found} dòng không có trong file danh sách. "
            "Các dòng này vẫn được xuất với ô giáo viên để trống và tô màu vàng."
        )
    if name_diff:
        st.warning(
            f"{name_diff} dòng khớp số CCCD nhưng họ tên khác với file danh sách. "
            "Hãy đối chiếu lại trước khi sử dụng."
        )

    st.dataframe(detail, width="stretch", hide_index=True)
    st.download_button(
        "Tải về Excel",
        data=build_result_xlsx(result),
        file_name="ket_qua_giao_vien_ho_so.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def render_qr_tool() -> None:
    st.caption("Tạo mã QR từ đường dẫn hoặc đoạn văn bản bất kỳ và tải về dưới dạng ảnh PNG.")

    left, right = st.columns([1.1, 1], gap="large")

    with left:
        st.markdown('<p class="section-title">Nội dung</p>', unsafe_allow_html=True)
        raw_text = st.text_area(
            "Nội dung mã QR",
            placeholder="Nhập đường dẫn (https://example.com) hoặc văn bản bất kỳ",
            height=120,
            label_visibility="collapsed",
        )

        with st.expander("Tùy chỉnh giao diện"):
            color_col, bg_col = st.columns(2)
            fill_color = color_col.color_picker("Màu mã QR", "#0F172A")
            back_color = bg_col.color_picker("Màu nền", "#FFFFFF")
            box_size = st.slider(
                "Độ phân giải ảnh (pixel mỗi ô vuông)",
                5,
                30,
                10,
                help="Quyết định kích thước thật của file PNG tải về. Giá trị càng cao "
                "ảnh càng lớn và nét, phù hợp để in. Khung xem trước luôn được thu "
                "vừa màn hình nên không thay đổi kích thước hiển thị.",
            )
            error_label = st.selectbox(
                "Mức sửa lỗi",
                list(ERROR_LEVELS.keys()),
                index=1,
                help="Mức cao giúp mã QR vẫn quét được khi bị mờ hoặc che một phần, "
                "nhưng mã sẽ dày đặc hơn.",
            )
            bg_file = st.file_uploader(
                "Ảnh chìm phía sau (tùy chọn)",
                type=["png", "jpg", "jpeg", "webp"],
                help="Ảnh được làm mờ và đặt dưới mã QR. Bỏ trống nếu không cần.",
            )
            bg_opacity_pct = 25
            if bg_file:
                bg_opacity_pct = st.slider(
                    "Độ đậm của ảnh chìm (%)",
                    5,
                    50,
                    25,
                    help="Giá trị càng cao ảnh càng rõ nhưng mã QR càng khó quét.",
                )

    content = raw_text.strip()
    png_bytes = None

    bg_bytes = None
    if bg_file:
        try:
            bg_bytes = bg_file.getvalue()
            Image.open(io.BytesIO(bg_bytes)).verify()
        except Exception:
            bg_bytes = None
            left.warning("Không đọc được ảnh chìm. Mã QR vẫn được tạo mà không có ảnh.")

    if content:
        ratio = contrast_ratio(fill_color, back_color)
        if ratio < 3:
            left.warning(
                "Màu mã QR và màu nền quá gần nhau, điện thoại có thể khó quét. "
                "Hãy chọn màu mã QR tối hơn màu nền."
            )
        if bg_bytes and ERROR_LEVELS[error_label] in (ERROR_CORRECT_L, ERROR_CORRECT_M):
            left.info(
                "Khi dùng ảnh chìm, nên chọn mức sửa lỗi Khá cao hoặc Cao để mã dễ quét hơn."
            )
        try:
            png_bytes = build_qr_png(
                content,
                fill_color,
                back_color,
                box_size,
                ERROR_LEVELS[error_label],
                bg_bytes,
                bg_opacity_pct / 100,
            )
        except (DataOverflowError, ValueError):
            left.error(
                "Nội dung quá dài để tạo mã QR. Hãy rút ngắn văn bản "
                "hoặc chọn mức sửa lỗi thấp hơn."
            )

    with right:
        with st.container(border=True):
            st.markdown('<p class="section-title">Xem trước</p>', unsafe_allow_html=True)
            if png_bytes:
                st.image(png_bytes, width="stretch")
                width_px, height_px = Image.open(io.BytesIO(png_bytes)).size
                preview_text = content if len(content) <= 60 else content[:57] + "..."
                preview_text = " ".join(preview_text.split())
                st.caption(
                    f"{preview_text}  |  {len(content)} ký tự  |  "
                    f"Ảnh tải về: {width_px} x {height_px} px"
                )
                st.download_button(
                    "Tải về PNG",
                    data=png_bytes,
                    file_name="qrcode.png",
                    mime="image/png",
                    type="primary",
                )
            else:
                st.markdown(
                    '<div class="preview-empty">Nhập nội dung để xem mã QR tại đây.</div>',
                    unsafe_allow_html=True,
                )


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<p class="app-title">Bộ công cụ</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subtitle">Tạo mã QR và tra cứu, lọc trùng danh sách học viên từ file Excel.</p>',
    unsafe_allow_html=True,
)

tab_qr, tab_lookup = st.tabs(["Tạo mã QR", "Lọc trùng và tra cứu"])
with tab_qr:
    render_qr_tool()
with tab_lookup:
    render_lookup_tool()
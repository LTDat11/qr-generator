from __future__ import annotations

import io
from urllib.parse import urlparse

import qrcode
import streamlit as st
from PIL import Image, ImageOps
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

st.set_page_config(page_title="QR Code Generator", layout="centered")

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


def normalize_url(raw: str) -> str | None:
    """Trả về URL hợp lệ (tự thêm https:// nếu thiếu), hoặc None nếu không hợp lệ."""
    value = raw.strip()
    if not value:
        return None
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or "." not in parsed.netloc:
        return None
    return value


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


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<p class="app-title">QR Code Generator</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subtitle">Tạo mã QR từ đường dẫn website và tải về dưới dạng ảnh PNG.</p>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.1, 1], gap="large")

with left:
    st.markdown('<p class="section-title">Đường dẫn</p>', unsafe_allow_html=True)
    raw_url = st.text_input(
        "URL",
        placeholder="https://example.com",
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

url = normalize_url(raw_url)
png_bytes = None

bg_bytes = None
if bg_file:
    try:
        bg_bytes = bg_file.getvalue()
        Image.open(io.BytesIO(bg_bytes)).verify()
    except Exception:
        bg_bytes = None
        left.warning("Không đọc được ảnh chìm. Mã QR vẫn được tạo mà không có ảnh.")

if raw_url.strip() and url is None:
    left.error("URL không hợp lệ. Hãy nhập địa chỉ dạng https://example.com.")
elif url:
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
    png_bytes = build_qr_png(
        url,
        fill_color,
        back_color,
        box_size,
        ERROR_LEVELS[error_label],
        bg_bytes,
        bg_opacity_pct / 100,
    )

with right:
    with st.container(border=True):
        st.markdown('<p class="section-title">Xem trước</p>', unsafe_allow_html=True)
        if png_bytes:
            st.image(png_bytes, use_container_width=True)
            width_px, height_px = Image.open(io.BytesIO(png_bytes)).size
            st.caption(f"{url}  |  Ảnh tải về: {width_px} x {height_px} px")
            st.download_button(
                "Tải về PNG",
                data=png_bytes,
                file_name="qrcode.png",
                mime="image/png",
                type="primary",
            )
        else:
            st.markdown(
                '<div class="preview-empty">Nhập đường dẫn để xem mã QR tại đây.</div>',
                unsafe_allow_html=True,
            )
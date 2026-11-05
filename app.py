import io

import qrcode
import streamlit as st

st.set_page_config(page_title="QR Code Generator")
st.title("Tạo mã QR từ URL")

url = st.text_input("Nhập URL", placeholder="https://example.com")

col1, col2 = st.columns(2)
fill_color = col1.color_picker("Màu mã QR", "#000000")
back_color = col2.color_picker("Màu nền", "#FFFFFF")
box_size = st.slider("Kích thước ô", 5, 20, 10)

if url:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    st.image(png_bytes, caption="Mã QR của bạn")
    st.download_button(
        "Tải về PNG",
        data=png_bytes,
        file_name="qrcode.png",
        mime="image/png",
    )
else:
    st.info("Nhập một URL để tạo mã QR.")
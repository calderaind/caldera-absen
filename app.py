import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests
from streamlit_geolocation import geolocation

st.set_page_config(page_title="Scanner Absen", layout="centered")
st.title("📷 Scanner Absen dengan GPS")

# 1) Minta permission & ambil lokasi device
location = geolocation(
    label="Klik untuk ijinkan lokasi perangkat",
    key="geo1",
)
if location:
    lat, lon = location["latitude"], location["longitude"]
    st.success(f"📍 Lokasi device: {lat:.6f}, {lon:.6f}")
else:
    st.info("📍 Lokasi belum diizinkan atau tidak tersedia.")

# 2) Scan QR/barcode lewat kamera
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode lalu foto")

if img_buffer:
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, pts, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")

        # 3) Panggil API absen dengan lat & long
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params = {}
        if location:
            params = {"lat": lat, "long": lon}

        try:
            resp = requests.get(api_url, params=params, timeout=5)
            resp.raise_for_status()
            st.json(resp.json())
        except Exception as e:
            st.error(f"Gagal: {e}")
    else:
        st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi.")

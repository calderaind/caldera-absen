import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests
from streamlit_geolocation import geolocation

# --- Setup halaman ---
st.set_page_config(page_title="Scanner Absen", layout="centered")
st.title("📷 Scanner Absen dengan GPS")

# --- Minta permission & ambil lokasi ---
# ukurannya kecil karena hanya butuh permission pop-up
location = geolocation(
    label="Klik untuk izinkan lokasi perangkat",
    key="geo1",
)
if location:
    lat, lng = location["latitude"], location["longitude"]
    st.success(f"📍 Lokasi device: {lat:.6f}, {lng:.6f}")
else:
    st.info("📍 Lokasi belum diizinkan atau tidak tersedia.")

# --- Ambil foto barcode/QR ---
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode dan ambil foto")

if img_buffer:
    # Preview
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # Decode via OpenCV
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, points, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")

        # Panggil API absen dengan lat & long
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params = {}
        if location:
            params = {"lat": lat, "long": lng}

        try:
            resp = requests.get(api_url, params=params, timeout=5)
            resp.raise_for_status()
            result = resp.json()
            st.markdown("**✅ Response server:**")
            st.json(result)
        except Exception as e:
            st.error(f"❌ Gagal koneksi/API:\n{e}")
    else:
        st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi.")

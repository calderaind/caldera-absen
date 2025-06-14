# app.py

import streamlit as st
from streamlit.components.v1 import html
from PIL import Image
import numpy as np
import cv2
import requests

# --- Setup page ---
st.set_page_config(page_title="Scanner QR & Lokasi", layout="centered")
st.title("📷 Scanner QR & Lokasi")

# --- 1) Kamera: selalu tampil ---
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode lalu tekan tombol Capture")
email = None

if img_buffer:
    # tampilkan preview
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # decode via OpenCV
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, _, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")
    else:
        st.warning("❌ QR/barcode tidak terdeteksi.")

# --- 2) Geolocation: baca dari URL ---
qs  = st.query_params
lat = qs.get("lat", [None])[0]
lon = qs.get("lon", [None])[0]

if lat and lon:
    st.success(f"📍 Lokasi device: {lat}, {lon}")
else:
    # tombol untuk request location
    if st.button("📍 Ambil Lokasi"):
        js = """
        <script>
          navigator.geolocation.getCurrentPosition(
            pos => {
              const url = new URL(window.location);
              url.searchParams.set('lat', pos.coords.latitude);
              url.searchParams.set('lon', pos.coords.longitude);
              window.location.href = url.toString();
            },
            err => {
              alert('Gagal mendapatkan lokasi: ' + err.message);
            }
          );
        </script>
        """
        html(js, height=0)
        st.stop()

# --- 3) Jika email + lokasi sudah ada, panggil API absen ---
if email and lat and lon:
    api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
    params  = {"lat": lat, "long": lon}
    try:
        res = requests.get(api_url, params=params, timeout=5)
        res.raise_for_status()
        st.markdown("**✅ Response server:**")
        st.json(res.json())
    except Exception as e:
        st.error(f"❌ Gagal koneksi ke API:\n{e}")

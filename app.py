# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests
from streamlit.components.v1 import html

# --- Setup halaman ---
st.set_page_config(page_title="Scanner QR + Geolocation", layout="centered")
st.title("📷 Scanner QR (Email) dengan Lokasi")

# --- 1) Cek apakah lat/lon sudah ada di URL ---
qs  = st.experimental_get_query_params()
lat = qs.get("lat", [None])[0]
lon = qs.get("lon", [None])[0]

# --- 2) Jika belum, inject JS untuk minta izin Geolocation ---
if lat is None or lon is None:
    st.info("🔒 Meminta izin lokasi… (browser akan mem-prompt)")
    js = """
    <script>
      navigator.geolocation.getCurrentPosition(
        pos => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const url = new URL(window.location);
          url.searchParams.set('lat', lat);
          url.searchParams.set('lon', lon);
          window.location.href = url.toString();
        },
        err => {
          alert('Gagal mendapatkan lokasi: ' + err.message);
        }
      );
    </script>
    """
    # height=0 agar tidak memengaruhi layout
    html(js, height=0)
    st.stop()

# --- 3) Tampilkan koordinat yang sudah terbaca ---
st.success(f"📍 Lokasi device: {lat}, {lon}")

# --- 4) Ambil foto via kamera ---
img_buffer = st.camera_input("Ambil foto QR/barcode")
if not img_buffer:
    st.info("Arahkan kamera ke QR/barcode lalu tekan tombol di atas.")
    st.stop()

# --- 5) Preview & decode QR/barcode ---
img = Image.open(img_buffer)
st.image(img, caption="Preview", use_column_width=True)

# Convert ke OpenCV (BGR)
img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
detector = cv2.QRCodeDetector()
email, _, _ = detector.detectAndDecode(img_cv)

if not email:
    st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi.")
    st.stop()

st.success(f"✉️ Email ter-scan: {email}")

# --- 6) Kirim ke API absen dengan lat & long ---
api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
params  = {"lat": lat, "long": lon}

try:
    resp = requests.get(api_url, params=params, timeout=5)
    resp.raise_for_status()
    st.markdown("**✅ Response server:**")
    st.json(resp.json())
except Exception as e:
    st.error(f"❌ Gagal koneksi/API:\n{e}")

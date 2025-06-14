# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests

# --- Setup halaman ---
st.set_page_config(page_title="Scanner Absen", layout="centered")
st.title("Scanner Absen")

# --- Ambil foto dari kamera ---
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode lalu tekan tombol Capture")
if not img_buffer:
    st.info("📸 Tunggu sampai foto di-capture untuk scan dan ambil lokasi otomatis.")
    st.stop()

# --- Tampilkan preview ---
img = Image.open(img_buffer)
st.image(img, caption="Preview foto", use_column_width=True)

# --- Decode QR/barcode (email) via OpenCV ---
img_cv   = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
detector = cv2.QRCodeDetector()
email, _, _ = detector.detectAndDecode(img_cv)

if not email:
    st.error("❌ QR/barcode tidak terdeteksi. Silakan coba ulangi.")
    st.stop()

st.success(f"✉️ Email ter-scan: {email}")

# --- Ambil koordinat melalui IP geolocation saat itu juga ---
st.info("📍 Mengambil lokasi (berdasarkan IP)…")
try:
    geo_req = requests.get("https://ipapi.co/json/", timeout=5)
    geo_req.raise_for_status()
    geo = geo_req.json()
    lat = geo.get("latitude")
    lon = geo.get("longitude")
    if lat is None or lon is None:
        raise ValueError("Tidak ada field latitude/longitude")
    st.success(f"📍 Lokasi terdeteksi: {lat:.6f}, {lon:.6f}")
except Exception as e:
    st.warning(f"⚠️ Gagal ambil lokasi: {e}")
    lat = lon = None

# --- Panggil API absen jika lokasi tersedia ---
api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
params = {}
if lat is not None and lon is not None:
    params = {"lat": lat, "long": lon}

st.info(f"🔄 Mengirim ke API: {api_url}{('?lat='+str(lat)+'&long='+str(lon)) if params else ''}")
try:
    resp = requests.get(api_url, params=params, timeout=5)
    resp.raise_for_status()
    st.markdown("**✅ Response dari server:**")
    st.json(resp.json())
except Exception as e:
    st.error(f"❌ Gagal koneksi/API:\n{e}")

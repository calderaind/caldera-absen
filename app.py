# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests

st.set_page_config(page_title="Scanner Absen GPS", layout="centered")

# 1) Baca lat/lon dari query params
params = st.experimental_get_query_params()
lat = params.get("lat", [None])[0]
lon = params.get("lon", [None])[0]

# 2) Jika belum ada, tampilkan tombol untuk request lokasi
if lat is None or lon is None:
    st.title("📍 Ambil Lokasi Device")
    st.markdown(
        """
        <button id="getloc" style="
            padding: 0.5rem 1rem;
            font-size:1rem;
            border:none;
            background:#4e73df;
            color:white;
            border-radius:4px;
            cursor:pointer;
        ">
          Izinkan Lokasi
        </button>
        <script>
        const btn = document.getElementById('getloc');
        btn.onclick = () => {
          if (!navigator.geolocation) {
            alert('Browser Anda tidak mendukung Geolocation');
            return;
          }
          navigator.geolocation.getCurrentPosition(pos => {
            const lat  = pos.coords.latitude;
            const lon  = pos.coords.longitude;
            const url  = new URL(window.location);
            url.searchParams.set('lat', lat);
            url.searchParams.set('lon', lon);
            window.history.replaceState({}, '', url);
            window.location.reload();
          }, err => {
            alert('Gagal mengambil lokasi: ' + err.message);
          });
        };
        </script>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# 3) Kalau sudah ada, lanjut ke scanner
st.title("📷 Scanner Absen (GPS)")
st.success(f"Lokasi device: {lat}, {lon}")

# 4) Ambil foto dari kamera
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode dan ambil foto")

if img_buffer:
    # preview
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # decode QR/barcode via OpenCV
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, points, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")

        # 5) Panggil API /absen/{email}?lat=...&long=...
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params = {"lat": lat, "long": lon}
        try:
            res = requests.get(api_url, params=params, timeout=5)
            res.raise_for_status()
            st.markdown("**✅ Response server:**")
            st.json(res.json())
        except Exception as e:
            st.error(f"❌ Gagal koneksi/API:\n{e}")
    else:
        st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi lagi.")

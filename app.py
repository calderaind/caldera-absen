# app.py

import streamlit as st
from streamlit.components.v1 import html
from PIL import Image
import numpy as np
import cv2
import requests

st.set_page_config(page_title="Scanner Absen GPS+Cam", layout="centered")

# 1. Baca lat/lon dari URL
qs = st.experimental_get_query_params()
lat = qs.get("lat", [None])[0]
lon = qs.get("lon", [None])[0]

# 2. Jika belum ada, inject JS untuk request Geolocation + Kamera
if lat is None or lon is None:
    st.title("🔒 Meminta izin lokasi & kamera…")
    js = """
    <script>
    (async () => {
      try {
        // 1) Minta izin lokasi
        const pos = await new Promise((res, rej) =>
          navigator.geolocation.getCurrentPosition(res, rej)
        );
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        // 2) Minta izin kamera
        await navigator.mediaDevices.getUserMedia({ video: true });
        // 3) Sisipkan ke URL & reload
        const url = new URL(window.location);
        url.searchParams.set('lat', lat);
        url.searchParams.set('lon', lon);
        window.history.replaceState({}, '', url);
        window.location.reload();
      } catch (err) {
        console.error(err);
        alert('Gagal dapatkan izin: ' + err.message);
      }
    })();
    </script>
    """
    # render zero‐height HTML (hanya JS)
    html(js, height=0)
    st.stop()

# 3. Jika sudah ada lat/lon, lanjut app
st.title("📷 Scanner Absen (GPS + Kamera)")
st.success(f"Lokasi device: {lat}, {lon}")

# 4. Ambil gambar dari kamera via Streamlit
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode lalu foto")

if img_buffer:
    # 4a. Preview
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # 4b. Decode QR/barcode (OpenCV)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, pts, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")

        # 5. Panggil API absen dengan lat & long
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
        st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi.")

# app.py

import streamlit as st
from streamlit.components.v1 import html
from PIL import Image
import numpy as np
import cv2
import requests

st.set_page_config(page_title="Scanner Absen GPS + Kamera", layout="centered")

# ————————————————————————————————
# 1) Geolocation: simpan di session_state setelah user klik tombol
# ————————————————————————————————
if 'lat' not in st.session_state or 'lon' not in st.session_state:
    st.title("📍 Izinkan Lokasi & Kamera")

    st.write(
        "Klik tombol di bawah untuk meminta izin lokasi (GPS) dan kamera. "
        "Browser akan memunculkan prompt. Setelah diijinkan, halaman akan reload."
    )
    if st.button("🔐 Izinkan Lokasi & Kamera"):
        js = """
        <script>
        (async () => {
          try {
            // 1) Prompt Geolocation
            const pos = await new Promise((res, rej) =>
              navigator.geolocation.getCurrentPosition(res, rej)
            );
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            // 2) Prompt Kamera
            await navigator.mediaDevices.getUserMedia({ video: true });
            // 3) Kirim data kembali ke Streamlit via hash URL
            const url = new URL(window.location);
            // gunakan hash agar st.experimental_get_query_params bisa tetap membaca
            url.searchParams.set('lat', lat);
            url.searchParams.set('lon', lon);
            window.location.href = url.toString();
          } catch (err) {
            alert('Gagal mendapatkan izin: ' + err.message);
          }
        })();
        </script>
        """
        # inject HTML+JS
        html(js, height=0)
    st.stop()

# ————————————————————————————————
# 2) Ambil lat/lon dari query params
# ————————————————————————————————
qs   = st.experimental_get_query_params()
lat  = qs.get("lat", [None])[0]
lon  = qs.get("lon", [None])[0]

# Jika tombol sudah diklik dan URL sudah berisi lat/lon, kita lanjut:
if not lat or not lon:
    st.error("⚠️ Gagal membaca lokasi. Silakan ulangi proses izin lokasi.")
    st.stop()

# ————————————————————————————————
# 3) Tampilkan scanner kamera
# ————————————————————————————————
st.title("📷 Scanner Absen (GPS + Kamera)")
st.success(f"Lokasi device: {lat}, {lon}")

img_buffer = st.camera_input("Arahkan kamera ke QR/barcode dan tekan Capture")

if img_buffer:
    # Preview
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # Decode QR/barcode
    img_cv   = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, _, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")

        # 4) Kirim ke API absen
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params  = {"lat": lat, "long": lon}
        try:
            resp = requests.get(api_url, params=params, timeout=5)
            resp.raise_for_status()
            st.markdown("**✅ Response server:**")
            st.json(resp.json())
        except Exception as e:
            st.error(f"❌ Gagal koneksi ke API:\n{e}")
    else:
        st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi lagi.")

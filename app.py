# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests

# --- Setup halaman Streamlit ---
st.set_page_config(page_title="Scanner Absen", layout="centered")
st.title("Scanner Absen 📷")

# --- Ambil foto dari kamera ---
img_buffer = st.camera_input("Arahkan kamera ke barcode/QR dan ambil foto")

if img_buffer:
    # Tampilkan preview
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # Konversi PIL → OpenCV (BGR)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Inisialisasi detektor QR
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img_cv)

    if data:
        # Jika terdeteksi, tampilkan email
        st.success(f"✉️ Email ter-scan: {data}")
        print(f"[SCAN] {data}")  # juga ke console Python

        # --- Panggil API absen ---
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{data}"
        try:
            res = requests.get(api_url, timeout=5)
            if res.ok:
                result = res.json()
                st.markdown("**Response dari server:**")
                st.json(result)
                print(f"[API] {api_url} → {res.status_code}", result)
            else:
                st.error(f"❌ API Error: {res.status_code}")
                print(f"[API ERROR] {api_url} → {res.status_code}", res.text)
        except Exception as e:
            st.error(f"⚠️ Gagal koneksi ke API:\n{e}")
            print(f"[API EXCEPTION] {e}")

    else:
        st.warning("❌ Tidak terdeteksi. Coba ulangi lagi.")

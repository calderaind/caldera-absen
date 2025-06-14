# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2

# --- Setup halaman Streamlit ---
st.set_page_config(page_title="Scanner Barcode/QR", layout="centered")
st.title("Scanner Absen 📷")

# --- Ambil foto dari kamera ---
img_buffer = st.camera_input("Arahkan kamera ke barcode/QR dan ambil foto Barcode")

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
        # Jika terdeteksi, tampilkan hasil
        st.success(f"✉️ Email ter-scan: {data}")
        print(f"[SCAN] {data}")  # juga ke console Python
    else:
        st.warning("❌ Tidak terdeteksi. Coba ulangi lagi.")

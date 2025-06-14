# app.py

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests

# 1. Setup halaman
st.set_page_config(page_title="Scanner Absen", layout="centered")
st.title("📷 Scanner Absen dengan Lokasi")

# 2. Ambil foto dari kamera
img_buffer = st.camera_input("Arahkan kamera ke QR/barcode dan ambil foto")

if img_buffer:
    # 2a. Preview hasil foto
    img = Image.open(img_buffer)
    st.image(img, caption="Preview", use_column_width=True)

    # 2b. Convert PIL → OpenCV BGR
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # 2c. Decode QR/barcode
    detector = cv2.QRCodeDetector()
    email, points, _ = detector.detectAndDecode(img_cv)

    if email:
        st.success(f"✉️ Email ter-scan: {email}")
        print(f"[SCAN] {email}")

        # 3. Dapatkan lokasi via IP
        def get_geo():
            try:
                r = requests.get("https://ipapi.co/json/", timeout=5)
                r.raise_for_status()
                js = r.json()
                return js.get("latitude"), js.get("longitude")
            except Exception as e:
                print("⚠️ Gagal ambil geolocation:", e)
                return None, None

        lat, lng = get_geo()
        if lat is not None and lng is not None:
            st.info(f"📍 Lokasi (dari IP): {lat:.6f}, {lng:.6f}")
        else:
            st.warning("⚠️ Lokasi tidak tersedia.")

        # 4. Panggil API absen dengan lat & long
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params = {"lat": lat, "long": lng}
        try:
            resp = requests.get(api_url, params=params, timeout=5)
            if resp.ok:
                result = resp.json()
                st.markdown("**✅ Response server:**")
                st.json(result)
                print(f"[API 200] {api_url}?lat={lat}&long={lng} →", result)
            else:
                st.error(f"❌ API Error {resp.status_code}")
                st.write(resp.text)
                print(f"[API ERROR] {resp.status_code}", resp.text)
        except Exception as e:
            st.error(f"⚠️ Gagal koneksi ke API:\n{e}")
            print(f"[API EXCEPTION]", e)

    else:
        st.warning("❌ QR/barcode tidak terdeteksi. Coba ulangi.")

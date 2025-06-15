import streamlit as st
import numpy as np
import cv2
from PIL import Image
from streamlit_js_eval import get_geolocation
import requests
from datetime import datetime
import pytz
from zoneinfo import ZoneInfo

# ════════════════════════════════════════
# 0. Konfigurasi halaman
# ════════════════════════════════════════
st.set_page_config("Caldera Absen", layout="centered")
st.title("📸→📍 Caldera Absen")

# State helper
if "qr_data" not in st.session_state:
    st.session_state["qr_data"] = None
if "coords" not in st.session_state:
    st.session_state["coords"] = None

# ════════════════════════════════════════
# 1. Capture / upload barcode dulu
# ════════════════════════════════════════
st.header("LScan barcode/QR")

cam_image = st.camera_input("Ambil foto barcode/QR")

image_src = cam_image

def decode_qr(pil_img):
    """Return decoded text or None."""
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    val, _, _ = detector.detectAndDecode(img)
    return val if val else None

if image_src and st.session_state["qr_data"] is None:
    pil = Image.open(image_src)
    data = decode_qr(pil)
    if data:
        st.success(f"✅ QR ter-decode: **{data}**")
        st.session_state["qr_data"] = data
    else:
        st.error("❌ QR tidak terdeteksi—coba ulangi, pastikan fokus & cahaya cukup.")

# ════════════════════════════════════════
# 2. Minta geolokasi **setelah** QR sukses
# ════════════════════════════════════════
if st.session_state["qr_data"]:
    st.header("Ambil lokasi")
    if st.session_state["coords"] is None:
        with st.spinner("Meminta izin lokasi ke browser…"):
            try:
                geo = get_geolocation()  # dialog Allow Location
                st.session_state["coords"] = {
                    "lat": geo["coords"]["latitude"],
                    "lon": geo["coords"]["longitude"],
                    "acc": geo["coords"].get("accuracy", "–")
                }
            except Exception as e:
                st.error(f"Gagal mendapat geolokasi: {e}")
    if st.session_state["coords"]:
        lat  = st.session_state["coords"]["lat"]
        lon  = st.session_state["coords"]["lon"]
        acc  = st.session_state["coords"]["acc"]
        st.success(f"📍 Koordinat: {lat:.6f}, {lon:.6f} (±{acc} m)")

# ════════════════════════════════════════
# 3. Kirim Check-In  (tombol aktif kalau dua-duanya OK)
# ════════════════════════════════════════
if st.session_state["qr_data"] and st.session_state["coords"]:
    st.header("Kirim Absen")

    # Asumsikan isi QR = email; jika bukan, user bisa edit
    email_default = st.session_state["qr_data"] if "@" in st.session_state["qr_data"] else "caldera.indonesia2017@gmail.com"
    email = st.text_input("✉️ Email", value=email_default)

    # Waktu WIB
    wib = ZoneInfo("Asia/Jakarta")
    time_iso = datetime.now(wib).isoformat()

    print(time_iso)

    if st.button("✅ SUBMIT"):
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params  = {"lat": lat, "long": lon, "time": time_iso}

        with st.spinner("Mengirim ke server…"):
            try:
                r = requests.get(api_url, params=params, timeout=10)
                r.raise_for_status()
                st.json(r.json())
                st.success("🎉 Check-in berhasil!")
                # Hapus state biar bisa coba lagi
                st.session_state.qr_data = None
                st.session_state.coords  = None
            except Exception as err:
                st.error(f"Check-in gagal: {err}")

st.markdown("---")
st.caption(
    "Alur wajib: ① scan barcode/QR → ② izinkan lokasi → ③ kirim ke server.\n"
    "Tidak perlu Google Geolocation API, sehingga bebas dari error 404."
)

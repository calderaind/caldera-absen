# app.py
"""
Streamlit – Scanner Absen
• Scan QR (e-mail) via kamera
• Minta izin geolocation → lat, long, waktu lokal device
• Fallback ke IP geolocation jika user menolak
• Kirim data ke endpoint absen
"""

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime


# ---------- util ----------
def get_device_location_and_time():
    """
    Jalankan JavaScript dari browser:
    • navigator.geolocation → lat, lon (akurasi meter)
    • local Date() → ISO-8601 waktu lokal device
    Return dict {'lat': float, 'lon': float, 'local_time': str} or None
    """
    js_code = """
    const getCoords = () => new Promise((resolve) => {
        if (!navigator.geolocation) { resolve(null); return; }

        navigator.geolocation.getCurrentPosition(
            pos => {
                const { latitude, longitude } = pos.coords;
                const nowISO = new Date().toISOString();
                resolve({lat: latitude, lon: longitude, local_time: nowISO});
            },
            _err => resolve(null),
            { enableHighAccuracy: true, timeout: 5000 }
        );
    });
    await getCoords();
    """
    return streamlit_js_eval(js_code=js_code, key="device_geolocation")


def ip_geolocation_fallback():
    """Kurang akurat, tapi tetap berguna jika user tolak izin lokasi."""
    try:
        res = requests.get("https://ipapi.co/json/", timeout=5)
        res.raise_for_status()
        j = res.json()
        return {"lat": j.get("latitude"), "lon": j.get("longitude"), "local_time": None}
    except Exception:
        return None


# ---------- main ----------
def main() -> None:
    st.set_page_config(page_title="Scanner Absen", layout="centered")
    st.title("Scanner Absen")

    # --- Ambil foto QR/barcode ---
    buf = st.camera_input("Arahkan kamera ke QR/barcode lalu klik **Capture**")
    if not buf:
        st.info("📸 Tunggu foto di-capture.")
        st.stop()

    img = Image.open(buf)
    st.image(img, caption="Preview foto", use_column_width=True)

    # --- Decode QR (OpenCV) ---
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    email, *_ = detector.detectAndDecode(img_cv)

    if not email:
        st.error("❌ QR/barcode tidak terdeteksi. Coba ulangi.")
        st.stop()

    st.success(f"✉️ Email ter-scan: **{email}**")

    # --- Geolocation (GPS/Wi-Fi) ---
    with st.spinner("📍 Meminta izin lokasi perangkat…"):
        dev_info = get_device_location_and_time()

    if dev_info is None or dev_info.get("lat") is None:
        st.warning("⚠️ Lokasi device ditolak/gagal. Coba IP geolocation…")
        dev_info = ip_geolocation_fallback()

    if dev_info and dev_info.get("lat") is not None:
        lat, lon = dev_info["lat"], dev_info["lon"]
        ltime_iso = dev_info.get("local_time") or datetime.now().isoformat()
        st.success(f"📍 Lokasi: {lat:.6f}, {lon:.6f}")
        if dev_info.get("local_time"):
            st.info(f"🕒 Waktu lokal device: {ltime_iso}")
    else:
        lat = lon = ltime_iso = None
        st.warning("⚠️ Tidak berhasil mendapatkan lokasi apa pun.")

    # --- Kirim ke API ---
    api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
    params = {}
    if lat is not None and lon is not None:
        params.update({"lat": lat, "long": lon})
    if ltime_iso:
        params["time"] = ltime_iso

    qs = ("?" + "&".join(f"{k}={v}" for k, v in params.items())) if params else ""
    st.info(f"🔄 Mengirim ke API: `{api_url}{qs}`")

    try:
        r = requests.get(api_url, params=params, timeout=5)
        r.raise_for_status()
        st.markdown("**✅ Response dari server:**")
        st.json(r.json())
    except Exception as e:
        st.error(f"❌ Gagal koneksi/API:\n{e}")


if __name__ == "__main__":
    main()

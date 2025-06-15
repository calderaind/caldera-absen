# app.py
"""
Scanner Absen – selalu minta izin lokasi
----------------------------------------
• Scan QR (email)
• Paksa browser mem-prompt geolocation setiap reload
  (navigator.permissions.revoke → prompt → getCurrentPosition)
• Fallback IP-lookup jika user menolak / revoke tak tersedia
• Reverse-geocode ke nama kota
• Kirim: lat, long, time, tz, city
"""

import streamlit as st
from PIL import Image
import numpy as np
import cv2
import requests
from streamlit_js_eval import streamlit_js_eval
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def get_fresh_location():
    """
    1. Cek permission; kalau 'granted' → revoke() supaya kembali 'prompt'
    2. Minta getCurrentPosition (akurasi tinggi)
    3. Return dict {lat, lon, local_time, tz_offset_min} | None
    """
    js_code = r"""
    const pad = n => n.toString().padStart(2,'0');

    async function forcePromptAndGet() {
      // ① Paksa kembali prompt jika sudah 'granted'
      try {
        const p = await navigator.permissions.query({name:'geolocation'});
        if (p.state === 'granted' && navigator.permissions.revoke) {
          await navigator.permissions.revoke({name:'geolocation'});
        }
      } catch(e) {/* ignore */ }

      // ② Sekarang minta posisi (akan tampil popup)
      return new Promise(resolve => {
        if (!navigator.geolocation) { resolve(null); return; }

        navigator.geolocation.getCurrentPosition(
          pos => {
            const { latitude, longitude } = pos.coords;
            const d  = new Date();
            const iso = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}` +
                        `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
            resolve({
              lat: latitude,
              lon: longitude,
              local_time: iso,
              tz_offset_min: -d.getTimezoneOffset()      // Jakarta 420
            });
          },
          _err => resolve(null),                        // user tolak / error
          { enableHighAccuracy:true, timeout:5000 }
        );
      });
    }

    await forcePromptAndGet();
    """
    return streamlit_js_eval(js_code=js_code, key="force_geo_prompt")

def ip_geolocation():
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        r.raise_for_status()
        j = r.json()
        return {
            "lat": j.get("latitude"),
            "lon": j.get("longitude"),
            "local_time": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "tz_offset_min": 0
        }
    except Exception:
        return None

def reverse_geocode(lat: float, lon: float) -> str | None:
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10},
            headers={"User-Agent":"absen-app/1.0"}, timeout=5
        )
        r.raise_for_status()
        addr = r.json().get("address", {})
        return addr.get("city") or addr.get("town") or addr.get("state")
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────
# Streamlit app
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Scanner Absen", layout="centered")
st.title("Scanner Absen")

# 1️⃣ Ambil foto QR
buf = st.camera_input("Arahkan kamera ke QR/barcode lalu klik **Capture**")
if not buf:
    st.info("📸 Ambil foto terlebih dahulu…")
    st.stop()

# 2️⃣ Decode QR ➜ email
img = Image.open(buf)
st.image(img, caption="Preview foto", use_column_width=True)
email, *_ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
if not email:
    st.error("❌ QR/barcode tidak terdeteksi.")
    st.stop()
st.success(f"✉️ Email: **{email}**")

# 3️⃣ Paksa prompt lokasi
with st.spinner("📍 Meminta izin lokasi (akan muncul popup)…"):
    geo = get_fresh_location()

if not geo or geo.get("lat") is None:
    st.warning("⚠️ User menolak atau gagal. Coba IP geolocation…")
    geo = ip_geolocation()

if not geo or geo.get("lat") is None:
    st.error("❌ Tidak bisa mendapatkan koordinat apa pun.")
    st.stop()

lat, lon      = geo["lat"], geo["lon"]
local_time    = geo["local_time"]
tz_offset_min = geo["tz_offset_min"]
st.success(f"📍 {lat:.6f}, {lon:.6f}")
st.info(f"🕒 {local_time} (offset {tz_offset_min:+} menit)")

# 4️⃣ Reverse-geocode → kota
with st.spinner("🔍 Menentukan kota…"):
    city = reverse_geocode(lat, lon) or "-"
st.write(f"🏙️ Kota terdekat: **{city}**")

# 5️⃣ Kirim ke API
api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
params  = {
    "lat": lat, "long": lon,
    "time": local_time,
    "tz":   tz_offset_min,
    "city": city,
}
st.info(f"🔄 `{api_url}?{'&'.join(f'{k}={v}' for k,v in params.items())}`")
try:
    r = requests.get(api_url, params=params, timeout=5)
    r.raise_for_status()
    st.markdown("### ✅ Respons Server")
    st.json(r.json())
except Exception as e:
    st.error(f"❌ Gagal koneksi/API:\n{e}")

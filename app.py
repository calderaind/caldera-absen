# app.py
import streamlit as st
import requests
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation  # pip install streamlit_js_eval

st.set_page_config("Check-In App", layout="centered")
st.title("🗺️ Check-In Caldera")

# 1. Ambil geolokasi dari browser
with st.spinner("Mengambil lokasi…"):
    try:
        geo = get_geolocation()  # akan memicu prompt izin Location di browser
        lat = geo["coords"]["latitude"]
        lon = geo["coords"]["longitude"]
    except Exception as e:
        st.error(f"Gagal dapatkan lokasi: {e}")
        st.stop()

st.success(f"📍 Lokasi: {lat:.6f}, {lon:.6f}")

# 2. Waktu lokal Jakarta
tz_jkt = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(tz_jkt)
time_iso = now_jkt.isoformat()  # e.g. '2025-06-15T08:38:12.345+07:00'
st.write("⏰ Waktu (WIB):", now_jkt.strftime("%Y-%m-%d %H:%M:%S"))

# 3. Input email dan tombol Check-In
email = st.text_input("✉️ Email akun", "caldera.indonesia2017@gmail.com")
if st.button("✅ Check-In"):
    url = (
        f"https://caldera.digisight-id.com/public/api/absen/"
        f"{email}?lat={lat}&long={lon}&time={time_iso}"
    )
    with st.spinner("Mengirim data ke server…"):
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            st.json(data)
            st.success("Check-in berhasil tercatat 🎉")
        except Exception as err:
            st.error(f"Gagal check-in: {err}")

# Footer
st.markdown("---")
st.caption("Pastikan Anda sudah allow Location dan mengakses via HTTPS.")

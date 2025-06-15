# app.py

import streamlit as st
import requests
from datetime import datetime
import pytz

# ————————————————
# 1. Konfigurasi Halaman
# ————————————————
st.set_page_config(
    page_title="Caldera Check-In",
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.title("🗺️ Check-In via Google Maps API")

# ————————————————————————————————
# 2. Ambil Google API Key dari secrets.toml
# ————————————————————————————————
try:
    GOOGLE_API_KEY = "AIzaSyCjnPEeMHTMyMJV_dORJS0sIL-sImZgXHw"
except Exception:
    st.error("⚠️ Tambahkan `google_maps_api_key` di ~/.streamlit/secrets.toml")
    st.stop()

# —————————————————————————————————————————————————
# 3. Geolocation: Google Geolocation API (bukan IP-fallback)
# —————————————————————————————————————————————————
with st.spinner("Menentukan lokasi via Google Geolocation API…"):
    try:
        response = requests.post(
            "https://www.googleapis.com/geolocation/v1/geolocate",
            params={"key": GOOGLE_API_KEY},
            json={}  # kosong → Google akan pakai Wi-Fi/Cell default
        )
        response.raise_for_status()
        loc = response.json()["location"]
        lat, lon = loc["lat"], loc["lng"]
        st.success(f"📍 Koordinat: {lat:.6f}, {lon:.6f}")
    except Exception as e:
        st.error(f"Gagal geolokasi: {e}")
        st.stop()

# ————————————————————————————————
# 4. Reverse-Geocoding untuk validasi area
# ————————————————————————————————
with st.spinner("Memeriksa apakah lokasi di Jakarta…"):
    try:
        geocode = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "latlng": f"{lat},{lon}",
                "key": GOOGLE_API_KEY,
                "language": "id"
            }
        ).json()
        components = geocode["results"][0]["address_components"]
        # cari nama provinsi/kabupaten
        area = next(
            (c["long_name"] for c in components
             if "administrative_area_level_1" in c["types"]
             or "administrative_area_level_2" in c["types"]),
            None
        )
        st.info(f"🏙️ Teridentifikasi area: **{area}**")
        if area is None or "Jakarta" not in area:
            st.error("❌ Lokasi tidak di Jakarta → check-in diblokir.")
            st.stop()
    except Exception as e:
        st.error(f"Gagal reverse-geocoding: {e}")
        st.stop()

# ————————————————————————————————
# 5. Waktu Lokal Asia/Jakarta (WIB)
# ————————————————————————————————
tz_jkt  = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(tz_jkt)
time_iso = now_jkt.isoformat()   # e.g. '2025-06-15T08:38:12.345+07:00'
st.write("⏰ Waktu (WIB):", now_jkt.strftime("%Y-%m-%d %H:%M:%S"))

# ————————————————————————————————
# 6. Form Input & Tombol Check-In
# ————————————————————————————————
email = st.text_input(
    "✉️ Email akun",
    value="caldera.indonesia2017@gmail.com",
    help="Masukkan email yang terdaftar di sistem Caldera"
)

if st.button("✅ Check-In"):
    api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
    params  = {"lat": lat, "long": lon, "time": time_iso}

    with st.spinner("Mengirim data ke server…"):
        try:
            r = requests.get(api_url, params=params)
            r.raise_for_status()
            st.json(r.json())
            st.success("🎉 Check-in berhasil tercatat!")
        except Exception as err:
            st.error(f"Gagal check-in: {err}")

# ————————————————————————————————
# 7. Footer / Catatan
# ————————————————————————————————
st.markdown("---")
st.caption("⚙️ Pastikan:\n"
           "1. Anda menggunakan HTTPS (atau localhost).\n"
           "2. Di Google Cloud Console sudah ENABLE:\n"
           "   • Maps Geolocation API\n"
           "   • Maps Geocoding API\n"
           "3. API key benar dan berhak akses kedua service di atas.")

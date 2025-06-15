# app.py

import streamlit as st
import requests
from datetime import datetime
import pytz

# ————————————————
# 1. Setup Streamlit
# ————————————————
st.set_page_config(
    page_title="Caldera Check-In",
    layout="centered",
    initial_sidebar_state="collapsed"
)
st.title("🗺️ Check-In via Google Maps API")

# ————————————————————————————————
# 2. Hard-coded Google API Key
# ————————————————————————————————
GOOGLE_API_KEY = "AIzaSyCjnPEeMHTMyMJV_dORJS0sIL-sImZgXHw"

# ——————————————————————————————————————————————
# 3. Google Geolocation API
# ——————————————————————————————————————————————
with st.spinner("Menentukan lokasi via Google Geolocation API…"):
    try:
        resp = requests.post(
            "https://www.googleapis.com/geolocation/v1/geolocate",
            params={"key": GOOGLE_API_KEY},
            json={}
        )
        resp.raise_for_status()
        loc = resp.json().get("location", {})
        lat, lon = loc.get("lat"), loc.get("lng")
        if lat is None or lon is None:
            raise ValueError("Response tidak mengandung lokasi")
        st.success(f"📍 Koordinat: {lat:.6f}, {lon:.6f}")
    except Exception as e:
        st.error(f"Gagal geolokasi: {e}")
        st.stop()

# ————————————————————————————————
# 4. Reverse-Geocoding untuk validasi area
# ————————————————————————————————
with st.spinner("Memeriksa area via reverse-geocoding…"):
    try:
        geo = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "latlng": f"{lat},{lon}",
                "key": GOOGLE_API_KEY,
                "language": "id"
            }
        ).json()
        comps = geo["results"][0]["address_components"]
        area = next(
            (c["long_name"] for c in comps
             if "administrative_area_level_1" in c["types"]
             or "administrative_area_level_2" in c["types"]),
            None
        )
        st.info(f"🏙️ Area terdeteksi: **{area}**")
        if not area or "Jakarta" not in area:
            st.error("❌ Lokasi bukan Jakarta → check-in diblokir.")
            st.stop()
    except Exception as e:
        st.error(f"Gagal reverse-geocoding: {e}")
        st.stop()

# ————————————————————————————————
# 5. Waktu Lokal Asia/Jakarta (WIB)
# ————————————————————————————————
tz_jkt  = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(tz_jkt)
time_iso = now_jkt.isoformat()
st.write("⏰ Waktu (WIB):", now_jkt.strftime("%Y-%m-%d %H:%M:%S"))

# ————————————————————————————————
# 6. Input Email & Check-In
# ————————————————————————————————
email = st.text_input(
    "✉️ Email akun",
    value="caldera.indonesia2017@gmail.com"
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
# 7. Footer
# ————————————————————————————————
st.markdown("---")
st.caption(
    "⚙️ Pastikan:\n"
    "1. Anda mengakses via HTTPS (atau localhost).\n"
    "2. Di Google Cloud Console sudah ENABLE:\n"
    "   • Maps Geolocation API\n"
    "   • Maps Geocoding API\n"
    "3. API key sudah di-hardcode di atas dan aktif."
)

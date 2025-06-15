import streamlit as st
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="Check-In Caldera", layout="centered")
st.title("🗺️ Check-In via Google Maps API")

# 1. Ambil API Key dari Streamlit Secrets
GOOGLE_API_KEY = "AIzaSyCjnPEeMHTMyMJV_dORJS0sIL-sImZgXHw"

# 2. Geolocation menggunakan Google Geolocation API
with st.spinner("Menentukan lokasi via Google Geolocation API…"):
    try:
        geo_res = requests.post(
            "https://www.googleapis.com/geolocation/v1/geolocate",
            params={"key": GOOGLE_API_KEY},
            json={}  # kosong → Google akan pakai cell/wifi default
        )
        geo_res.raise_for_status()
        loc = geo_res.json()["location"]
        lat, lon = loc["lat"], loc["lng"]
        st.success(f"📍 Koordinat: {lat:.6f}, {lon:.6f}")
    except Exception as e:
        st.error(f"Gagal geolokasi: {e}")
        st.stop()

# 3. Reverse geocoding untuk validasi area (Jakarta)
with st.spinner("Memeriksa area via reverse-geocoding…"):
    try:
        rev = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "latlng": f"{lat},{lon}",
                "key": GOOGLE_API_KEY,
                "language": "id"
            }
        ).json()
        # ambil administrative_area_level_2 atau _1
        comps = rev["results"][0]["address_components"]
        area = next(
            (c["long_name"] for c in comps
             if "administrative_area_level_2" in c["types"]
             or "administrative_area_level_1" in c["types"]),
            None
        )
        st.info(f"Teridentifikasi area: **{area}**")
        if not area or "Jakarta" not in area:
            st.error("❌ Lokasi bukan di Jakarta → check-in diblokir.")
            st.stop()
    except Exception as e:
        st.error(f"Gagal reverse-geocoding: {e}")
        st.stop()

# 4. Waktu lokal Asia/Jakarta (WIB)
tz_jkt  = pytz.timezone("Asia/Jakarta")
now_jkt = datetime.now(tz_jkt)
time_iso = now_jkt.isoformat()
st.write("⏰ Waktu (WIB):", now_jkt.strftime("%Y-%m-%d %H:%M:%S"))

# 5. Input email & tombol check-in
email = st.text_input("✉️ Email akun", "caldera.indonesia2017@gmail.com")
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

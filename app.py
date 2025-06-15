# app.py
import streamlit as st
import requests, json
from datetime import datetime
import pytz

st.set_page_config(page_title="Caldera Check-In", layout="centered")
st.title("🗺️ Check-In via Google Maps API")

API_KEY = "AIzaSyCjnPEeMHTMyMJV_dORJS0sIL-sImZgXHw"   # ← hard-coded

def call_geolocation():
    payload = {"considerIp": True}   # minimal payload
    # 1) endpoint “location.googleapis.com” (Maps Platform)
    url1 = "https://location.googleapis.com/v1/geolocate"
    # 2) endpoint legacy “www.googleapis.com”
    url2 = "https://www.googleapis.com/geolocation/v1/geolocate"

    for url in (url1, url2):
        st.write("🔗 Mencoba:", f"{url}?key=API_KEY")
        resp = requests.post(url, params={"key": API_KEY}, json=payload)
        if resp.status_code == 200:
            return resp.json()["location"]
        # tampilkan isi error utk debugging
        st.warning(f"   → {resp.status_code} {resp.reason}: {resp.text[:120]}…")
    # kalau dua-duanya gagal:
    resp.raise_for_status()

# ──────────────────────────────────────
with st.spinner("Mengambil koordinat…"):
    try:
        loc = call_geolocation()
        lat, lon = loc["lat"], loc["lng"]
        st.success(f"📍 Koordinat: {lat:.6f}, {lon:.6f}")
    except Exception as e:
        st.error(f"Gagal geolokasi: {e}")
        st.stop()

# ── Reverse geocode utk validasi Jakarta ──
with st.spinner("Reverse-geocoding…"):
    try:
        g = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"latlng": f"{lat},{lon}", "key": API_KEY, "language": "id"},
            timeout=10,
        ).json()
        area = next(
            (c["long_name"] for c in g["results"][0]["address_components"]
             if "administrative_area_level_1" in c["types"]
             or "administrative_area_level_2" in c["types"]), None)
        st.info(f"🏙️ Area: **{area}**")
        if not area or "Jakarta" not in area:
            st.error("Lokasi di luar Jakarta → Check-in diblokir.")
            st.stop()
    except Exception as e:
        st.error(f"Reverse-geocode error: {e}")
        st.stop()

# ── Waktu WIB & tombol Check-in ──
now_wib = datetime.now(pytz.timezone("Asia/Jakarta"))
time_iso = now_wib.isoformat()
st.write("⏰ Waktu (WIB):", now_wib.strftime("%Y-%m-%d %H:%M:%S"))

email = st.text_input("✉️ Email", "caldera.indonesia2017@gmail.com")
if st.button("✅ Check-In"):
    api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
    params  = {"lat": lat, "long": lon, "time": time_iso}
    st.write("🔗 ", api_url, params)
    with st.spinner("Mengirim…"):
        try:
            r = requests.get(api_url, params=params, timeout=10)
            r.raise_for_status()
            st.json(r.json())
            st.success("✔️ Check-in sukses!")
        except Exception as err:
            st.error(f"Check-in gagal: {err}")

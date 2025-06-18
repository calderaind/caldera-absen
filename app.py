import streamlit as st
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from streamlit_js_eval import get_geolocation
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import io

# ═════════════════════════════
# 0. Konfigurasi dan helper
# ═════════════════════════════
st.set_page_config("Caldera Absen", layout="centered")
st.title("📸→📍 Caldera Absen + Certificate")

TEMPLATE_PATH   = "./sertif.png"                # file template sertifikat
MAIL_API_URL    = "https://caldera.digisight-id.com/public/api/send-email"

def generate_certificate(name: str) -> bytes:
    # 1) buka template
    img = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # 2) load font TrueType (ukuran besar)
    font_size = 80
    
    try:
        # coba Arial Bold
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except OSError:
        # fallback ke DejaVuSans-Bold (Linux/macOS)
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)

    # 3) hitung bbox teks
    bbox = draw.textbbox((0, 0), name, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 4) posisi center
    x = (W - text_w) / 2
    y = H * 0.31  # sesuaikan jika perlu

    # 5) gambar teks
    draw.text((x, y), name, fill="black", font=font)

    # 6) simpan ke bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
# ═════════════════════════════
# 1. Scan QR
# ═════════════════════════════
if "qr_data" not in st.session_state:
    st.session_state["qr_data"] = None
if "coords" not in st.session_state:
    st.session_state["coords"] = None

st.header("1️⃣ Scan barcode/QR")
cam_image = st.camera_input("Ambil foto barcode/QR")

def decode_qr(pil_img):
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    val, _, _ = detector.detectAndDecode(img)
    return val or None

if cam_image and st.session_state["qr_data"] is None:
    pil = Image.open(cam_image)
    data = decode_qr(pil)
    if data:
        st.success(f"✅ QR ter-decode: **{data}**")
        st.session_state["qr_data"] = data
    else:
        st.error("❌ QR tidak terdeteksi—coba ulangi.")


# ═════════════════════════════
# 2. Ambil geolokasi
# ═════════════════════════════
if st.session_state["qr_data"]:
    st.header("2️⃣ Izinkan lokasi")
    if st.session_state["coords"] is None:
        with st.spinner("Meminta izin…"):
            try:
                geo = get_geolocation()
                st.session_state["coords"] = {
                    "lat": geo["coords"]["latitude"],
                    "lon": geo["coords"]["longitude"],
                    "acc": geo["coords"].get("accuracy", "–")
                }
            except Exception as e:
                st.error(f"Gagal: {e}")
    if st.session_state["coords"]:
        c = st.session_state["coords"]
        st.success(f"📍 {c['lat']:.6f}, {c['lon']:.6f} (±{c['acc']} m)")


# ═════════════════════════════
# 3. Kirim absen & generate sertifikat
# ═════════════════════════════
if st.session_state["qr_data"] and st.session_state["coords"]:
    st.header("3️⃣ Kirim Absen")
    email_default = st.session_state["qr_data"] if "@" in st.session_state["qr_data"] else ""
    email = st.text_input("✉️ Email", value=email_default)
    wib = ZoneInfo("Asia/Jakarta")
    time_iso = datetime.now(wib).isoformat()

    if st.button("✅ SUBMIT"):
        api_url = f"https://caldera.digisight-id.com/public/api/absen/{email}"
        params  = {"lat": st.session_state["coords"]["lat"],
                   "long": st.session_state["coords"]["lon"],
                   "time": time_iso}

        with st.spinner("Mengirim absen…"):
            try:
                r = requests.get(api_url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                st.json(data)
            except Exception as err:
                st.error(f"Absen gagal: {err}")
                st.stop()

        # ---- jika check-out (kode 200) ada 'name' di response
        if r.status_code == 200 and data.get("name"):
            name = data["name"]
            st.success(f"Check-out untuk **{name}** tercatat!")

            # 1) generate certificate
            cert_bytes = generate_certificate(name)
            st.image(cert_bytes, caption="Preview Sertifikat", use_column_width=True)

            # 2) kirim email via API Laravel
            files = {
                "image": ("certificate.png", cert_bytes, "image/png")
            }
            payload = {
                "to": email,
                "subject": "Sertifikat Seminar Caldera",
                # "body": f"Halo {name},\n\nTerima kasih telah hadir. Berikut sertifikat Anda."
                "body": f"Salam hormat,\n\nTeriring salam dan rasa hormat yang setinggi-tingginya, kami menyampaikan ucapan terima kasih yang sebesar-besarnya atas kehadiran Bapak/Ibu dalam kegiatan Seminar STRATEGI SUKSES DIMULAI DARI SMA/SMK yang diselenggarakan pada:\n\n📅 Hari, Tanggal: Kamis, 19 Juni 2025\n📍 Tempat: Ruang TDC, SMA Plus YPHB\n🏙️ Alamat: Jalan Pajajaran, Kota \n\nPartisipasi aktif dan antusiasme Bapak/Ibu dalam mengikuti rangkaian acara menjadi semangat tersendiri bagi kami, Caldera Indonesia dan BMPS Kota Bogor, untuk terus menghadirkan kolaborasi strategis yang memberikan dampak nyata dalam dunia pendidikan, khususnya dalam pengembangan potensi dan perencanaan masa depan siswa-siswi SMA/SMK di era digital saat ini.\n\nKami berharap materi yang disampaikan dalam seminar ini dapat memberikan manfaat, wawasan baru, serta inspirasi dalam mendampingi peserta didik agar lebih memahami arah karier dan kompetensinya di tengah perubahan dunia kerja yang semakin cepat dan kompleks.\n\nSebagai bentuk apresiasi atas partisipasi Bapak/Ibu, bersama ini kami lampirkan sertifikat keikutsertaan yang dikeluarkan oleh Caldera Indonesia dan BMPS Kota Bogor.\n\nSemoga kerja sama ini menjadi langkah awal dari sinergi berkelanjutan dalam membangun masa depan pendidikan yang lebih adaptif dan relevan.\n\nHormat kami,\nTim Caldera Indonesia\nBMPS Kota Bogor"
            }
            with st.spinner("Mengirim email…"):
                mail = requests.post(MAIL_API_URL, data=payload, files=files, timeout=10)
                if mail.ok:
                    st.success("📧 Sertifikat berhasil dikirim ke email.")
                else:
                    st.error(f"Gagal kirim email: {mail.text}")

        # reset state biar bisa absen lagi
        st.session_state.qr_data = None
        st.session_state.coords  = None

# st.markdown("---")
# st.caption("Pastikan file `sertif.png` & font TTF ada di folder project sebelum run.") 

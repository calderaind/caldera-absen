# app.py

import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import av
import cv2
import numpy as np
import requests

st.set_page_config(page_title="Take Photo & Scan QR", layout="centered")
st.title("📷 Camera Capture & QR Scanner")

# 1) Buat processor untuk menyimpan frame terakhir
class PhotoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None      # last frame from camera
        self.captured = False  # flag apakah sudah capture

    def recv(self, video_frame: av.VideoFrame) -> av.VideoFrame:
        img = video_frame.to_ndarray(format="bgr24")
        if not self.captured:
            # selalu update frame selama belum capture
            self.frame = img
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# 2) Tampilkan live‐camera & instansiasi processor
ctx = webrtc_streamer(
    key="photo",
    video_processor_factory=PhotoProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

# 3) Tombol untuk capture
if ctx.video_processor:
    proc: PhotoProcessor = ctx.video_processor

    col1, col2 = st.columns(2)
    with col1:
        take = st.button("📸 Take Photo")
    with col2:
        reset = st.button("🔄 Reset")

    if take:
        proc.captured = True

    if reset:
        proc.captured = False

    # 4) Jika sudah capture, tampilkan snapshot
    if proc.captured and proc.frame is not None:
        st.image(
            proc.frame[:, :, ::-1],  # BGR → RGB
            caption="📷 Captured Photo",
            use_column_width=True
        )

        # 5) Decode QR/barcode
        detector = cv2.QRCodeDetector()
        data, pts, _ = detector.detectAndDecode(proc.frame)
        if data:
            st.success(f"✉️ Email ter-scan: {data}")

            # 6) (Opsional) kirim ke API absen
            api_url = f"https://caldera.digisight-id.com/public/api/absen/{data}"
            try:
                r = requests.get(api_url, timeout=5)
                r.raise_for_status()
                st.json(r.json())
            except Exception as e:
                st.error(f"Gagal memanggil API:\n{e}")
        else:
            st.warning("❌ QR/barcode tidak terdeteksi di foto.")

    else:
        st.info("Arahkan kamera, lalu klik **Take Photo** untuk capture.")

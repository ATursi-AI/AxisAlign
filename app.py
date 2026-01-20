import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import ortho_math
import numpy as np
import matplotlib.pyplot as plt
import time

# 1. Page Config
st.set_page_config(page_title="AxisAlign Precision", layout="wide")
st.title("🦵 AxisAlign: Surgical Planning Suite")

# 2. State
if 'landmarks' not in st.session_state: st.session_state.landmarks = []
if 'cal_points' not in st.session_state: st.session_state.cal_points = []
if 'mm_per_pixel' not in st.session_state: st.session_state.mm_per_pixel = None

# 3. Sidebar
mode = st.sidebar.selectbox("Select Image Type", ["Full Leg (HKA)", "Femur Only (mLDFA)", "Tibia Only (mMPTA)"])
known_mm = st.sidebar.number_input("Marker Size (mm)", value=25.0)
draw_mode = st.sidebar.radio("Tool", ["Add Points", "Tweak/Move"], horizontal=True)
mode_map = {"Add Points": "point", "Tweak/Move": "transform"}

# 4. Upload Logic
uploaded_file = st.file_uploader("Upload Radiograph", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Open and convert
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    
    # Scaling math
    canvas_w = 700 # Slightly smaller to ensure it fits on all screens
    ratio = canvas_w / w
    canvas_h = int(h * ratio)

    # THE FIX: We use a timestamp in the key to force a fresh render
    unique_key = f"canvas_{int(time.time())}"

    st.write(f"📐 Image ready: {w}x{h}")

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#FFFF00",
        background_image=img,
        update_streamlit=True,
        height=canvas_h,
        width=canvas_w,
        drawing_mode=mode_map[draw_mode],
        point_display_radius=6,
        key=unique_key
    )

    # 5. Data Handling
    if canvas_result.json_data is not None:
        objs = canvas_result.json_data["objects"]
        all_pts = [(obj["left"], obj["top"]) for obj in objs if obj["type"] == "circle"]
        st.session_state.cal_points = all_pts[:2]
        st.session_state.landmarks = all_pts[2:]

        # Calibration
        if len(st.session_state.cal_points) == 2 and st.session_state.mm_per_pixel is None:
            p1, p2 = st.session_state.cal_points[0], st.session_state.cal_points[1]
            st.session_state.mm_per_pixel = ortho_math.calculate_mm_pixel_ratio(p1, p2, known_mm)

    # 6. Analysis Preview
    if len(st.session_state.landmarks) >= 2:
        st.success(f"✅ Points Placed: {len(st.session_state.landmarks)}")
        # Show a static preview below to prove the image is loaded
        st.write("### Static Preview (Verification)")
        st.image(img, width=400)
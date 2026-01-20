import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import ortho_math
import numpy as np
import matplotlib.pyplot as plt

# 1. Page Config
st.set_page_config(page_title="AxisAlign Precision", layout="wide")
st.title("🦵 AxisAlign: Surgical Planning Suite")

# 2. State Initialization
if 'landmarks' not in st.session_state: st.session_state.landmarks = []
if 'cal_points' not in st.session_state: st.session_state.cal_points = []
if 'mm_per_pixel' not in st.session_state: st.session_state.mm_per_pixel = None

# 3. Sidebar Controls
mode = st.sidebar.selectbox("Select Image Type", ["Full Leg (HKA)", "Femur Only (mLDFA)", "Tibia Only (mMPTA)"])
known_mm = st.sidebar.number_input("Marker Size (mm)", value=25.0)
draw_mode = st.sidebar.radio("Tool", ["Add Points", "Tweak/Move"], horizontal=True)
mode_map = {"Add Points": "point", "Tweak/Move": "transform"}

# 4. Image Upload
uploaded_file = st.file_uploader("Upload Radiograph", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Use a fixed key tied to the filename so it only refreshes when the file changes
    fixed_key = f"canvas_stable_{uploaded_file.name}"
    
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    canvas_w = 700
    ratio = canvas_w / w
    canvas_h = int(h * ratio)

    st.write(f"📐 Image Dimensions: {w}x{h}")

    # THE STABLE CANVAS
    # THE REFINED CANVAS
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
        key=fixed_key,
        display_toolbar=True,
    )
    

    # 5. Data Processing
    if canvas_result.json_data is not None:
        objs = canvas_result.json_data["objects"]
        all_pts = [(obj["left"], obj["top"]) for obj in objs if obj["type"] == "circle"]
        st.session_state.cal_points = all_pts[:2]
        st.session_state.landmarks = all_pts[2:]

    # 6. Fallback Verification
    # If the canvas is blank, this will prove the image is at least loaded in memory
    st.write("---")
    st.write("### Verification Preview")
    st.image(img, caption="Original Upload (Verification Only)", width=300)
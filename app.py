import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import ortho_math
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="AxisAlign Precision", layout="wide")
st.title("🦵 AxisAlign: Surgical Planning Suite")

# 1. State
if 'landmarks' not in st.session_state: st.session_state.landmarks = []
if 'cal_points' not in st.session_state: st.session_state.cal_points = []
if 'mm_per_pixel' not in st.session_state: st.session_state.mm_per_pixel = None

# 2. Sidebar
mode = st.sidebar.selectbox("Select Image Type", ["Full Leg (HKA)", "Femur Only (mLDFA)", "Tibia Only (mMPTA)"])
known_mm = st.sidebar.number_input("Marker Size (mm)", value=25.0)
draw_mode = st.sidebar.radio("Tool", ["Add Points", "Tweak/Move"], horizontal=True)
mode_map = {"Add Points": "point", "Tweak/Move": "transform"}

# 3. Upload
uploaded_file = st.file_uploader("Upload Radiograph", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    canvas_w = 800
    ratio = canvas_w / w
    canvas_h = int(h * ratio)

    # The Canvas
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
        key="axisalign_fixed_canvas"
    )

    # 4. Data Logic
    if canvas_result.json_data is not None:
        objs = canvas_result.json_data["objects"]
        all_pts = [(obj["left"], obj["top"]) for obj in objs if obj["type"] == "circle"]
        st.session_state.cal_points = all_pts[:2]
        st.session_state.landmarks = all_pts[2:]

        if len(st.session_state.cal_points) == 2 and st.session_state.mm_per_pixel is None:
            p1, p2 = st.session_state.cal_points[0], st.session_state.cal_points[1]
            st.session_state.mm_per_pixel = ortho_math.calculate_mm_pixel_ratio(p1, p2, known_mm)

    # 5. Simulation & Analysis
    if len(st.session_state.landmarks) >= 3:
        results = ortho_math.run_analysis(mode, st.session_state.landmarks)
        correction = st.sidebar.slider("Simulation (Deg)", -15.0, 15.0, 0.0)
        
        st.write("### 📈 Live Analysis")
        # Visual Plotting
        fig, ax = plt.subplots()
        ax.imshow(img)
        pts = st.session_state.landmarks
        # (Draw lines here...)
        ax.axis('off')
        st.pyplot(fig)
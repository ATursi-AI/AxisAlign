import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import ortho_math
import numpy as np
import matplotlib.pyplot as plt

# 1. Branding
st.set_page_config(page_title="AxisAlign Precision", layout="wide")
st.title("🦵 AxisAlign: Surgical Planning Suite")

LANDMARK_MODES = {
    "Full Leg (HKA)": ["Hip Center", "Knee Center", "Ankle Center", "Fem Lat Condyle", "Fem Med Condyle", "Tib Lat Plateau", "Tib Med Plateau"],
    "Femur Only (mLDFA)": ["Hip Center", "Knee Center", "Fem Lat Condyle", "Fem Med Condyle"],
    "Tibia Only (mMPTA)": ["Knee Center", "Ankle Center", "Tib Lat Plateau", "Tib Med Plateau"]
}

# 2. State Initialization
if 'landmarks' not in st.session_state: st.session_state.landmarks = []
if 'cal_points' not in st.session_state: st.session_state.cal_points = []
if 'mm_per_pixel' not in st.session_state: st.session_state.mm_per_pixel = None

# --- SIDEBAR ---
st.sidebar.header("⚙️ Planning Controls")
mode = st.sidebar.selectbox("Select Image Type", list(LANDMARK_MODES.keys()))
known_mm = st.sidebar.number_input("Marker Size (mm)", value=25.0)
draw_mode = st.sidebar.radio("Tool", ["Add Points", "Tweak/Move"], horizontal=True)
mode_map = {"Add Points": "point", "Tweak/Move": "transform"}

if st.sidebar.button("Reset Data"):
    for key in ['landmarks', 'cal_points', 'mm_per_pixel']: st.session_state[key] = None
    st.rerun()

# --- MAIN UI ---
uploaded_file = st.file_uploader("Upload Radiograph", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    w, h = img.size
    canvas_w = 800
    canvas_h = int(h * (canvas_w / w))

    canvas_result = st_canvas(
        background_image=img, update_streamlit=True, height=canvas_h, width=canvas_w,
        drawing_mode=mode_map[draw_mode], point_display_radius=5, stroke_color="#FFFF00", key="ortho_canvas"
    )

    if canvas_result.json_data is not None:
        objs = canvas_result.json_data["objects"]
        all_pts = [(obj["left"], obj["top"]) for obj in objs if obj["type"] == "circle"]
        st.session_state.cal_points = all_pts[:2]
        st.session_state.landmarks = all_pts[2:]

        if len(st.session_state.cal_points) == 2 and st.session_state.mm_per_pixel is None:
            p1, p2 = st.session_state.cal_points[0], st.session_state.cal_points[1]
            st.session_state.mm_per_pixel = ortho_math.calculate_mm_pixel_ratio(p1, p2, known_mm)

        if len(objs) > 0:
            st.sidebar.markdown("---")
            st.sidebar.header("🔍 Precision Loupe")
            lx, ly = int(objs[-1]["left"]), int(objs[-1]["top"])
            z = 40
            roi = img.crop((max(0, lx-z), max(0, ly-z), min(w, lx+z), min(h, ly+z)))
            st.sidebar.image(roi, use_container_width=True)

    target_list = LANDMARK_MODES[mode]
    if len(st.session_state.landmarks) == len(target_list):
        st.divider()
        results = ortho_math.run_analysis(mode, st.session_state.landmarks)
        
        # Simulation
        correction = st.sidebar.slider("Correction (Deg)", -15.0, 15.0, 0.0)
        
        st.write("### 📊 Metrics & Simulation")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pre-Op HKA", f"{results.get('HKA', 180.0):.2f}°")
        c2.metric("Simulated HKA", f"{results.get('HKA', 180.0) + correction:.2f}°", delta=f"{correction}°")
        
        if st.session_state.mm_per_pixel:
            p_lat, p_med = st.session_state.landmarks[3], st.session_state.landmarks[4]
            px_w = np.linalg.norm(np.array(p_lat) - np.array(p_med))
            wedge = ortho_math.calculate_wedge_height(px_w, abs(correction), st.session_state.mm_per_pixel)
            c3.metric("Wedge Height", f"{wedge:.2f} mm")

        # Visualization
        fig, ax = plt.subplots()
        ax.imshow(img)
        pts = st.session_state.landmarks
        ax.plot([pts[0][0], pts[1][0]], [pts[0][1], pts[1][1]], color='yellow', alpha=0.5)
        ax.plot([pts[1][0], pts[2][0]], [pts[1][1], pts[2][1]], color='yellow', alpha=0.5)
        
        s_pts = ortho_math.get_rotated_points(pts, 1, correction)
        ax.plot([s_pts[0][0], s_pts[1][0]], [s_pts[0][1], s_pts[1][1]], color='lime', linewidth=2)
        ax.plot([s_pts[1][0], s_pts[2][0]], [s_pts[1][1], s_pts[2][1]], color='lime', linewidth=2)
        ax.axis('off')
        st.pyplot(fig)
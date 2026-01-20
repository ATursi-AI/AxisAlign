import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import ortho_math
import numpy as np
import matplotlib.pyplot as plt

# 1. Branding & Config
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
    for key in ['landmarks', 'cal_points', 'mm_per_pixel']:
        st.session_state[key] = None
    st.rerun()

# --- MAIN UI ---
uploaded_file = st.file_uploader("Upload Radiograph", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    
    # Robust Scaling Math
    canvas_w = 800
    ratio = canvas_w / w
    canvas_h = int(h * ratio)
    
    # Safety Check: Ensure canvas isn't invisible
    if canvas_h < 100: canvas_h = 600 

    st.info(f"📐 Resolution: {w}x{h} | Displaying at: {canvas_w}x{canvas_h}")

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=2,
        stroke_color="#FFFF00",
        background_image=img,
        update_streamlit=True,
        height=canvas_h,
        width=canvas_w,
        drawing_mode=mode_map[draw_mode],
        point_display_radius=5,
        key="axis_align_canvas_v1",
    )

    # Handle Data
    if canvas_result.json_data is not None:
        objs = canvas_result.json_data["objects"]
        all_pts = [(obj["left"], obj["top"]) for obj in objs if obj["type"] == "circle"]
        
        # Split Calibration (first 2) from Landmarks
        st.session_state.cal_points = all_pts[:2]
        st.session_state.landmarks = all_pts[2:]

        # Calibration Logic
        if len(st.session_state.cal_points) == 2 and st.session_state.mm_per_pixel is None:
            p1, p2 = st.session_state.cal_points[0], st.session_state.cal_points[1]
            st.session_state.mm_per_pixel = ortho_math.calculate_mm_pixel_ratio(p1, p2, known_mm)

        # 🔍 Precision Loupe Logic
        if len(objs) > 0:
            st.sidebar.markdown("---")
            st.sidebar.header("🔍 Precision Loupe")
            last_obj = objs[-1]
            lx, ly = int(last_obj["left"] / ratio), int(last_obj["top"] / ratio)
            zoom = 60
            roi = img.crop((max(0, lx-zoom), max(0, ly-zoom), min(w, lx+zoom), min(h, ly+zoom)))
            st.sidebar.image(roi, caption="Targeting Accuracy", use_container_width=True)

    # 📊 Analysis and Simulation
    target_list = LANDMARK_MODES[mode]
    current_count = len(st.session_state.landmarks)
    
    st.write(f"**Points Placed:** {current_count} / {len(target_list)}")
    
    if current_count == len(target_list):
        st.divider()
        results = ortho_math.run_analysis(mode, st.session_state.landmarks)
        
        # Simulation Controls
        correction = st.sidebar.slider("Simulate Correction (Deg)", -15.0, 15.0, 0.0)
        
        st.write("### 📈 Analysis Results")
        c1, c2, c3 = st.columns(3)
        
        pre_hka = results.get('HKA', 180.0)
        sim_hka = pre_hka + correction
        
        c1.metric("Pre-Op HKA", f"{pre_hka:.2f}°")
        c2.metric("Simulated HKA", f"{sim_hka:.2f}°", delta=f"{correction}°")
        
        if st.session_state.mm_per_pixel:
            # Estimate wedge based on distance between Femoral Condyles (Points 3 and 4)
            p_lat, p_med = st.session_state.landmarks[3], st.session_state.landmarks[4]
            px_width = np.linalg.norm(np.array(p_lat) - np.array(p_med))
            wedge_mm = ortho_math.calculate_wedge_height(px_width, abs(correction), st.session_state.mm_per_pixel)
            c3.metric("Wedge Height", f"{wedge_mm:.2f} mm")

        # Visual Overlay
        fig, ax = plt.subplots()
        ax.imshow(img)
        pts = st.session_state.landmarks
        
        # Original Axis (Yellow)
        ax.plot([pts[0][0]/ratio, pts[1][0]/ratio], [pts[0][1]/ratio, pts[1][1]/ratio], color='yellow', alpha=0.4, label='Original')
        
        # Simulated Axis (Lime)
        s_pts = ortho_math.get_rotated_points(pts, 1, correction)
        ax.plot([s_pts[0][0]/ratio, s_pts[1][0]/ratio], [s_pts[0][1]/ratio, s_pts[1][1]/ratio], color='#32CD32', linewidth=2, label='Simulated')
        
        ax.axis('off')
        st.pyplot(fig)
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import ortho_math
import numpy as np
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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
    # Load and process image for Base64 injection
    img = Image.open(uploaded_file).convert("RGB")
    w, h = img.size
    canvas_w = 800
    ratio = canvas_w / w
    canvas_h = int(h * ratio)

    # Encode image to Base64 to bypass Streamlit rendering bugs
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    st.info(f"📐 Resolution: {w}x{h} | Displaying at: {canvas_w}x{canvas_h}")

    # Use a unique key based on the file to force fresh renders
    canvas_key = f"canvas_{uploaded_file.name}_{mode}"

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
        key=canvas_key,
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
            last_obj = objs[-1]
            lx, ly = int(last_obj["left"] / ratio), int(last_obj["top"] / ratio)
            zoom = 70
            roi = img.crop((max(0, lx-zoom), max(0, ly-zoom), min(w, lx+zoom), min(h, ly+zoom)))
            st.sidebar.image(roi, caption="Precision Zoom", use_container_width=True)

    target_list = LANDMARK_MODES[mode]
    current_count = len(st.session_state.landmarks)
    st.write(f"**Landmarks:** {current_count} / {len(target_list)}")
    
    if current_count == len(target_list):
        st.divider()
        results = ortho_math.run_analysis(mode, st.session_state.landmarks)
        correction = st.sidebar.slider("Simulation (Deg)", -15.0, 15.0, 0.0)
        
        c1, c2, c3 = st.columns(3)
        pre_hka = results.get('HKA', 180.0)
        sim_hka = pre_hka + correction
        c1.metric("Pre-Op HKA", f"{pre_hka:.2f}°")
        c2.metric("Simulated HKA", f"{sim_hka:.2f}°", delta=f"{correction}°")
        
        if st.session_state.mm_per_pixel:
            p_lat, p_med = st.session_state.landmarks[3], st.session_state.landmarks[4]
            px_w = np.linalg.norm(np.array(p_lat) - np.array(p_med))
            wedge_mm = ortho_math.calculate_wedge_height(px_w, abs(correction), st.session_state.mm_per_pixel)
            c3.metric("Wedge Height", f"{wedge_mm:.2f} mm")

        fig, ax = plt.subplots()
        ax.imshow(img)
        pts = st.session_state.landmarks
        ax.plot([pts[0][0]/ratio, pts[1][0]/ratio], [pts[0][1]/ratio, pts[1][1]/ratio], color='yellow', linestyle='--', alpha=0.6)
        s_pts = ortho_math.get_rotated_points(pts, 1, correction)
        ax.plot([s_pts[0][0]/ratio, s_pts[1][0]/ratio], [s_pts[0][1]/ratio, s_pts[1][1]/ratio], color='#00FF00', linewidth=2)
        ax.axis('off')
        st.pyplot(fig)

        st.sidebar.markdown("---")
        if st.sidebar.button("📄 Prepare Surgical Passport"):
            import exporter
            pdf_data = exporter.generate_surgical_report(mode, results, sim_hka, wedge_mm if 'wedge_mm' in locals() else 0.0)
            st.sidebar.download_button("📥 Download PDF", data=pdf_data, file_name="Surgical_Plan.pdf", mime="application/pdf")
# AxisAlign: Precision Surgical Planning Suite 🦵

AxisAlign is a "Human-in-the-Loop" (HITL) computer vision application designed for orthopedic surgeons to perform pre-operative planning for osteotomies (HTO/DFO).

## 🚀 Key Features
- **Spatial Calibration:** Corrects for radiographic magnification using fiducial markers.
- **Dynamic Simulation:** Uses affine transformation matrices to rotate anatomical segments and predict Post-Op HKA (Hip-Knee-Ankle) alignment.
- **Precision UX:** Integrated ROI (Region of Interest) Loupe to ensure sub-millimeter landmarking accuracy.
- **Patient-Specific Morphometrics:** Calculates required opening wedge height based on real-time Euclidean distance measurements of the bone.

## 🛠️ Technical Stack
- **Frontend:** Streamlit (Reactive State Management)
- **Geometry:** NumPy & Python Math (Trigonometric Identities & Vector Analysis)
- **Computer Vision UI:** Streamlit-Drawable-Canvas
- **Imaging:** Pillow (ROI Extraction)
- **Visualization:** Matplotlib (Vector Overlays)

## 📐 The Math Behind the Medicine
The application calculates the **Opening Wedge Height ($H$)** using the Tangent Identity:
$$H = W \times \tan(\theta)$$
Where $W$ is the measured bone width and $\theta$ is the planned correction angle.

## 👨‍💻 AI Engineer Perspective
This tool serves as a high-fidelity data labeling interface. The manual landmarks acquired provide the **Ground Truth** dataset required to train future Deep Learning models (CNNs) for automated anatomical landmark detection and automated surgical planning.
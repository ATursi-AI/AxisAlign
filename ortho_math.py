import math
import numpy as np

def get_angle_between_vectors(p1, p2, p3, p4):
    """Calculates the angle in degrees between vector p1->p2 and p3->p4."""
    vec1 = (p2[0] - p1[0], p2[1] - p1[1])
    vec2 = (p4[0] - p3[0], p4[1] - p3[1])
    
    angle1 = math.atan2(vec1[1], vec1[0])
    angle2 = math.atan2(vec2[1], vec2[0])
    
    diff = math.degrees(angle1 - angle2)
    return abs(diff)

def run_analysis(mode, points):
    """Orchestrates mathematical calculations based on anatomical mode."""
    results = {}
    if mode == "Full Leg (HKA)":
        results["HKA"] = get_angle_between_vectors(points[0], points[1], points[1], points[2])
        results["mLDFA"] = get_angle_between_vectors(points[0], points[1], points[3], points[4])
        results["mMPTA"] = get_angle_between_vectors(points[1], points[2], points[5], points[6])
    elif mode == "Femur Only (mLDFA)":
        results["mLDFA"] = get_angle_between_vectors(points[0], points[1], points[2], points[3])
    elif mode == "Tibia Only (mMPTA)":
        results["mMPTA"] = get_angle_between_vectors(points[0], points[1], points[2], points[3])
    return results

def calculate_mm_pixel_ratio(p1, p2, known_mm):
    """Establishes spatial scalar for radiographic magnification correction."""
    pixel_distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    return known_mm / pixel_distance if pixel_distance != 0 else 0

def calculate_wedge_height(bone_width_pixels, correction_angle_deg, mm_per_pixel):
    """Calculates opening wedge height via Tangent Identity."""
    angle_rad = math.radians(correction_angle_deg)
    height_pixels = bone_width_pixels * math.tan(angle_rad)
    return height_pixels * mm_per_pixel

def get_rotated_points(points, hinge_index, angle_deg):
    """Simulates distal segment rotation using an Affine Rotation Matrix."""
    if not points or len(points) <= hinge_index:
        return points
        
    pivot = points[hinge_index]
    angle_rad = math.radians(angle_deg)
    ox, oy = pivot
    corrected_points = []
    
    for i, pt in enumerate(points):
        if i > hinge_index: 
            px, py = pt
            qx = ox + math.cos(angle_rad) * (px - ox) - math.sin(angle_rad) * (py - oy)
            qy = oy + math.sin(angle_rad) * (px - ox) + math.cos(angle_rad) * (py - oy)
            corrected_points.append((qx, qy))
        else:
            corrected_points.append(pt)
    return corrected_points
from fpdf import FPDF

def generate_surgical_report(mode, original_metrics, sim_hka, wedge_mm):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AxisAlign: Surgical Planning Report", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Analysis Mode: {mode}", ln=True, align='C')
    pdf.ln(10)

    # Metrics
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Pre-Operative Metrics:", ln=True)
    pdf.set_font("Arial", size=12)
    for label, val in original_metrics.items():
        pdf.cell(200, 10, txt=f"- {label}: {val:.2f} degrees", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Simulated Plan:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"- Predicted HKA: {sim_hka:.2f} degrees", ln=True)
    pdf.cell(200, 10, txt=f"- Opening Wedge Height: {wedge_mm:.2f} mm", ln=True)

    return pdf.output(dest='S').encode('latin-1')
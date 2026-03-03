from fpdf import FPDF
import os
import datetime

class CompliancePackGenerator:
    def __init__(self, pilot_id, output_dir="pilot/evidence"):
        self.pilot_id = pilot_id
        self.output_dir = os.path.join(output_dir, pilot_id)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_safety_case(self, health_stats):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, f"Safety Case: GCO-Engine Pilot {self.pilot_id}", 0, 1, 'C')
        pdf.ln(10)
        
        sections = [
            ("1. System Definition", "The GCO Engine is a pseudo-NMPC controller for 2x2 MIMO batch processes."),
            ("2. Hazard Analysis", "Hazards include out-of-bounds recommendations and network latency."),
            ("3. Mitigations", "Mandatory Golden Corridor checks and local edge deployment."),
            ("4. Validation Evidence", f"Soak test p95 latency: {health_stats.get('reco_p95_ms', 0):.2f} ms.
Violations: {health_stats.get('constraint_violations', 0)}.")
        ]
        
        for title, content in sections:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, title, 0, 1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, content)
            pdf.ln(5)
            
        filename = os.path.join(self.output_dir, "safety_case.pdf")
        pdf.output(filename)
        return filename

    def generate_security_dossier(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "Security & Compliance Dossier", 0, 1, 'C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "1. Threat Model (STRIDE)", 0, 1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, "Spoofing: API Auth
Tampering: Versioned Bounds
Information Disclosure: Local Deployment")
        
        filename = os.path.join(self.output_dir, "security_dossier.pdf")
        pdf.output(filename)
        return filename

if __name__ == "__main__":
    gen = CompliancePackGenerator("P-001")
    gen.generate_safety_case({"reco_p95_ms": 42.5, "constraint_violations": 0})
    gen.generate_security_dossier()
    print(f"Compliance Pack generated in pilot/evidence/P-001/")

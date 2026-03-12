import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def _ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write_pdf(run_id: str, title: str, notes: str, snapshot: dict, chart_paths: list, out_pdf_path: str):
    _ensure_dir(out_pdf_path)
    
    doc = SimpleDocTemplate(out_pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    h2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    story = []
    
    # Cover Page
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Run ID: {run_id}", normal_style))
    story.append(Paragraph(f"Collected At: {snapshot.get('collected_at', 'unknown')}", normal_style))
    story.append(Paragraph(f"Active Version: {snapshot.get('active_version', 'unknown')}", normal_style))
    story.append(Paragraph(f"Mode: {snapshot.get('mode', 'unknown')}", normal_style))
    if notes:
        story.append(Spacer(1, 20))
        story.append(Paragraph("Notes:", h2_style))
        story.append(Paragraph(notes, normal_style))
        
    story.append(PageBreak())
    
    # LLM Summary
    llm_data = snapshot.get("llm")
    if llm_data:
        story.append(Paragraph("Executive Summary", h2_style))
        story.append(Paragraph(str(llm_data.get("summary", "N/A")), normal_style))
        story.append(Spacer(1, 20))
    
    # KPI Highlights Table
    story.append(Paragraph("KPI Highlights (Top 5 Recent)", h2_style))
    kpis = snapshot.get("recent_kpis", [])[:5]
    if kpis:
        # Just show keys of first element as headers
        headers = ["timestamp", "value", "metric"]
        data = [headers]
        for k in kpis:
            data.append([str(k.get("timestamp", "")), str(k.get("value", "")), str(k.get("metric", ""))])
            
        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No recent KPIs available.", normal_style))
        
    story.append(Spacer(1, 20))
    
    # Charts
    for chart in chart_paths:
        if os.path.exists(chart):
            story.append(Paragraph(f"Chart: {os.path.basename(chart)}", h2_style))
            story.append(Image(chart, width=400, height=225))
            story.append(Spacer(1, 20))
            
    # System Metrics
    story.append(PageBreak())
    story.append(Paragraph("System Metrics", h2_style))
    opt_health = snapshot.get("optimizer_health", {})
    for k, v in opt_health.items():
        story.append(Paragraph(f"Optimizer - {k}: {v}", normal_style))
        
    story.append(Spacer(1, 10))
    pol_health = snapshot.get("policy", {})
    for k, v in pol_health.items():
        story.append(Paragraph(f"Policy - {k}: {v}", normal_style))

    doc.build(story)

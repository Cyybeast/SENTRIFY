from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import sqlite3
from datetime import datetime

BRAND = colors.HexColor('#1A0050')
ACCENT = colors.HexColor('#00B89C')
RED = colors.HexColor('#E74C3C')
LIGHT = colors.HexColor('#F0F2F5')
WHITE = colors.white
BLACK = colors.HexColor('#333333')

def get_campaign_report_data(campaign_id):
    conn = sqlite3.connect('sentrify.db')
    c = conn.cursor()
    c.execute('SELECT company_name, campaign_name, template, created_at FROM campaigns WHERE id = ?', (campaign_id,))
    campaign = c.fetchone()
    c.execute('SELECT email, clicked_at, training_completed FROM results WHERE campaign_id = ? ORDER BY clicked_at', (campaign_id,))
    results = c.fetchall()
    conn.close()
    return campaign, results

def generate_report(campaign_id, output_path):
    campaign, results = get_campaign_report_data(campaign_id)
    if not campaign:
        return False

    company_name = campaign[0]
    campaign_name = campaign[1]
    template = campaign[2].upper()
    created_at = campaign[3]
    total = len(results)
    trained = sum(1 for r in results if r[2] == 1)
    not_trained = total - trained
    click_rate = f"{(total / max(total, 1)) * 100:.0f}%"
    training_rate = f"{(trained / max(total, 1)) * 100:.0f}%"

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story = []

    # Header
    header_data = [[
        Paragraph('<font color="#FFFFFF"><b>SENTRIFY</b></font>', ParagraphStyle('h', fontName='Helvetica-Bold', fontSize=22, textColor=WHITE)),
        Paragraph('<font color="#00B89C">Security Awareness Campaign Report</font>', ParagraphStyle('s', fontName='Helvetica', fontSize=11, textColor=ACCENT, alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[9*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BRAND),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # Campaign info
    info_style = ParagraphStyle('info', fontName='Helvetica', fontSize=10, textColor=BLACK, spaceAfter=4)
    bold_style = ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=10, textColor=BRAND)

    story.append(Paragraph(f'<b>Company:</b> {company_name}', info_style))
    story.append(Paragraph(f'<b>Campaign:</b> {campaign_name}', info_style))
    story.append(Paragraph(f'<b>Template Used:</b> {template}', info_style))
    story.append(Paragraph(f'<b>Date Generated:</b> {datetime.now().strftime("%d %B %Y, %I:%M %p")}', info_style))
    story.append(Paragraph(f'<b>Campaign Created:</b> {created_at}', info_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.5*cm))

    # Summary stats
    story.append(Paragraph('<b>Campaign Summary</b>', ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=13, textColor=BRAND, spaceAfter=10)))

    stats_data = [
        ['Metric', 'Value'],
        ['Total Employees Tested', str(total)],
        ['Employees Who Clicked', str(total)],
        ['Training Completed', str(trained)],
        ['Training Incomplete', str(not_trained)],
        ['Training Completion Rate', training_rate],
    ]
    stats_table = Table(stats_data, colWidths=[10*cm, 7*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('TEXTCOLOR', (0,1), (-1,-1), BLACK),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.6*cm))

    # Individual results
    story.append(Paragraph('<b>Individual Employee Results</b>', ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=13, textColor=BRAND, spaceAfter=10)))

    results_data = [['#', 'Email Address', 'Time Clicked', 'Training Status']]
    for i, r in enumerate(results):
        status = '✓ Completed' if r[2] == 1 else '✗ Incomplete'
        results_data.append([str(i+1), r[0], r[1], status])

    results_table = Table(results_data, colWidths=[1*cm, 7.5*cm, 5*cm, 3.5*cm])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('PADDING', (0,0), (-1,-1), 7),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('TEXTCOLOR', (0,1), (-1,-1), BLACK),
    ]))

    # Color training status column
    for i, r in enumerate(results):
        color = ACCENT if r[2] == 1 else RED
        results_table.setStyle(TableStyle([
            ('TEXTCOLOR', (3, i+1), (3, i+1), color),
            ('FONTNAME', (3, i+1), (3, i+1), 'Helvetica-Bold'),
        ]))

    story.append(results_table)
    story.append(Spacer(1, 0.6*cm))

    # Compliance statement
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('<b>Compliance Statement</b>', ParagraphStyle('sec', fontName='Helvetica-Bold', fontSize=13, textColor=BRAND, spaceAfter=8)))

    compliance_text = f"""
    This report certifies that <b>{company_name}</b> conducted a security awareness phishing simulation
    campaign titled <b>"{campaign_name}"</b> on <b>{created_at}</b> using the Sentrify Human Risk Management Platform.
    A total of <b>{total} employees</b> participated in the simulation, of which <b>{trained} ({training_rate})</b>
    successfully completed the mandatory security awareness training module.<br/><br/>
    This campaign was conducted in accordance with organisational security awareness obligations under the
    Nigeria Data Protection Regulation (NDPR), Central Bank of Nigeria (CBN) cybersecurity guidelines,
    and applicable information security best practices.<br/><br/>
    <i>Generated by Sentrify — Africa's Human Risk Management Platform</i>
    """
    story.append(Paragraph(compliance_text, ParagraphStyle('comp', fontName='Helvetica', fontSize=9, textColor=BLACK, leading=14)))

    doc.build(story)
    return True

if __name__ == '__main__':
    generate_report(1, 'test_report.pdf')
    print("Report generated.")

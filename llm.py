from llama_cpp import Llama
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import json
from datetime import datetime
current_date = datetime.now()

with open('details.json', 'r') as file:
    data = json.load(file)

# Load the model
MODEL = Llama(model_path=r"models\aya-expanse-8b-Q5_K_S.gguf", n_ctx=3000, n_threads=5, n_gpu_layers=-1)

def generate_cover_letter(job_description):
    print("generating cover")
    applicant_info = data['content']
    prompt = f"""
    Job Description:
    {job_description}

    Applicant Information:
    {applicant_info}

    <｜User｜> Write a small professional cover letter for this job application and just output the content of the cover letter.
    <|Assistant|>
    """
    
    output = MODEL(prompt,max_tokens=1000, stop=["Sincerely,", "Best regards,","<｜User｜>", "<｜Assistant｜>"], echo=False)
    return output['choices'][0]['text'].strip()


def create_cover_letter_pdf(content, title, company):
    print("saving pdf")
    name = data['name']
    email = data['email']
    website = data['website']
    
    # Register Calibri font (adjust path as needed)
    pdfmetrics.registerFont(TTFont('Calibri', 'Calibri.ttf'))

    # Use A4 with 1-inch (72 pt) margins
    doc = SimpleDocTemplate(f"coverLetter/{title.replace('/', '-')}-{company}.pdf", pagesize=A4,
                            leftMargin=72, rightMargin=72,
                            topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()
    # Custom styles to mimic the LaTeX template
    header_name_style = ParagraphStyle(
        'HeaderName',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=24,
        leading=28,
        alignment=TA_LEFT,
        spaceAfter=4
    )
    header_website_style = ParagraphStyle(
        'HeaderWebsite',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=12,
        textColor=colors.gray,
        alignment=TA_LEFT,
        spaceAfter=12
    )
    date_style = ParagraphStyle(
        'Date',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT
    )
    address_style = ParagraphStyle(
        'Address',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=11,
        leading=14,
        alignment=TA_RIGHT
    )
    greeting_style = ParagraphStyle(
        'Greeting',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=12
    )
    closing_style = ParagraphStyle(
        'Closing',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=2
    )
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontName='Calibri',
        fontSize=11,
        leading=14,
        alignment=TA_LEFT
    )

    story = []

    # Header: Name and Website (mimicking \header{...}{...})
    story.append(Paragraph(f"<b>{name}</b>", header_name_style))
    story.append(Paragraph(website, header_website_style))
    story.append(Spacer(1, 28))  # ~1cm vertical space
    formatted_date = current_date.strftime("%d %b %Y").lstrip("0")
    # Date and Address block (mimicking \dateAndAddress)
    # Left: fixed date ("2 Feb 2025"); Right: address details
    date_text = f"<b>{formatted_date}</b>"
    address_text = ("7 Eaton PL<br/>"
                    "Binghamton, NY 13905<br/>"
                    "(607) 296-9098<br/>"
                    f"<a href='mailto:{email}'>{email}</a>")
    date_para = Paragraph(date_text, date_style)
    address_para = Paragraph(address_text, address_style)
    # Table with two columns (approximate widths: left=271, right=180)
    table = Table([[date_para, address_para]], colWidths=[271, 180])
    table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LINEBELOW', (0,0), (-1,0), 0, colors.white)
    ]))
    story.append(table)
    story.append(Spacer(1, 24))

    # Opening Greeting
    story.append(Paragraph("<b>Dear Hiring Manager,</b>", greeting_style))

    # Body: Split the provided content into paragraphs
    for para in content.strip().split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))

    story.append(Spacer(1, 28))
    # Closing and signature (mimicking the LaTeX closing)
    story.append(Paragraph("Best regards,", closing_style))
    story.append(Paragraph(f"<b>{name}</b>", signature_style))

    doc.build(story)
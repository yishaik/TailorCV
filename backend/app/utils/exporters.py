"""
Export utilities for generating Markdown, DOCX, and PDF outputs.
"""
import io
from typing import Optional
from ..models.output import TailoredCV, CoverLetter


def generate_markdown(cv: TailoredCV, cover_letter: Optional[CoverLetter] = None) -> str:
    """
    Generate Markdown format CV.
    
    Args:
        cv: Tailored CV data
        cover_letter: Optional cover letter
    
    Returns:
        Markdown formatted string
    """
    lines = []
    
    # Header
    lines.append(f"# {cv.header.name}")
    lines.append(f"**{cv.header.title}**")
    lines.append("")
    
    # Contact info
    contact_parts = []
    if cv.header.contact.get("email"):
        contact_parts.append(cv.header.contact["email"])
    if cv.header.contact.get("phone"):
        contact_parts.append(cv.header.contact["phone"])
    if cv.header.contact.get("location"):
        contact_parts.append(cv.header.contact["location"])
    if cv.header.contact.get("linkedin"):
        contact_parts.append(f"[LinkedIn]({cv.header.contact['linkedin']})")
    
    if contact_parts:
        lines.append(" | ".join(contact_parts))
        lines.append("")
    
    # Summary
    lines.append("## Summary")
    lines.append(cv.summary)
    lines.append("")
    
    # Experience
    if cv.experience:
        lines.append("## Experience")
        lines.append("")
        for exp in cv.experience:
            location_str = f" | {exp.location}" if exp.location else ""
            lines.append(f"### {exp.title}")
            lines.append(f"**{exp.company}** | {exp.dates}{location_str}")
            lines.append("")
            for bullet in exp.bullets:
                lines.append(f"- {bullet.text}")
            lines.append("")
    
    # Skills
    if cv.skills.primary or cv.skills.secondary or cv.skills.tools:
        lines.append("## Skills")
        lines.append("")
        if cv.skills.primary:
            lines.append(f"**Core:** {', '.join(cv.skills.primary)}")
        if cv.skills.secondary:
            lines.append(f"**Additional:** {', '.join(cv.skills.secondary)}")
        if cv.skills.tools:
            lines.append(f"**Tools & Technologies:** {', '.join(cv.skills.tools)}")
        lines.append("")
    
    # Education
    if cv.education:
        lines.append("## Education")
        lines.append("")
        for edu in cv.education:
            year_str = f" ({edu.year})" if edu.year else ""
            lines.append(f"**{edu.degree} in {edu.field}**{year_str}")
            lines.append(f"{edu.institution}")
            for highlight in edu.highlights:
                lines.append(f"- {highlight}")
            lines.append("")
    
    # Certifications
    if cv.certifications:
        lines.append("## Certifications")
        lines.append("")
        for cert in cv.certifications:
            date_str = f" ({cert.date})" if cert.date else ""
            lines.append(f"- **{cert.name}** - {cert.issuer}{date_str}")
        lines.append("")
    
    # Projects
    if cv.projects:
        lines.append("## Projects")
        lines.append("")
        for proj in cv.projects:
            lines.append(f"### {proj.name}")
            lines.append(proj.description)
            if proj.technologies:
                lines.append(f"*Technologies: {', '.join(proj.technologies)}*")
            lines.append("")
    
    cv_markdown = "\n".join(lines)
    
    # Add cover letter if present
    if cover_letter:
        cl_lines = [
            "",
            "---",
            "",
            "# Cover Letter",
            "",
            cover_letter.full_text
        ]
        cv_markdown += "\n".join(cl_lines)
    
    return cv_markdown


def generate_docx(cv: TailoredCV, cover_letter: Optional[CoverLetter] = None) -> bytes:
    """
    Generate DOCX format CV.
    
    Args:
        cv: Tailored CV data
        cover_letter: Optional cover letter
    
    Returns:
        DOCX file content as bytes
    """
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    doc = Document()
    
    # Set narrow margins
    for section in doc.sections:
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
    
    # Header - Name
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_para.add_run(cv.header.name)
    name_run.bold = True
    name_run.font.size = Pt(18)
    
    # Title
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(cv.header.title)
    title_run.font.size = Pt(12)
    
    # Contact info
    contact_parts = []
    if cv.header.contact.get("email"):
        contact_parts.append(cv.header.contact["email"])
    if cv.header.contact.get("phone"):
        contact_parts.append(cv.header.contact["phone"])
    if cv.header.contact.get("location"):
        contact_parts.append(cv.header.contact["location"])
    
    if contact_parts:
        contact_para = doc.add_paragraph()
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_para.add_run(" | ".join(contact_parts))
    
    # Summary
    doc.add_heading("Summary", level=1)
    doc.add_paragraph(cv.summary)
    
    # Experience
    if cv.experience:
        doc.add_heading("Experience", level=1)
        for exp in cv.experience:
            # Company and title
            exp_para = doc.add_paragraph()
            title_run = exp_para.add_run(f"{exp.title} at {exp.company}")
            title_run.bold = True
            
            # Date and location
            date_para = doc.add_paragraph()
            date_text = exp.dates
            if exp.location:
                date_text += f" | {exp.location}"
            date_para.add_run(date_text).italic = True
            
            # Bullets
            for bullet in exp.bullets:
                bullet_para = doc.add_paragraph(bullet.text, style='List Bullet')
    
    # Skills
    if cv.skills.primary or cv.skills.secondary or cv.skills.tools:
        doc.add_heading("Skills", level=1)
        if cv.skills.primary:
            para = doc.add_paragraph()
            para.add_run("Core: ").bold = True
            para.add_run(", ".join(cv.skills.primary))
        if cv.skills.secondary:
            para = doc.add_paragraph()
            para.add_run("Additional: ").bold = True
            para.add_run(", ".join(cv.skills.secondary))
        if cv.skills.tools:
            para = doc.add_paragraph()
            para.add_run("Tools & Technologies: ").bold = True
            para.add_run(", ".join(cv.skills.tools))
    
    # Education
    if cv.education:
        doc.add_heading("Education", level=1)
        for edu in cv.education:
            edu_para = doc.add_paragraph()
            degree_text = f"{edu.degree} in {edu.field}"
            if edu.year:
                degree_text += f" ({edu.year})"
            edu_para.add_run(degree_text).bold = True
            doc.add_paragraph(edu.institution)
            for highlight in edu.highlights:
                doc.add_paragraph(highlight, style='List Bullet')
    
    # Certifications
    if cv.certifications:
        doc.add_heading("Certifications", level=1)
        for cert in cv.certifications:
            cert_text = f"{cert.name} - {cert.issuer}"
            if cert.date:
                cert_text += f" ({cert.date})"
            doc.add_paragraph(cert_text, style='List Bullet')
    
    # Projects
    if cv.projects:
        doc.add_heading("Projects", level=1)
        for proj in cv.projects:
            proj_para = doc.add_paragraph()
            proj_para.add_run(proj.name).bold = True
            doc.add_paragraph(proj.description)
            if proj.technologies:
                tech_para = doc.add_paragraph()
                tech_para.add_run("Technologies: ").italic = True
                tech_para.add_run(", ".join(proj.technologies))
    
    # Cover letter on new page
    if cover_letter:
        doc.add_page_break()
        doc.add_heading("Cover Letter", level=1)
        doc.add_paragraph(cover_letter.hook)
        doc.add_paragraph(cover_letter.value_proposition)
        doc.add_paragraph(cover_letter.fit_narrative)
        doc.add_paragraph(cover_letter.closing)
    
    # Save to bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def generate_pdf(cv: TailoredCV, cover_letter: Optional[CoverLetter] = None) -> bytes:
    """
    Generate PDF format CV using WeasyPrint.
    
    Args:
        cv: Tailored CV data
        cover_letter: Optional cover letter
    
    Returns:
        PDF file content as bytes
    """
    from weasyprint import HTML, CSS
    
    # Generate HTML content
    html_content = _generate_html(cv, cover_letter)
    
    # Convert to PDF
    html = HTML(string=html_content)
    css = CSS(string=_get_pdf_styles())
    
    return html.write_pdf(stylesheets=[css])


def _generate_html(cv: TailoredCV, cover_letter: Optional[CoverLetter] = None) -> str:
    """Generate HTML for PDF conversion."""
    
    contact_parts = []
    if cv.header.contact.get("email"):
        contact_parts.append(cv.header.contact["email"])
    if cv.header.contact.get("phone"):
        contact_parts.append(cv.header.contact["phone"])
    if cv.header.contact.get("location"):
        contact_parts.append(cv.header.contact["location"])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{cv.header.name} - CV</title>
    </head>
    <body>
        <header>
            <h1>{cv.header.name}</h1>
            <p class="title">{cv.header.title}</p>
            <p class="contact">{' | '.join(contact_parts)}</p>
        </header>
        
        <section class="summary">
            <h2>Summary</h2>
            <p>{cv.summary}</p>
        </section>
    """
    
    # Experience
    if cv.experience:
        html += "<section class='experience'><h2>Experience</h2>"
        for exp in cv.experience:
            html += f"""
            <div class="job">
                <h3>{exp.title}</h3>
                <p class="company">{exp.company} | {exp.dates}</p>
                <ul>
            """
            for bullet in exp.bullets:
                html += f"<li>{bullet.text}</li>"
            html += "</ul></div>"
        html += "</section>"
    
    # Skills
    if cv.skills.primary or cv.skills.secondary:
        html += "<section class='skills'><h2>Skills</h2>"
        if cv.skills.primary:
            html += f"<p><strong>Core:</strong> {', '.join(cv.skills.primary)}</p>"
        if cv.skills.secondary:
            html += f"<p><strong>Additional:</strong> {', '.join(cv.skills.secondary)}</p>"
        if cv.skills.tools:
            html += f"<p><strong>Tools:</strong> {', '.join(cv.skills.tools)}</p>"
        html += "</section>"
    
    # Education
    if cv.education:
        html += "<section class='education'><h2>Education</h2>"
        for edu in cv.education:
            html += f"<p><strong>{edu.degree} in {edu.field}</strong>"
            if edu.year:
                html += f" ({edu.year})"
            html += f"<br>{edu.institution}</p>"
        html += "</section>"
    
    # Certifications
    if cv.certifications:
        html += "<section class='certifications'><h2>Certifications</h2><ul>"
        for cert in cv.certifications:
            html += f"<li><strong>{cert.name}</strong> - {cert.issuer}"
            if cert.date:
                html += f" ({cert.date})"
            html += "</li>"
        html += "</ul></section>"
    
    # Cover letter
    if cover_letter:
        html += f"""
        <div class="page-break"></div>
        <section class="cover-letter">
            <h2>Cover Letter</h2>
            <p>{cover_letter.hook}</p>
            <p>{cover_letter.value_proposition}</p>
            <p>{cover_letter.fit_narrative}</p>
            <p>{cover_letter.closing}</p>
        </section>
        """
    
    html += "</body></html>"
    return html


def _get_pdf_styles() -> str:
    """Get CSS styles for PDF generation."""
    return """
    @page {
        size: A4;
        margin: 1.5cm;
    }
    
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #333;
    }
    
    header {
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 2px solid #2c3e50;
        padding-bottom: 10px;
    }
    
    h1 {
        font-size: 24pt;
        margin: 0;
        color: #2c3e50;
    }
    
    .title {
        font-size: 12pt;
        color: #7f8c8d;
        margin: 5px 0;
    }
    
    .contact {
        font-size: 9pt;
        color: #95a5a6;
    }
    
    h2 {
        font-size: 14pt;
        color: #2c3e50;
        border-bottom: 1px solid #bdc3c7;
        padding-bottom: 3px;
        margin-top: 15px;
    }
    
    h3 {
        font-size: 11pt;
        margin: 10px 0 3px 0;
    }
    
    .company {
        font-style: italic;
        color: #7f8c8d;
        margin: 0 0 5px 0;
    }
    
    ul {
        margin: 5px 0;
        padding-left: 20px;
    }
    
    li {
        margin-bottom: 3px;
    }
    
    .page-break {
        page-break-before: always;
    }
    
    .cover-letter p {
        margin-bottom: 12px;
        text-align: justify;
    }
    """

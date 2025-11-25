#!/usr/bin/env python3
"""
Convert DOCUMENTATION.md to PDF using reportlab
"""

import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

def clean_markdown(text):
    """Remove markdown formatting for simple text"""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold/italic
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    return text.strip()

def parse_markdown_to_elements(md_content, styles):
    """Parse markdown content into reportlab elements"""
    elements = []
    lines = md_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            elements.append(Spacer(1, 0.2*inch))
            i += 1
            continue
        
        # H1
        if line.startswith('# ') and not line.startswith('##'):
            text = clean_markdown(line[2:])
            elements.append(Paragraph(text, styles['Heading1']))
            elements.append(Spacer(1, 0.3*inch))
            i += 1
            continue
        
        # H2
        if line.startswith('## ') and not line.startswith('###'):
            text = clean_markdown(line[3:])
            elements.append(Paragraph(text, styles['Heading2']))
            elements.append(Spacer(1, 0.2*inch))
            i += 1
            continue
        
        # H3
        if line.startswith('### '):
            text = clean_markdown(line[4:])
            elements.append(Paragraph(text, styles['Heading3']))
            elements.append(Spacer(1, 0.15*inch))
            i += 1
            continue
        
        # H4
        if line.startswith('#### '):
            text = clean_markdown(line[5:])
            elements.append(Paragraph(text, styles['Heading4']))
            elements.append(Spacer(1, 0.1*inch))
            i += 1
            continue
        
        # Horizontal rule
        if line.startswith('---'):
            elements.append(Spacer(1, 0.3*inch))
            i += 1
            continue
        
        # Code block
        if line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if code_lines:
                code_text = '\n'.join(code_lines)
                elements.append(Preformatted(code_text, styles['Code']))
                elements.append(Spacer(1, 0.2*inch))
            i += 1
            continue
        
        # Bullet list
        if line.startswith('- ') or line.startswith('* '):
            text = clean_markdown(line[2:])
            elements.append(Paragraph(f"• {text}", styles['Normal']))
            i += 1
            continue
        
        # Numbered list
        if re.match(r'^\d+\.\s', line):
            text = clean_markdown(re.sub(r'^\d+\.\s', '', line))
            elements.append(Paragraph(f"• {text}", styles['Normal']))
            i += 1
            continue
        
        # Regular paragraph
        if line:
            text = clean_markdown(line)
            if text:
                elements.append(Paragraph(text, styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        i += 1
    
    return elements

def markdown_to_pdf(markdown_file, output_pdf):
    """Convert markdown file to PDF"""
    
    # Read markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Modify existing styles
    styles['Heading1'].fontSize = 24
    styles['Heading1'].textColor = colors.HexColor('#000000')
    styles['Heading1'].spaceAfter = 12
    styles['Heading1'].spaceBefore = 20
    
    styles['Heading2'].fontSize = 18
    styles['Heading2'].textColor = colors.HexColor('#0066cc')
    styles['Heading2'].spaceAfter = 10
    styles['Heading2'].spaceBefore = 15
    
    styles['Heading3'].fontSize = 14
    styles['Heading3'].textColor = colors.HexColor('#333333')
    styles['Heading3'].spaceAfter = 8
    styles['Heading3'].spaceBefore = 12
    
    styles['Heading4'].fontSize = 12
    styles['Heading4'].textColor = colors.HexColor('#555555')
    styles['Heading4'].spaceAfter = 6
    styles['Heading4'].spaceBefore = 10
    
    # Add Code style if it doesn't exist
    if 'Code' not in styles.byName:
        styles.add(ParagraphStyle(
            name='Code',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Courier',
            backColor=colors.HexColor('#f4f4f4'),
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10
        ))
    else:
        styles['Code'].fontSize = 9
        styles['Code'].fontName = 'Courier'
        styles['Code'].backColor = colors.HexColor('#f4f4f4')
        styles['Code'].leftIndent = 20
        styles['Code'].rightIndent = 20
        styles['Code'].spaceAfter = 10
    
    # Parse markdown and build PDF
    elements = parse_markdown_to_elements(md_content, styles)
    
    # Build PDF
    doc.build(elements)
    
    print(f"✅ PDF generated successfully: {output_pdf}")

if __name__ == "__main__":
    markdown_file = "DOCUMENTATION.md"
    output_pdf = "DOCUMENTATION.pdf"
    
    if not os.path.exists(markdown_file):
        print(f"❌ Error: {markdown_file} not found")
        exit(1)
    
    try:
        markdown_to_pdf(markdown_file, output_pdf)
    except ImportError as e:
        print("❌ Error: Required libraries not installed")
        print("Install with: pip install reportlab")
        exit(1)
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


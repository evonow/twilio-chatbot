#!/usr/bin/env python3
"""
Convert DOCUMENTATION.md to PDF
"""

import os
import markdown
from xhtml2pdf import pisa

def markdown_to_pdf(markdown_file, output_pdf):
    """Convert markdown file to PDF"""
    
    # Read markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    try:
        html_content = markdown.markdown(
            md_content,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )
    except Exception:
        # Fallback if extensions not available
        html_content = markdown.markdown(md_content)
    
    # Add CSS styling
    css_content = """
    <style>
    @page {
        size: A4;
        margin: 2cm;
    }
    
    body {
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    
    h1 {
        font-size: 24pt;
        color: #000;
        border-bottom: 3px solid #0066cc;
        padding-bottom: 10px;
        margin-top: 30px;
        page-break-after: avoid;
    }
    
    h2 {
        font-size: 18pt;
        color: #0066cc;
        border-bottom: 2px solid #e0e0e0;
        padding-bottom: 8px;
        margin-top: 25px;
        page-break-after: avoid;
    }
    
    h3 {
        font-size: 14pt;
        color: #333;
        margin-top: 20px;
        page-break-after: avoid;
    }
    
    h4 {
        font-size: 12pt;
        color: #555;
        margin-top: 15px;
        page-break-after: avoid;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    
    pre {
        background-color: #f4f4f4;
        padding: 15px;
        border-left: 4px solid #0066cc;
        page-break-inside: avoid;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 15px 0;
        page-break-inside: avoid;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    
    th {
        background-color: #0066cc;
        color: white;
        font-weight: bold;
    }
    
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    blockquote {
        border-left: 4px solid #0066cc;
        margin: 15px 0;
        padding-left: 15px;
        color: #666;
        font-style: italic;
    }
    
    a {
        color: #0066cc;
        text-decoration: none;
    }
    
    ul, ol {
        margin: 10px 0;
        padding-left: 30px;
    }
    
    li {
        margin: 5px 0;
    }
    
    hr {
        border: none;
        border-top: 2px solid #e0e0e0;
        margin: 30px 0;
    }
    
    p {
        margin: 10px 0;
    }
    </style>
    """
    
    # Wrap HTML content
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Ask GroupFund - Complete Documentation</title>
        {css_content}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert to PDF
    with open(output_pdf, 'w+b') as pdf_file:
        pisa_status = pisa.CreatePDF(
            full_html,
            dest=pdf_file,
            encoding='utf-8'
        )
    
    if pisa_status.err:
        raise Exception(f"Error generating PDF: {pisa_status.err}")
    
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
        print("Install with: pip install markdown weasyprint")
        exit(1)
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


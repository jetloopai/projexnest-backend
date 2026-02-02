from weasyprint import HTML, CSS
from typing import Dict, Any
import json

def render_proposal_html(proposal: Dict[str, Any], content_json: Dict[str, Any]) -> str:
    """
    Renders a proposal's content_json into an HTML string suitable for PDF conversion.
    """
    title = proposal.get("title", "Proposal")
    
    # Extract sections from content_json
    sections = content_json.get("sections", [])
    scope = content_json.get("scope", "")
    pricing = content_json.get("pricing", [])
    terms = content_json.get("terms", "")
    
    # Build sections HTML
    sections_html = ""
    for section in sections:
        sections_html += f"""
        <div class="section">
            <h2>{section.get('title', 'Section')}</h2>
            <p>{section.get('content', '')}</p>
        </div>
        """
    
    # Build pricing table
    pricing_html = ""
    if pricing:
        pricing_html = """
        <div class="section">
            <h2>Pricing</h2>
            <table>
                <thead>
                    <tr><th>Item</th><th>Description</th><th>Amount</th></tr>
                </thead>
                <tbody>
        """
        total = 0
        for item in pricing:
            amount = item.get('amount', 0)
            total += amount
            pricing_html += f"""
                <tr>
                    <td>{item.get('name', '')}</td>
                    <td>{item.get('description', '')}</td>
                    <td>${amount:,.2f}</td>
                </tr>
            """
        pricing_html += f"""
                </tbody>
                <tfoot>
                    <tr><td colspan="2"><strong>Total</strong></td><td><strong>${total:,.2f}</strong></td></tr>
                </tfoot>
            </table>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                margin: 40px;
                color: #333;
                line-height: 1.6;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #2563eb;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2563eb;
                margin-bottom: 5px;
            }}
            .section {{
                margin-bottom: 25px;
            }}
            .section h2 {{
                color: #1e40af;
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 5px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #e5e7eb;
                text-align: left;
            }}
            th {{
                background-color: #f3f4f6;
            }}
            tfoot td {{
                font-weight: bold;
                background-color: #f9fafb;
            }}
            .terms {{
                font-size: 0.9em;
                color: #6b7280;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
            }}
            .signature-block {{
                margin-top: 50px;
                padding: 20px;
                border: 1px dashed #9ca3af;
            }}
            .signature-line {{
                margin-top: 40px;
                border-top: 1px solid #333;
                width: 300px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
            <p>Professional Proposal</p>
        </div>
        
        {sections_html}
        
        {f'<div class="section"><h2>Scope of Work</h2><p>{scope}</p></div>' if scope else ''}
        
        {pricing_html}
        
        {f'<div class="terms"><h3>Terms & Conditions</h3><p>{terms}</p></div>' if terms else ''}
        
        <div class="signature-block">
            <p><strong>Acceptance</strong></p>
            <p>By signing below, you agree to the terms outlined in this proposal.</p>
            <div class="signature-line"></div>
            <p>Signature & Date</p>
        </div>
    </body>
    </html>
    """
    return html

def generate_pdf_from_html(html_content: str) -> bytes:
    """
    Generates a PDF from HTML content using WeasyPrint.
    Returns the PDF as bytes.
    """
    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf()
    return pdf_bytes

def generate_proposal_pdf(proposal: Dict[str, Any], content_json: Dict[str, Any]) -> bytes:
    """
    High-level function: Takes a proposal and its content, returns PDF bytes.
    """
    html = render_proposal_html(proposal, content_json)
    return generate_pdf_from_html(html)

def upload_pdf_to_storage(client, bucket_name: str, path: str, pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Uploads bytes to Supabase Storage.
    """
    try:
        resp = client.storage.from_(bucket_name).upload(
            file=pdf_bytes,
            path=path,
            file_options={"content-type": "application/pdf"}
        )
        return resp
    except Exception as e:
        print(f"Error uploading PDF: {e}")
        return None

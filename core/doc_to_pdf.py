import os
import random, markdown
import pypandoc
from weasyprint import HTML, CSS
import os, random, docx
import subprocess
import os
from docx import Document as DocxDocument

def save_doc_to_pdf(file_path: str) -> str:
    """
    Chuyển file .txt, .md, .docx thành PDF.
    Giữ vị trí bảng đúng thứ tự với paragraph.
    """
    base_dir = os.path.join(os.getcwd(), "files_database")
    os.makedirs(base_dir, exist_ok=True)

    rand_id = random.randint(100000, 999999)
    name_only = os.path.splitext(os.path.basename(file_path))[0]
    pdf_path = os.path.join(base_dir, f"{name_only}.pdf")

    ext = os.path.splitext(file_path)[1].lower()
    html_parts = []

    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            html_parts.append(markdown.markdown(content, extensions=['tables']))
    elif ext == ".docx":
        doc = DocxDocument(file_path)

        # Lặp theo thứ tự các block: paragraph hoặc table
        for block in doc.element.body:
            if block.tag.endswith('p'):
                para = docx.text.paragraph.Paragraph(block, doc)
                text = para.text.strip()
                if text:
                    html_parts.append(f"<p>{text}</p>")
            elif block.tag.endswith('tbl'):
                table = docx.table.Table(block, doc)
                table_html = '<table style="page-break-inside: avoid;">'
                for row in table.rows:
                    table_html += "<tr>"
                    for cell in row.cells:
                        table_html += f"<td>{cell.text}</td>"
                    table_html += "</tr>"
                table_html += "</table>"
                html_parts.append(table_html)
    else:
        raise ValueError("Chỉ hỗ trợ .txt, .md, .docx")

    html_content = "\n".join(html_parts)

    css = CSS(string='''
        @page { size: A4; margin: 2cm; }
        body { font-family: Arial, sans-serif; font-size: 10pt; line-height: 1.5; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; page-break-inside: avoid; }
        th, td { border: 1px solid #333; padding: 5px; text-align: left; }
        th { background-color: #f0f0f0; }
    ''')

    HTML(string=html_content).write_pdf(pdf_path, stylesheets=[css])
    print(f"✅ PDF đã được lưu tại: {pdf_path}")

    return pdf_path

def convert_doc_to_docx(input_path):
    output_dir = os.path.dirname(input_path)

    subprocess.run([
        "soffice",
        "--headless",
        "--convert-to", "docx",
        "--outdir", output_dir,
        input_path
    ], check=True)

    base, ext = os.path.splitext(input_path)
    return base + ".docx"
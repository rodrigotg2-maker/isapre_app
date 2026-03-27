import requests
from io import BytesIO
from pypdf import PdfReader, PdfWriter


def download_plan_pdf(codigo: str) -> bytes:
    url = f"https://pdfplan.cl/viewplan/{codigo}.pdf"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Validación básica
    if len(response.content) < 1000:
        raise ValueError(f"PDF no disponible para código {codigo}")

    return response.content


def merge_pdfs(pdf_bytes_list: list[bytes]) -> bytes:
    writer = PdfWriter()

    for pdf_bytes in pdf_bytes_list:
        reader = PdfReader(BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()
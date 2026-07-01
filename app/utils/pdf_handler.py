from io import BytesIO
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas


async def add_cnpj(pdf_bytes: bytes, cnpj: str) -> bytes:
    # pra quando o cnd n tem o cnpj completo
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        # medidas do pdf
        w, h = float(page.mediabox.width), float(page.mediabox.height)

        # buffer temporario
        overlay = BytesIO()

        # criar canvas para o texto
        c = canvas.Canvas(overlay, pagesize=(w, h))

        # escrevo no canvas e salvo
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 1)
        c.drawString(
            0,
            h - 1,
            f"SOLICITO PARA O AGENTE UTILIZAR ESTE CNPJ {cnpj}",
        )
        c.save()

        # como overlay e um buffer tem que voltar pro inicio pra ler tudo
        overlay.seek(0)

        # jogo o overlay por cima da pagina original
        page.merge_page(PdfReader(overlay).pages[0])

        # adiciono a pagina modificada ao writer
        writer.add_page(page)

    out = BytesIO()
    writer.write(out)
    return out.getvalue()

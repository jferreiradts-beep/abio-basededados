from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO

def gerar_grade(largura, altura, passo = 20):
    buffer = BytesIO()
    can = canvas.Canvas(buffer, pagesize=(largura, altura))

    for y in range(0, int(altura), passo):
        can.setFont('Times-Roman', 12)
        can.drawString(2, y + 2, str(y))
        can.line(0, y, largura, y)

    for x in range(0, int(largura), passo):
        can.setFont('Times-Roman', 12)
        can.drawString(x + 2, 2, str(x))
        can.line(x, 0, x, altura)

    can.save()
    buffer.seek(0)
    return buffer

def sobrepor_grade(layout_pdf, saida="layout_com_grade.pdf", passo=20):
    base = PdfReader(layout_pdf)
    page = base.pages[0]

    largura = float(page.mediabox.width)
    altura = float(page.mediabox.height)

    # gerar grade
    grade_pdf = PdfReader(gerar_grade(largura, altura, passo))

    writer = PdfWriter()
    page.merge_page(grade_pdf.pages[0])
    writer.add_page(page)

    with open(saida, "wb") as f:
        writer.write(f)

    print("Grade criada:", saida)


sobrepor_grade("mapa/certificado_capa.pdf", "Outros/certificado_capa_com_grade.pdf")

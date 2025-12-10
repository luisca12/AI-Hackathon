# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas

# # Create a new PDF with ReportLab
# file_name = "example.pdf"
# c = canvas.Canvas(file_name, pagesize=letter)
# c.drawString(100, 750, "Hello, this is a PDF generated with ReportLab!")
# c.save()

from fpdf import FPDF
from datetime import datetime

def createPDF(deviceIP, interfaces=""):
    dateHour = datetime.now()
    dateHourOut = dateHour.strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 12, "Error Disabled Interfaces", ln=True, align='C')

    # Imagen
    pdf.image("Caremore.png", x=10, y=12, w=34) # descomenta si tienes una imagen
    pdf.image("Kyndryl.png", x=165, y=12, w=34)

    pdf.ln(6)

    # Subtítulo
    pdf.set_font("Arial", '', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Results from {dateHourOut}", ln=True)

    # Línea separadora
    pdf.set_draw_color(0, 102, 204)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.ln(5)

    # Tabla
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(60, 10, "Device", border=1, fill=True)
    pdf.cell(60, 10, "Interface", border=1, ln=True, fill=True)

    
    pdf.set_font("Arial", '', 12)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(60, 10, f"{deviceIP}", border=1, fill=True)
    pdf.cell(60, 10, f"{', '.join(interfaces)}", border=1, ln=True, fill=True)

    # pdf.cell(60, 10, "Value 3", border=1, fill=True)
    # pdf.cell(60, 10, "Value 4", border=1, ln=True, fill=True)
    # pdf.cell(60, 10, "Value 5", border=1, fill=True)
    # pdf.cell(60, 10, "Value 6", border=1, ln=True, fill=True)

    pdf.ln(10)

    pdf.output("Error Disable Interfaces Report.pdf")
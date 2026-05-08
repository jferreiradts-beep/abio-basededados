from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
styles = getSampleStyleSheet()
try:
    p = Paragraph("", styles['Normal'])
    print("Empty paragraph works")
except Exception as e:
    print(f"Error with empty paragraph: {e}")

try:
    p = Paragraph(None, styles['Normal'])
    print("None paragraph works")
except Exception as e:
    print(f"Error with None paragraph: {e}")

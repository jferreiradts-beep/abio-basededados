from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
styles = getSampleStyleSheet()
try:
    p = Paragraph(123, styles['Normal'])
    print("Int paragraph works")
except Exception as e:
    print(f"Error with int paragraph: {e}")

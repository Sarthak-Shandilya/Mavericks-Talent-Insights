"""PDF report generation (BRD §7.9)."""
from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def table_to_pdf(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(inch, y, title)
    y -= 0.4 * inch
    c.setFont("Helvetica", 9)
    c.drawString(inch, y, " | ".join(headers))
    y -= 0.25 * inch
    for row in rows:
        if y < inch:
            c.showPage()
            y = height - inch
            c.setFont("Helvetica", 9)
        line = " | ".join(str(cell) for cell in row)
        if len(line) > 120:
            line = line[:117] + "..."
        c.drawString(inch, y, line)
        y -= 0.2 * inch
    c.save()
    buffer.seek(0)
    return buffer.read()

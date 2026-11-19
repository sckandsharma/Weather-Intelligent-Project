"""
Custom two-pass canvas for dynamic total page counting and running headers/footers.
"""
from reportlab.pdfgen import canvas
from reportlab.lib import colors

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, total_pages):
        # Page 1 is the cover page; skip running headers and footers
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header
        self.drawString(36, 756, "Weather Intelligence & Advisory Assistant — Technical Interview Study Guide")
        self.drawRightString(576, 756, "Core Architecture & Implementation")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(36, 750, 576, 750)

        # Running Footer
        self.line(36, 42, 576, 42)
        self.drawString(36, 30, "Confidential | Prepared for Technical Interview Evaluation")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(576, 30, page_str)

        self.restoreState()

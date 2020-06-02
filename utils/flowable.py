from reportlab.lib.colors import white, black
from reportlab.pdfbase.acroform import AcroForm
from reportlab.platypus import Flowable


class InteractiveTextField(Flowable):
    def __init__(self, width=470):
        Flowable.__init__(self)
        self.width = width

    def draw(self):
        self.canv.saveState()
        form: AcroForm = self.canv.acroForm
        form.textfieldRelative(tooltip='Комментарий', fontName='Times-Bold',
                               fontSize=12, borderStyle='underlined', borderColor=white,
                               height=18, width=self.width,
                               fillColor=white, textColor=black, forceBorder=False)
        self.canv.restoreState()

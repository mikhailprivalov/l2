from reportlab.lib.colors import white, black
from reportlab.pdfbase.acroform import AcroForm
from reportlab.platypus import Flowable
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from laboratory.settings import FONTS_FOLDER

pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

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


class InteractiveTextFieldAmbulatoryCard(Flowable):
    def __init__(self, width=140 * mm):
        Flowable.__init__(self)
        self.width = width

    def draw(self):
        self.canv.saveState()
        self.canv.setFont("PTAstraSerifBold", 14)
        form: AcroForm = self.canv.acroForm
        form.textfieldRelative(tooltip='Комментарий', fontName='Times-Bold',
                               fontSize=10, borderStyle='underlined', borderColor=white,
                               height=5 * mm, width=self.width,
                               fillColor=white, textColor=black, forceBorder=False)
        self.canv.restoreState()

class InteractiveListBoxField(Flowable):
    def __init__(self):
        Flowable.__init__(self)

    def draw(self):
        self.canv.saveState()
        form: AcroForm = self.canv.acroForm
        options = [' ',
                   'Вид медосмотра: периодический',
                   'Вид медосмотра: первичный',
                   'Вид медосмотра: водительская справка',
                   'Вид медосмотра: периодический',
                   'Вид медосмотра: первичный',
                   'Вид медосмотра: водительская справка'
                   ]
        form.choice(name='choice2', tooltip='Field choice2',
                    value=' ', height= 7 * mm, width=178 * mm,
                    options=options, borderColor=black, fillColor=white,
                    borderStyle='solid', borderWidth=1, relative=True, forceBorder=False, dashLen=1)

        self.canv.restoreState()

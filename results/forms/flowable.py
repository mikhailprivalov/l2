from reportlab import rl_config
from reportlab.lib.colors import white, black
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.acroform import AcroForm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Table, Paragraph, Frame, KeepInFrame

from laboratory.settings import FONTS_FOLDER
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os.path


class FrameData(Flowable):
    def __init__(self, x=0, y=0, width=0, height=0, text="", style="", tbl=None):
        Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.style = style
        self.tbl = tbl

    def draw(self):
        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 10
        style.alignment = TA_JUSTIFY
        self.canv.saveState()
        near_diagnos_text = [Paragraph(f'{self.text}', self.style)]
        if self.tbl:
            near_diagnos_text = [self.tbl]
        near_diagnos_frame = Frame(self.x * mm, self.y, self.width * mm, self.height * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        near_diagnos_inframe = KeepInFrame(
            self.width * mm,
            self.height * mm,
            near_diagnos_text,
            vAlign='TOP',
            fakeWidth=False,
        )
        near_diagnos_frame.addFromList([near_diagnos_inframe], self.canv)
        self.canv.restoreState()


class FrameDataStamp(Flowable):
    def __init__(self, x=0, y=0, width=0, height=0, text="", style="", tbl=None):
        Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.style = style
        self.tbl = tbl


    def draw(self):
        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 10
        style.alignment = TA_JUSTIFY
        # self.canv.saveState()
        near_diagnos_text = [self.tbl]
        near_diagnos_frame = Frame(0 * mm, -70 * mm, 175 * mm, 20 * mm, leftPadding=2, bottomPadding=2, rightPadding=2, topPadding=2, showBoundary=1)
        near_diagnos_inframe = KeepInFrame(
            175 * mm,
            20 * mm,
            near_diagnos_text,
            vAlign='TOP',
        )
        near_diagnos_frame.addFromList([near_diagnos_inframe], self.canv)
        # self.canv.restoreState()

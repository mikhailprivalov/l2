from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Paragraph, Frame, KeepInFrame

from laboratory.settings import FONTS_FOLDER
from reportlab.lib.enums import TA_JUSTIFY
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
        data_text = [Paragraph(f'{self.text}', self.style)]
        if self.tbl:
            data_text = [self.tbl]
        data_frame = Frame(self.x * mm, self.y, self.width * mm, self.height * mm, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
        data_inframe = KeepInFrame(
            self.width * mm,
            self.height * mm,
            data_text,
            vAlign='TOP',
            fakeWidth=False,
        )
        data_frame.addFromList([data_inframe], self.canv)
        self.canv.restoreState()


class FrameDataUniversal(Flowable):
    def __init__(self, x=0, y=0, width=0, height=0, text=None):
        Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self):
        self.canv.saveState()
        data_text = None
        if self.text:
            data_text = self.text
        if data_text:
            data_frame = Frame(self.x, self.y, self.width, self.height, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=0)
            data_inframe = KeepInFrame(
                self.width,
                self.height,
                data_text,
                vAlign='TOP',
                fakeWidth=False,
            )
            data_frame.addFromList([data_inframe], self.canv)
        self.canv.restoreState()


class FrameDataCol(Flowable):
    def __init__(self, params_columns=None):
        Flowable.__init__(self)
        self.params_columns = params_columns

    def draw(self):
        self.canv.saveState()
        for params in self.params_columns:
            current_data_frame = Frame(
                params["x"], params["y"], params["width"], params["height"], leftPadding=params.get('left_padding', 0),
                bottomPadding=params.get('bottom_padding', 0), rightPadding=params.get("right_padding", 0),
                topPadding=params.get("top_padding", 0), showBoundary=params.get("showBoundary", 0)
            )
            data_inframe = KeepInFrame(params["width"], params["height"], params["text"], vAlign='TOP', fakeWidth=False)
            current_data_frame.addFromList([data_inframe], self.canv)
        self.canv.restoreState()

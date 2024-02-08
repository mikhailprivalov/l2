from reportlab import rl_config
from reportlab.lib.colors import white, black
from reportlab.lib.units import mm
from reportlab.pdfbase.acroform import AcroForm
from reportlab.platypus import Flowable, Table
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing


class InteractiveTextField(Flowable):
    def __init__(self, width=470, fontsize=12, height=18):
        Flowable.__init__(self)
        self.width = width
        self.fontSize = fontsize
        self.height = height

    def draw(self):
        self.canv.saveState()
        form: AcroForm = self.canv.acroForm
        form.textfieldRelative(
            tooltip='Комментарий',
            fontName='Times-Bold',
            fontSize=12,
            borderStyle='underlined',
            borderColor=white,
            height=18,
            width=self.width,
            fillColor=white,
            textColor=black,
            forceBorder=False,
        )
        self.canv.restoreState()


class InteractiveListBoxField(Flowable):
    def __init__(self):
        Flowable.__init__(self)

    def draw(self):
        self.canv.saveState()
        form: AcroForm = self.canv.acroForm
        options = [
            ' ',
            "Предварительный",
            "Периодический",
            "№003-В/У(водительская справка)",
            "№ 002-О/У (оружие)",
            "Форма №733",
            "Форма №500",
            "Справка 001-ГС",
            "Справка 086-1/У",
            "Справка 086/У",
            "Сан.книжка",
            "Форма 989-Н",
            "Бюджет",
            "Диспансеризация",
            "Консультативный прием",
            "Платно",
            "Росгосстрах",
            "Согаз",
        ]
        form.choice(
            name='choice1',
            tooltip='choice1',
            value=' ',
            height=7 * mm,
            width=178 * mm,
            options=options,
            borderColor=black,
            fillColor=white,
            fieldFlags='edit',
            borderStyle='solid',
            borderWidth=1,
            relative=True,
            forceBorder=False,
            dashLen=1,
        )

        self.canv.restoreState()


class InteractiveListTypeMedExam(Flowable):
    def __init__(self):
        Flowable.__init__(self)

    def draw(self):
        self.canv.saveState()
        form: AcroForm = self.canv.acroForm
        options = [
            ' ',
            "Платно",
            "Профосмотр",
        ]
        form.choice(
            name='choice2',
            tooltip='choice2',
            value=' ',
            height=7 * mm,
            width=178 * mm,
            options=options,
            borderColor=black,
            fillColor=white,
            fieldFlags='edit',
            borderStyle='solid',
            borderWidth=1,
            relative=True,
            forceBorder=False,
            dashLen=1,
        )

        self.canv.restoreState()


class LaterPagesTable(Table):
    def __init__(self, data, laterColWidths=None, laterStyle=None, **kwargs):
        Table.__init__(self, data, **kwargs)

        self._later_column_widths = laterColWidths
        self._later_style = laterStyle

    def split(self, availWidth, availHeight):
        self._calc(availWidth, availHeight)
        if self.splitByRow:
            if not getattr(rl_config, 'allowTableBoundsErrors') and self._width > availWidth:
                return []
            tables = self._splitRows(availHeight)

            if len(tables):
                self.onLaterPages(tables[1])
            return tables
        else:
            raise NotImplementedError

    def onLaterPages(self, T):
        if self._later_column_widths:
            T._argW = self._later_column_widths

        if self._later_style:
            T.setStyle(self._later_style)


class QrCodeSite(Flowable):
    def __init__(self, qr_value, params):
        # init and store rendering value
        Flowable.__init__(self)
        self.qr_value = qr_value
        self.x_offset = params.get("x", 0) * mm
        self.y_offset = params.get("y", 0) * mm
        self.size = params.get("size", 0) * mm

    def draw(self):
        qr_code = qr.QrCodeWidget(self.qr_value)
        qr_code.barWidth = self.size
        qr_code.barHeight = self.size
        qr_code.qrVersion = 1
        d = Drawing()
        d.add(qr_code)
        renderPDF.draw(d, self.canv, self.x_offset, self.y_offset)

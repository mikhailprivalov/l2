from reportlab.lib.colors import white, black
from reportlab.pdfbase.acroform import AcroForm
from reportlab.platypus import Flowable
from reportlab.lib.units import mm


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
            "Профомотр",
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

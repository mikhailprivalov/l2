import os.path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from laboratory.settings import FONTS_FOLDER, SELF_WATERMARKS


class PageNumCanvas(canvas.Canvas):
    """
    Adding a Page Number of Total
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """
        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        if not SELF_WATERMARKS:
            pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
            page = "Лист {} из {}".format(self._pageNumber, page_count)
            self.setFont("PTAstraSerifReg", 9)
            self.drawRightString(200 * mm, 8 * mm, page)


class Colontitul(canvas.Canvas):
    """
    Adding a Page Number of Total
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """
        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        if not SELF_WATERMARKS:
            pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
            self.setFont("PTAstraSerifReg", 8)
            page = "Данное заключение не является окончательным диагнозом и должно быть интерпретировано лечащим врачом в совокупности с клинико-"
            self.drawString(20 * mm, 13 * mm, page)

            page = "лабораторными данными (Согласно федеральному закону №323-ФЗ от 21.11.2011 «Об основах охраны здоровья граждан в Российской Федерации»)."
            self.drawString(20 * mm, 10 * mm, page)

            page = "Выданные заключения, предыдущие исследования на электронных носителях необходимо сохранять и предоставлять при повторных обследованиях "
            self.drawString(20 * mm, 7 * mm, page)

            page = "врачу-рентгенологу и непосредственно лечащему врачу для оценки динамики. Результаты исследования хранятся в электронном архиве PACS."
            self.drawString(20 * mm, 4 * mm, page)

            # page = "Не пренебрегайте консультацией специалиста и не ограничивайтесь диагностическими исследованиями. Будьте здоровы."
            # self.drawString(20 * mm, 6 * mm, page)


class PageNumCanvasPartitionAll(canvas.Canvas):
    """
    Adding a Page Number of Total
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        if not SELF_WATERMARKS:
            pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
            page = "Лист {}".format(self._pageNumber)
            self.setFont("PTAstraSerifReg", 9)
            self.drawRightString(200 * mm, 8 * mm, page)

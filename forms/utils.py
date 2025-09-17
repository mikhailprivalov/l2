import os
from copy import deepcopy
from typing import List, Dict, Union

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfbase.ttfonts import TTFont

from laboratory.settings import FONTS_FOLDER

base_style_sheet = getSampleStyleSheet()
BASE_STYLE = base_style_sheet["Normal"]
BASE_STYLE.fontName = "PTAstraSerifReg"
BASE_STYLE.fontSize = 12
BASE_STYLE.alignment = TA_LEFT
Number = Union[int, float]


def register_fonts(fonts: List[Dict[str, str]] = None) -> None:
    """
    Регистрация шрифтов, по умолчанию регистрируются PTAstraSerif
    """
    if fonts:
        for font in fonts:
            pdfmetrics.registerFont(TTFont(font.get("name"), os.path.join(FONTS_FOLDER, font.get("filename"))))
    else:
        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    return None


def create_style(base: any = BASE_STYLE, font_name: str = None, font_size: Number = None, leading: Number = None, space_after: Number = None, alignment: str = None):
    """
    Создание копии базового стиля с необходимыми параметрами, alignment - ["left", "center", "right", "justify"]
    """
    alignments = {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT, "justify": TA_JUSTIFY}
    style = deepcopy(base)
    if font_name:
        style.fontName = font_name
    if font_size:
        style.fontSize = font_size
    if leading:
        style.leading = leading
    if space_after:
        style.spaceAfter = space_after
    if alignment:
        style.alignment = alignments.get(alignment)
    return style

import os
from typing import List, Dict

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from laboratory.settings import FONTS_FOLDER


def register_fonts(fonts: List[Dict[str, str]] = None) -> None:
    if fonts:
        for font in fonts:
            pdfmetrics.registerFont(TTFont(font.get("name"), os.path.join(FONTS_FOLDER, font.get("filename"))))
    else:
        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))
    return None

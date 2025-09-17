import calendar
import datetime
from io import BytesIO

import pytils
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph

from forms.utils import register_fonts, create_style
from hospitals.models import Hospitals


def form_01(request_data):
    """
    Создание печатной формы графика рабочего времени
    """
    register_fonts()
    style = create_style(font_size=10, alignment="justify")
    # TODO Изменить названия стилей на более правильные
    style_center = create_style(style, alignment="center")
    style_center_bold = create_style(style_center, "PTAstraSerifBold")
    style_center_title = create_style(style_center, font_size=7)
    style_center_sup = create_style(style_center, font_size=5)
    style_center_data = create_style(style_center, font_size=8)
    style_center_data_bold = create_style(style_center_bold)  # TODO Заменить его в коде на style_center_bold
    style_center_data_title = create_style(style_center_title)  # TODO Заменить его в коде на style_center_title
    style_left = create_style(font_size=6)
    style_right = create_style(style_left, alignment="right")
    style_right_bold = create_style(style_right, "PTAstraSerifBold")

    objs = [] # TODO Изменить на document_data
    department_table_number = 27
    month_name = pytils.dt.ru_strftime(u"%B", inflected=True, date=datetime.datetime.now()) # TODO месяц надо получать из документа который приходит в запросе
    current_year = datetime.date.today().year # TODO год из документа
    current_month = datetime.date.today().month # TODO месяц из документа
    first_day_month = 1
    last_day_month = calendar.monthrange(current_year, current_month)[1]
    tabel_type = 'первичный'  # TODO Этого нет в графике
    department_name = 'Кабинет неотложной травматологии и ортопедии (травмпункт)' # TODO это из документа
    date_now = datetime.datetime.now().strftime('%d.%m.%Y') # TODO не актуально
    main_doctor = 'Новожилов В.А.'  # TODO динамически
    head_department = 'Преториус Т.Л.'  # TODO Из документа
    old_sestra = 'Тотьямина Д.С.'  # TODO из документа
    hr_specialist = 'Краснова С.А.'  # TODO не акутально
    hospital: Hospitals = request_data.get("hospital")  # TODO заменить на organization
    hospital_name = hospital.safe_short_title
    objs.append(Paragraph('Привет', style))

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=10 * mm, leftMargin=5 * mm, topMargin=56 * mm, bottomMargin=43 * mm, title="График рабочего времени")
    document.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

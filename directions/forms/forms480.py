import os
from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import eanbc
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from appconf.manager import SettingManager
from directions.models import Napravleniya, Issledovaniya, DirectionParamsResult
from reportlab.platypus import Table, TableStyle, Paragraph, Frame, KeepInFrame, Spacer
from reportlab.pdfgen.canvas import Canvas
from laboratory.settings import FONTS_FOLDER
from laboratory.utils import strdate
import sys
import locale
from forms.forms_func import hosp_get_operation_data
from results.prepare_data import table_part_result, previous_laboratory_result, previous_doc_refferal_result
from utils.dates import normalize_dash_date
import simplejson as json


def form_01(c: Canvas, dir: Napravleniya):
    # Гистология - Учетная форма № 014/у Утверждена приказом Минздрава России от 24 марта 2016 г. № 179н
    def printForm():
        hospital_name = dir.hospital_short_title
        hospital_address = SettingManager.get("org_address")
        hospital_kod_ogrn = SettingManager.get("org_ogrn")

        if sys.platform == 'win32':
            locale.setlocale(locale.LC_ALL, 'rus_rus')
        else:
            locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

        pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
        pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

        styleSheet = getSampleStyleSheet()
        style = styleSheet["Normal"]
        style.fontName = "PTAstraSerifReg"
        style.fontSize = 10.5
        style.leading = 14
        style.spaceAfter = 1 * mm

        styleCenterBold = deepcopy(style)
        styleCenterBold.alignment = TA_CENTER
        styleCenterBold.fontSize = 12
        styleCenterBold.leading = 15
        styleCenterBold.fontName = 'PTAstraSerifBold'

        styleT = deepcopy(style)
        styleT.alignment = TA_LEFT
        styleT.fontSize = 10
        styleT.leading = 4.5 * mm
        styleT.face = 'PTAstraSerifReg'

        barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0, barHeight=8 * mm, barWidth=1.25)
        dir_code = Drawing()
        dir_code.add(barcode)
        renderPDF.draw(dir_code, c, 157 * mm, 259 * mm)

        objs = []
        if dir.hospital:
            source_hospital = dir.hospital
            hospital_name = source_hospital.safe_short_title
            hospital_address = source_hospital.safe_address
            hospital_kod_ogrn = source_hospital.safe_ogrn
        opinion = [
            [
                Paragraph(f'<font size=11>{hospital_name}<br/>Адрес: {hospital_address}<br/>ОГРН: {hospital_kod_ogrn} <br/> </font>', styleT),
                Paragraph('<font size=9 >Код формы по ОКУД:<br/>Код организации по ОКПО: <br/>' 'Медицинская документация<br/>Учетная форма № 014/у</font>', styleT),
            ],
        ]

        tbl = Table(opinion, 2 * [100 * mm])
        tbl.setStyle(
            TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 0.75, colors.white),
                    ('LEFTPADDING', (1, 0), (-1, -1), 55 * mm),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]
            )
        )

        objs.append(tbl)
        objs.append(Spacer(1, 5 * mm))
        history_num = ''
        try:
            issledovaniye = Issledovaniya.objects.get(napravleniye=dir.pk)
        except ObjectDoesNotExist:
            issledovaniye = None
        short_title = issledovaniye.research.short_title
        if dir.parent and dir.parent.research.is_hospital:
            history_num = f"(cтационар-{str(dir.parent.napravleniye_id)})"
        objs.append(Paragraph(f'НАПРАВЛЕНИЕ № {dir.pk} {history_num} ', styleCenterBold))
        objs.append(Paragraph('НА ПРИЖИЗНЕННОЕ ПАТОЛОГО-АНАТОМИЧЕСКОЕ<br/> ИССЛЕДОВАНИЕ БИОПСИЙНОГО (ОПЕРАЦИОННОГО) МАТЕРИАЛА', styleCenterBold))
        objs.append(Paragraph(f'{short_title.upper()}', styleCenterBold))
        objs.append(Spacer(1, 10 * mm))
        space_symbol = '&nbsp;'

        direction_params = DirectionParamsResult.objects.filter(napravleniye=dir)
        descriptive_values = []
        patient_locality = ""
        laboratory_value, purpose, table_value, main_diagnos, mkb10_code, clinical_data, method_get_material, doc_get_material, previous_result = (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
        date_get_material = '_________________________'
        time_get_material = '______________'
        is_aqua_material = '(да/нет)___________'
        purpose = 'Уточнение диагноза'
        department = ""

        for param in direction_params:
            if param.field_type == 24:
                laboratory_value = param.value
            elif param.field_type == 27:
                table_value = param.value
            elif param.field_type in [26, 25]:
                descriptive_values.append(param.value)
            elif param.title == 'Цель':
                purpose = param.value
            elif param.title == 'Диагноз основной':
                main_diagnos = param.value
            elif param.title == 'результаты предыдущие':
                previous_result = param.value
            elif param.title.strip() == 'Код по МКБ':
                try:
                    value = json.loads(param.value)
                    mkb10_code = value["code"]
                except:
                    mkb10_code = param.value
            elif param.title == 'Дополнительные клинические сведения':
                clinical_data = param.value
            elif param.title == 'Способ получения биопсийного (операционного) материала':
                method_get_material = param.value
            elif param.title == 'Материал помещен в 10%-ный раствор нейтрального формалина':
                is_aqua_material = param.value
            elif param.title == 'Дата забора материала':
                date_get_material = normalize_dash_date(param.value)
            elif param.title == 'Время забора материала':
                time_get_material = param.value
            elif param.title == 'ФИО врача':
                doc_get_material = param.value
            elif param.title == 'Вид места жительства':
                try:
                    value = json.loads(param.value)
                    patient_locality = f'{value.get("title", "")} -{value.get("code", "")}'
                except:
                    patient_locality = "Городская -1, Сельская -2"
            elif param.title == 'Отделение':
                department = param.value
        if not dir.is_external:
            department = dir.get_doc_podrazdeleniye_title()

        objs.append(Paragraph(f'1. Отделение, направившее биопсийный (операционный) материал: {department}', style))
        objs.append(Paragraph(f'2. Фамилия, имя, отчество (при наличии) пациента: {dir.client.individual.fio()}', style))
        sex = dir.client.individual.sex
        if sex == "м":
            sex = f'{sex}-1'
        else:
            sex = f'{sex}-2'
        objs.append(Paragraph(f'3. Пол: {sex}, {space_symbol * 5}   4. Дата рождения: число: {dir.client.individual.bd()}', style))
        polis_num = ''
        polis_issue = ''
        snils = ''
        ind_data = dir.client.get_data_individual()
        if ind_data['oms']['polis_num']:
            polis_num = ind_data['oms']['polis_num']
        if ind_data['oms']['polis_issued']:
            polis_issue = ind_data['oms']['polis_issued']
        objs.append(Paragraph(f'5. Полис ОМС: {polis_num} с/к: {polis_issue}', style))
        if ind_data['snils']:
            snils = ind_data['snils']
        objs.append(Paragraph(f'6. СНИЛС: {snils}', style))
        address = ind_data['main_address']
        objs.append(Paragraph(f'7. Место регистрации: {address}', style))
        objs.append(Paragraph(f'8. Местность: {patient_locality}', style))

        hosp_operation = None
        if dir.parent and len(hosp_get_operation_data(dir.parent.napravleniye_id)) > 0:
            hosp_operation = hosp_get_operation_data(dir.parent.napravleniye_id)[-1]
        diagnos_after_operation = ''
        mkb10 = ''
        if hosp_operation:
            diagnos_after_operation = hosp_operation['diagnos_after_operation']
            mkb10 = hosp_operation['mkb10']

        if main_diagnos:
            diagnos_after_operation = main_diagnos

        objs.append(Paragraph(f"9. Диагноз основного заболевания (состояния):  <font face=\"PTAstraSerifBold\">{diagnos_after_operation}</font>", style))
        objs.append(Paragraph('_______________________________________________________________________________________________________', style))

        diagnosis = ''
        if mkb10_code:
            mkb10 = mkb10_code
        if mkb10.strip():
            diagnosis = mkb10.strip().split(' ')[0]
        elif dir.diagnos.strip():
            diagnosis = dir.diagnos.strip()
        objs.append(Paragraph(f'10. Код по МКБ: {diagnosis}', style))
        objs.append(Paragraph('11. Задача прижизненного патолого-анатомического исследования биопсийного (операционного) материала', style))
        objs.append(Paragraph(f'<u>{purpose}</u>', style))
        objs.append(Paragraph('12. Дополнительные клинические сведения (основные симптомы, оперативное или гормональное, или лучевое лечение,', style))
        objs.append(Paragraph('результаты инструментальных и лабораторных исследований)__________________________________________________', style))

        if clinical_data:
            objs.append(Paragraph(f"{clinical_data}", style))
        if not laboratory_value:
            objs.append(Paragraph('_______________________________________________________________________________________________________', style))
        if laboratory_value:
            lab_values = previous_laboratory_result(laboratory_value)
            if lab_values:
                objs.extend(lab_values)
        if descriptive_values:
            for v in descriptive_values:
                objs = previous_doc_refferal_result(v, objs)

        objs.append(
            Paragraph('13. Результаты предыдущих прижизненных патолого-анатомических исследований (наименование медицинской организа-ции, дата, регистрационный номер, заключение)', style)
        )
        if not previous_result:
            previous_result = '_______________________________________________________________________________________________________'
        objs.append(Paragraph(f'{previous_result}', style))
        objs.append(Paragraph('14. Проведенное предоперационное лечение (вид лечения, его сроки, дозировка лекарственного препарата, доза облучения)', style))
        objs.append(Paragraph('_______________________________________________________________________________________________________', style))
        objs.append(Paragraph('_______________________________________________________________________________________________________', style))
        if not method_get_material:
            objs.append(Paragraph('15. Способ получения биопсийного (операционного) материала: эндоскопическая биопсия—1, пункционная биопсия—2,', style))
            objs.append(Paragraph('аспирационная биопсия—3, инцизионная биопсия—4, операционная биопсия—5, операционный материал—6,', style))
            objs.append(Paragraph('самопроизвольно отделившиеся фрагменты тканей—7.', style))
        else:
            objs.append(Paragraph(f'15. Способ получения биопсийного (операционного) материала: {method_get_material}', style))
        objs.append(Paragraph(f'16. Дата забора материала {date_get_material} время {time_get_material}', style))
        objs.append(Paragraph(f'17. Материал помещен в 10%-ный раствор нейтрального формалина {is_aqua_material}', style))
        objs.append(Paragraph('18. Маркировка биопсийного (операционного) материала (расшифровка маркировки флаконов):', style))
        if not table_value:
            opinion = [
                [
                    Paragraph('Номер флакона', styleT),
                    Paragraph('Локализация патологического процесса (орган, топография)', styleT),
                    Paragraph('Характер патологического процесса (эрозия, язва, полип, пятно, узел, внешне не измененная ткань, отношение к окружающим тканям)', styleT),
                    Paragraph('Количество объектов', styleT),
                ],
                [Paragraph('1', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
                [Paragraph('2', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
                [Paragraph('3', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
                [Paragraph('4', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
                [Paragraph('5', styleT), Paragraph('', styleT), Paragraph('', styleT), Paragraph('', styleT)],
            ]

            cols_width = [
                20 * mm,
                50 * mm,
                70 * mm,
                25 * mm,
            ]
            tbl = Table(opinion, colWidths=cols_width)
            tbl.setStyle(
                TableStyle(
                    [
                        ('GRID', (0, 0), (-1, -1), 0.75, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]
                )
            )
            objs.append(Spacer(1, 5 * mm))
            objs.append(tbl)
        else:
            table_value_result = table_part_result(table_value, width_max_table=180)
            if table_value_result:
                objs.append(table_value_result)

        objs.append(Spacer(1, 5 * mm))
        if not doc_get_material:
            doc_get_material = dir.doc.get_fio()
        objs.append(Paragraph(f'19. Фамилия, инициалы врача: {doc_get_material} {space_symbol * 5} подпись _________', style))
        if dir.rmis_direction_date:
            dir_create = strdate(dir.rmis_direction_date)
        else:
            dir_create = strdate(dir.data_sozdaniya)
        objs.append(Paragraph(f'20. Дата направления:  {dir_create}', style))

        gistology_frame = Frame(0 * mm, 0 * mm, 210 * mm, 297 * mm, leftPadding=15 * mm, bottomPadding=16 * mm, rightPadding=7 * mm, topPadding=10 * mm, showBoundary=1)
        gistology_inframe = KeepInFrame(210 * mm, 297 * mm, objs, hAlign='LEFT', vAlign='TOP', fakeWidth=False)
        gistology_frame.addFromList([gistology_inframe], c)

    printForm()

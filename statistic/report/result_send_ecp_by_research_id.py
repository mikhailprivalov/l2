from openpyxl.styles import Border, Side, Alignment, Font, NamedStyle
from openpyxl.utils import get_column_letter

from utils.dates import normalize_date
from utils.db import namedtuplefetchall
from laboratory.settings import TIME_ZONE
from django.db import connection
import simplejson as json


def form_01(ws1, data):
    # Для журнала ВК - ДЛО
    style_border = NamedStyle(name="style_border_ca")
    bd = Side(style="thin", color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=12)
    style_border.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

    style_border2 = NamedStyle(name="style_border2")
    style_border2.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border2.font = Font(bold=False, size=11)
    style_border2.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")

    columns = [
        ('№ п/п.', 5),
        ('Номер направления', 30),
        ('Дата подтверждения', 10),
        ('Отправлен', 10),
        ('Врач', 25),
        ('Служебный ИД', 30),
        ('Дата создания', 30),
        ('Организация', 25),
        ('Фамилия, имя, отчество пациента', 25),
        ('Дата рождения', 10),
    ]
    row = 5
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=row, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=row, column=idx).style = style_border

    result = []
    previous_direction_number = None
    tmp_string = {}
    step = 0
    sql_data = sql_01(data['research_id'], data['d_s'], data['d_e'])
    for i in sql_data:
        if i.direction_number != previous_direction_number and step != 0:
            result.append(tmp_string.copy())
            tmp_string = {}
        tmp_string.update({i.field_title: i.field_value, "history_num": i.parent_direction, "doc_fio": i.doc_fio, "medical_examination": i.medical_examination})
        previous_direction_number = i.direction_number
        step += 1
    result.append(tmp_string.copy())
    previous_date = None
    step = 0
    for i in result:
        row += 1
        if step != 0 and previous_date != i.get("medical_examination"):
            step = 0
        step += 1
        ws1.cell(row=row, column=1).value = step
        ws1.cell(row=row, column=2).value = normalize_date(i.get("Дата"))
        ws1.cell(row=row, column=3).value = i.get("doc_fio")
        ws1.cell(row=row, column=4).value = i.get("ФИО пациента")
        ws1.cell(row=row, column=5).value = i.get("Дата рождения пациента")
        try:
            subject = json.loads(i.get("Предмет рассмотрения"))
        except:
            subject = {"rows": [""]}
        subject_result = ""
        k = 0
        for s in subject.get("rows"):
            if k != 0:
                subject_result = f"{subject_result} \n {s[0]}"
            else:
                subject_result = s[0]
            k += 1
        ws1.cell(row=row, column=6).value = subject_result
        try:
            diag = json.loads(i.get("Диагноз основной по МКБ-10"))
        except:
            diag = {"code": "-"}

        ws1.cell(row=row, column=7).value = diag.get("code")

        ws1.cell(row=row, column=8).value = i.get("history_num")

        name_form = i.get("Наименование/форма выпуска/дозировка", "-")
        count = i.get("Количество упаковок", "-")
        ws1.cell(row=row, column=9).value = f"{name_form} ({count})"
        try:
            members = json.loads(i.get("Члены комиссии"))
        except:
            members = {"rows": ["-", "-"]}
        members_result = ""
        m_step = 0
        for m in members.get("rows"):
            if m_step != 0:
                members_result = f"{members_result} \n {m[1]}"
            else:
                members_result = m[1]
            m_step += 1

        ws1.cell(row=row, column=10).value = members_result

        for c in range(11):
            ws1.cell(row=row, column=c + 1).style = style_border2

        previous_date = i.get("medical_examination")

    return ws1


def sql_01(research_id, d_s, d_e):
    """
    Для журнала ВК-ДЛО
    :return:
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    directions_issledovaniya.napravleniye_id as direction_number,
                    dn.result_rmis_send,
                    dn.rmis_direction_date,
                    hh.title as hospital_title,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'DD.MM.YYYY') as date_confirm,
                    ud.family as doc_family,
                    ud.name as doc_name,
                    ud.patronymic as doc_patronymic,
                    ci.family as patient_family,
                    ci.name as patient_name,
                    ci.patronymic as patient_patronymic,
                    ci.birthday
                    FROM directions_issledovaniya
                    LEFT JOIN directions_napravleniya dn ON dn.id = directions_issledovaniya.napravleniye_id
                    LEFT JOIN users_doctorprofile ud ON directions_issledovaniya.doc_confirmation_id=ud.id
                    LEFT JOIN clients_card cc ON cc.id=dn.id
                    LEFT JOIN clients_individual ci ON cc.individual_id=ci.id
                    LEFT JOIN hospitals_hospitals hh ON dn.hospital_id=hh.id
                    WHERE 
                      directions_issledovaniya.research_id=%(research_id)s
                      AND directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                      AND dn.rmis_number IS NOT NULL 
                    order by directions_issledovaniya.time_confirmation, ud.id
                """,
            params={'research_id': research_id, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )

        rows = namedtuplefetchall(cursor)
    return rows

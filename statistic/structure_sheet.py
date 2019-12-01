from openpyxl.utils.cell import get_column_letter
from openpyxl.styles import Font, NamedStyle
from collections import OrderedDict
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font, NamedStyle, Color, Fill, colors
import openpyxl
from directions.models import IstochnikiFinansirovaniya
from datetime import  timedelta
from laboratory import utils
from copy import deepcopy, copy

month_dict = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
              9: 'Сентябрь',
              10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}


def job_total_base(ws1, month, type_fin):
    """
    Основа(каркас) для итоговых данных
    :return:
    """
    ws1.column_dimensions[get_column_letter(1)].width = 22
    for i in range(1, 32):
        ws1.column_dimensions[get_column_letter(1 + i)].width = 4
        ws1.cell(row=4, column=1 + i).value = i

    ws1.cell(row=1, column=1).value = 'Месяц'
    ws1.cell(row=1, column=2).value = month_dict.get(month)
    ws1.cell(row=4, column=1).value = 'Вид работы'
    fin_obj = IstochnikiFinansirovaniya.objects.values_list('title').get(pk=type_fin)
    ws1.cell(row=2, column=1).value = fin_obj[0]

    return ws1


def jot_total_titles(ws1, titles):
    """
    Заговловки видов работ
    :param ws1:
    :param titles:
    :return:
    """
    cel_res = OrderedDict()
    for i in range(len(titles)):
        cell_row = 5 + i
        ws1.cell(row=cell_row, column=1).value = titles[i]
        cel_res[titles[i]] = cell_row

    return ws1, cel_res


def job_total_data(ws1, titles, data):
    for k, v in data.items():
        for res, uet in v.items():
            r = titles.get(res)
            ws1.cell(row=r, column=k + 1).value = uet


def passed_research_base(ws1, data_date):
    """
    :param ws1:
    :return:
    """
    style_border = NamedStyle(name="style_border")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=11)
    style_border.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=19)
    ws1.cell(row=1, column=1).value = 'ЖУРНАЛ учета приема и отказов в госпитализации за ' + data_date + \
                                      'г.(мед.документация Ф№001/У утв. МИНЗДРАВОМ СССР 04.10.1980г. №1030)'
    ws1.cell(row=1, column=1).style = style_border

    # габариты ячеек
    ws1.row_dimensions[2].height = 115
    columns = [
    ('№ п/п', 5), ('Время поступления', 8),
    ('Услуга (дата-время подтверждения)', 14), ('Направление', 11),
    ('Фамилия, имя, отчество больного', 20), ('Дата рождения', 10),
    ('Постоянное место жительства или адрес родственников, близких и N телефона', 23),('Каким учреждением был направлен или доставлен', 15),
    ('Отделение, в которое помещен больной', 12),('N карты (стационарного) больного', 10),
    ('Диагноз направившего учреждения', 7),('Диагноз при поступлении', 7),
    ('№ ДДУ', 16),('Полис', 21),
    ('Примечания', 10),('Выписан, переведен в другой стационар, умер (вписать и указать дату и название стационара, куда переведен', 20),
    ('Отметка о сообщении родственникам или учреждению', 11),('Если не был госпитализирован указать причину и принятые меры', 11),
    ('отказ в приеме первичный, повторный (вписать)', 11)
    ]

    for idx, column in enumerate(columns, 1):
        ws1.cell(row=2, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=2, column=idx).style = style_border

    return ws1


def passed_research_data(ws1, data):
    r = 2
    n = 0
    empty = ' '

    style_border1 = NamedStyle(name="style_border1")
    bd = Side(style='thin', color="000000")
    style_border1.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border1.font = Font(bold=False, size=11)
    style_border1.alignment = Alignment(wrap_text=True, horizontal='left', vertical='center')

    for i in data:
        current_research_title = i[1]
        current_polis_n = i[2] or empty
        current_polis_who_give = i[3] or empty
        current_napravlen = i[4]
        current_datatime_confirm = i[5]
        current_create_napr = i[6]
        current_diagnoz = i[7] or empty
        current_result = i[8] or empty
        current_napr_time_at = i[19] or empty
        current_num_card = i[10]
        current_family = i[11] or empty
        current_name = i[12] or empty
        current_patronymic = i[13] or empty
        current_birthday = i[14] or empty
        current_main_address = i[15] if i[15] else ''
        current_fact_address = i[16] if i[16] else empty
        current_address = current_main_address if current_main_address else current_fact_address
        current_work_place = i[17] or empty
        current_kem_napravlen = i[18] or empty
        r = r + 1
        n = n + 1
        ws1.cell(row=r, column=1).value = n
        ws1.cell(row=r, column=2).value = current_napr_time_at
        ws1.cell(row=r, column=3).value = f'{current_research_title},\n({current_datatime_confirm})'
        ws1.cell(row=r, column=4).value = f'{current_napravlen},\n({current_create_napr})'
        ws1.cell(row=r, column=5).value = current_family + ' ' + current_name + ' ' + current_patronymic
        ws1.cell(row=r, column=6).value = current_birthday
        ws1.cell(row=r, column=7).value = current_address
        ws1.cell(row=r, column=8).value = current_kem_napravlen
        ws1.cell(row=r, column=9).value = 'Приемное'
        ws1.cell(row=r, column=10).value = current_num_card
        ws1.cell(row=r, column=11).value = ' '
        ws1.cell(row=r, column=12).value = current_diagnoz
        ws1.cell(row=r, column=13).value = current_work_place
        ws1.cell(row=r, column=14).value = current_polis_n + ', ' + current_polis_who_give
        ws1.cell(row=r, column=15).value = ' '
        ws1.cell(row=r, column=16).value = current_result
        ws1.cell(row=r, column=17).value = ' '
        ws1.cell(row=r, column=18).value = ' '
        ws1.cell(row=r, column=19).value = ' '
        for j in range(1, 20):
            ws1.cell(row=r, column=j).style = style_border1

    return ws1


def style_sheet():
    style_border = NamedStyle(name="style_border")
    bd = Side(style='thin', color="000000")
    border = Border(left=bd, top=bd, right=bd, bottom=bd)

    style_border.border = border
    style_border.font = Font(bold=True, size=11)
    style_border.alignment = Alignment(wrap_text=True)

    style_border1 = NamedStyle(name="style_border1")
    style_border1.border = border
    style_border1.font = Font(bold=False, size=11)
    style_border1.alignment = Alignment(wrap_text=True)

    style_o = NamedStyle(name="style_o")
    style_o.font = Font(bold=True, size=11)

    return (style_border, style_o, style_border1)


def statistics_tickets_base(ws1, i_obj, type_fin, d1, d2, style_border, style_o):
    """
    Назначить ширину колонок. Вход worksheet выход worksheen с размерами
    Заголовки данных
    """

    columns = [
        ('Дата',13), ('Кол-во', 7),
        ('Услуга',15), ('Соисполнитель', 9),
        ('ФИО пациента,\n№ направления',31), ('Дата рождения', 13),
        ('№ карты',12), ('Данные полиса', 27),
        ('Код услуги',16), ('Услуга \n (ует/мин)', 12),
        ('Время \n подтверждения',18), ('Онкоподозрение', 13),
        ('Первичный прием',12), ('Цель \n посещения\n(код)е', 13),
        ('Диагноз \n МКБ',13), ('Впервые', 13),
        ('Результат \n обращения \n(код)',13), ('Исход(код)', 13)
    ]
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=7, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=7, column=idx).style = style_border

    # Закголовки столбцов
    ws1.cell(row=1, column=1).value = 'Сотрудник'
    ws1.cell(row=1, column=1).style = style_o
    ws1.cell(row=1, column=2).value = i_obj.fio
    ws1.cell(row=2, column=1).value = 'Должность'
    ws1.cell(row=2, column=1).style = style_o
    ws1.cell(row=2, column=2).value = i_obj.specialities.title if i_obj.specialities else ""
    ws1.cell(row=4, column=1).value = 'Период:'
    ws1.cell(row=4, column=1).style = style_o
    ws1.cell(row=5, column=1).value = d1
    ws1.cell(row=5, column=2).value = 'по'
    ws1.cell(row=5, column=3).value = d2
    ws1.cell(row=1, column=5).value = 'Код врача'
    ws1.cell(row=1, column=5).style = style_o
    ws1.cell(row=1, column=6).value = i_obj.personal_code
    ws1.cell(row=3, column=5).value = 'Источник'
    ws1.cell(row=3, column=5).style = style_o
    fin_obj = IstochnikiFinansirovaniya.objects.values_list('title').get(pk=type_fin)
    ws1.cell(row=3, column=6).value = fin_obj[0]

    return ws1


def statistics_tickets_data(ws1, issl_obj, i_obj, style_border1):
    #i_obj - обеъект доктор

    my_fill = openpyxl.styles.fills.PatternFill(patternType='solid', start_color='a9d094',
                                                end_color='a9d094')
    total_fill = openpyxl.styles.fills.PatternFill(patternType='solid', start_color='ffcc66',
                                                   end_color='ffcc66')

    r = 7
    r1 = r + 1
    total_sum = []
    one_days = timedelta(1)
    current_date = ''
    for issled in issl_obj:
        # Порядок колонок в issled:
        # title, code, is_first_reception, polis_n, polis_who_give, \
        # first_time, napravleniye_id, doc_confirmation_id, def_uet, co_executor_id, \
        # co_executor_uet, co_executor2_id, co_executor2_uet, datetime_confirm, date_confirm, \
        # time_confirm, maybe_onco, purpose, diagnos, iss_result, \
        # outcome, card_number, client_family, client_name, client_patronymic, \
        # birthday
        empty =' '
        current_datetime_confirm = issled[13]
        current_date = issled[14]
        current_count = 1
        current_research_title = issled[0]
        f = issled[22] or empty
        n = issled[23] or empty
        p = issled[24] or empty
        current_napr = str(issled[6])
       # current_patient_napr = f'{f} {n} {p}\n{current_napr}'
        current_patient_napr = f'{current_napr}'
        current_born = issled[25]
        current_card = issled[21]
        polis_n = issled[3] or ''
        polis_who = issled[4] or ''
        current_polis = f'{polis_n};\n{polis_who}'
        current_code_reserch = issled[1]
        current_doc_conf = issled[7]
        current_def_uet = issled[8] or 0
        current_co_exec1 = issled[9]
        current_uet1 = issled[10] or 0
        current_co_exec2 = issled[11]
        current_uet2 = issled[12] or 0
        current_time_confirm = issled[15]
        current_isfirst = issled[2]
        current_onko = issled[16]
        current_purpose = issled[17]
        current_diagnos = issled[18]
        current_firsttime = issled[5]
        current_result = issled[19]
        current_octome = issled[20]
        current_price = ''

        if r != 7 and r != 8:
            befor_date = ws1.cell(row=r, column=1).value
            if current_date != befor_date and not (ws1.cell(row=r, column=1).value).istitle():
                r = r + 1
                ws1.cell(row=r, column=1).value = 'Итого за ' +  befor_date[:2]
                ws1.cell(row=r, column=2).value = f'=SUM(B{r1}:B{r-1})'
                ws1.cell(row=r, column=10).value = f'=SUM(J{r1}:J{r-1})'

                total_sum.append(r)
                ws1.row_dimensions.group(r1, r - 1, hidden=True)
                rows = ws1[f'A{r}:V{r}']
                for row in rows:
                    for cell in row:
                        cell.fill = my_fill
                r1 = r + 1

        r = r + 1
        ws1.cell(row=r, column=1).value = current_date
        ws1.cell(row=r, column=2).value = 1
        ws1.cell(row=r, column=3).value = current_research_title
        sum_uet = 0
        co_exec = ''
        if (current_doc_conf == i_obj.pk) and (current_co_exec1 == i_obj.pk):
            sum_uet = sum_uet + current_def_uet
            co_exec = co_exec + 'ОСН'

        if (current_doc_conf == i_obj.pk) and (current_co_exec1 != i_obj.pk):
            sum_uet = sum_uet + current_def_uet
            co_exec = co_exec + 'ОСН'

        if (current_doc_conf != i_obj.pk) and (current_co_exec1 == i_obj.pk):
            sum_uet = sum_uet + current_uet1
            co_exec = co_exec + 'СО-1'

        if current_co_exec2 == i_obj.pk:
            sum_uet = sum_uet + current_uet2
            co_exec = co_exec + ', СО-2'
        ws1.cell(row=r, column=4).value = co_exec
        ws1.cell(row=r, column=5).value = current_patient_napr
        ws1.cell(row=r, column=6).value = current_born
        ws1.cell(row=r, column=7).value = current_card

        ws1.cell(row=r, column=8).value = current_polis
        ws1.cell(row=r, column=9).value = current_code_reserch
        ws1.cell(row=r, column=10).value = sum_uet
        ws1.cell(row=r, column=11).value = current_time_confirm

        ws1.cell(row=r, column=12).value = current_onko
        ws1.cell(row=r, column=13).value = current_isfirst
        ws1.cell(row=r, column=14).value = current_purpose
        ws1.cell(row=r, column=15).value = current_diagnos
        ws1.cell(row=r, column=16).value = current_firsttime
        ws1.cell(row=r, column=17).value = current_result
        ws1.cell(row=r, column=18).value = current_octome
        ws1.cell(row=r, column=19).value = ''

        rows = ws1[f'A{r}:V{r}']
        for row in rows:
            for cell in row:
                cell.style = style_border1

    r = r + 1
    ws1.cell(row=r, column=1).value = 'Итого за ' + current_date[:2]
    ws1.cell(row=r, column=2).value = f'=SUM(B{r1}:B{r-1})'
    ws1.cell(row=r, column=10).value = f'=SUM(J{r1}:J{r-1})'
    ws1.row_dimensions.group(r1, r - 1, hidden=True)
    total_sum.append(r)
    rows = ws1[f'A{r}:V{r}']
    for row in rows:
        for cell in row:
            cell.fill = my_fill

    t_s = '=SUM('
    t_s_uet = '=SUM('
    for ts in total_sum:
        t_uet = ts
        t_s = t_s + f'(B{ts})' + ','
        t_s_uet = t_s_uet + f'(J{t_uet})' + ','
    t_s = t_s + ')'
    t_s_uet = t_s_uet + ')'
    r = r + 1
    ws1.cell(row=r, column=1).value = 'Итого Всего'
    ws1.cell(row=r, column=2).value = t_s
    ws1.cell(row=r, column=10).value = t_s_uet
    rows = ws1[f'A{r}:V{r}']
    for row in rows:
        for cell in row:
            cell.fill = total_fill

    return ws1


def inderect_job_base(ws1, doc_obj, d1, d2):
    pink_fill = openpyxl.styles.fills.PatternFill(patternType='solid', start_color='FCD5B4', end_color='FCD5B4')
    rows = ws1[f'A{1}:V{1}']
    for row in rows:
        for cell in row:
            cell.fill = pink_fill

    ws1.column_dimensions[get_column_letter(1)].width = 15
    ws1.column_dimensions[get_column_letter(2)].width = 30
    ws1.column_dimensions[get_column_letter(3)].width = 15

    ws1.cell(row=1, column=1).value = "Косвенные услуги"
    ws1.cell(row=2, column=1).value = "Сотрудник"
    ws1.cell(row=2, column=2).value = doc_obj.fio
    ws1.cell(row=3, column=1).value = f'c {d1}'
    ws1.cell(row=3, column=2).value = f'по {d2}'

    return ws1


def inderect_job_data(ws1, indirect_job):
    r = 4
    for k,v in indirect_job.items():
        for k_job, v_job in v.items():
            r = r + 1
            ws1.cell(row=r, column=1).value = k
            ws1.cell(row=r, column=2).value = k_job
            ws1.cell(row=r, column=3).value = v_job

    return ws1


def statistic_research_base(ws1, d1, d2, research_titile):
    style_border = NamedStyle(name="style_border")
    bd = Side(style='thin', color="000000")
    style_border.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border.font = Font(bold=True, size=11)
    style_border.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')

    ws1.cell(row=1, column=1).value = 'Услуга:'
    ws1.cell(row=1, column=2).value = research_titile
    ws1.cell(row=2, column=1).value = 'Период:'
    ws1.cell(row=3, column=1).value = f'c {d1} по {d2}'

    columns = [
        ('Исполнитель',26),('Направление, за дату',15),
        ('Дата подтверждения',16.5),('Время подтверждения',16.5),
        ('Источник',10),('Цена',10),
        ('Кол-во',7),('Скидка',7.5),
        ('Сумма',14),('Физлицо',26),
        ('Дата рождения',12),('Возраст',8),
        ('Карта',15)
    ]
    for idx, column in enumerate(columns, 1):
        ws1.cell(row=4, column=idx).value = column[0]
        ws1.column_dimensions[get_column_letter(idx)].width = column[1]
        ws1.cell(row=4, column=idx).style = style_border

    return ws1


def statistic_research_data(ws1, researches):
    """
    res - результат выборки SQL
    порядок возврата:
    napr, date_confirm, time_confirm, create_date_napr, create_time_napr,
    doc_fio, coast, discount, how_many, ((coast + (coast/100 * discount)) * how_many)::NUMERIC(10,2) AS sum_money,
    ist_f, time_confirmation, num_card, ind_family, ind_name,
    patronymic, birthday, date_born, to_char(EXTRACT(YEAR from age(time_confirmation, date_born)), '999') as ind_age
    :return:
    """
    style_border_res = NamedStyle(name="style_border_res")
    bd = Side(style='thin', color="000000")
    style_border_res.border = Border(left=bd, top=bd, right=bd, bottom=bd)
    style_border_res.font = Font(bold=False, size=11)
    style_border_res.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    r = 4
    for res in researches:
        r += 1
        current_doc = res[5]
        current_napr = res[0]
        current_napr_atcreate = res[3]
        current_date_confirm = res[1]
        current_time_confirm = res[2]
        current_ist_f = res[10]
        current_coast = res[6]
        current_how_many = res[8]
        current_discount = res[7]
        current_price_total = res[9]
        current_ind_fio = f'{res[13]} {res[14]} {res[15]}'
        current_born = res[16]
        current_age = res[18]
        current_num_card = res[12]

        ws1.cell(row=r, column=1).value = current_doc
        ws1.cell(row=r, column=2).value = f'{current_napr}, {current_napr_atcreate}'
        ws1.cell(row=r, column=3).value = current_date_confirm
        ws1.cell(row=r, column=4).value = current_time_confirm
        ws1.cell(row=r, column=5).value = current_ist_f
        ws1.cell(row=r, column=6).value = current_coast
        ws1.cell(row=r, column=7).value = current_how_many
        ws1.cell(row=r, column=8).value = current_discount
        ws1.cell(row=r, column=9).value = current_price_total
        ws1.cell(row=r, column=10).value = current_ind_fio
        ws1.cell(row=r, column=11).value = current_born
        ws1.cell(row=r, column=12).value = current_age
        ws1.cell(row=r, column=13).value = current_num_card

        rows = ws1[f'A{r}:M{r}']
        for row in rows:
            for cell in row:
                cell.style = style_border_res

    return ws1

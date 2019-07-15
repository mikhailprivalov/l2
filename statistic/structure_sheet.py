from openpyxl.utils.cell import get_column_letter
from openpyxl.styles import Font, NamedStyle
from collections import OrderedDict
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font, NamedStyle, Color, Fill, colors
import openpyxl

month_dict = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
              9: 'Сентябрь',
              10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}


def job_total_base(ws1, month):
    """
    Основа(каркас) для итоговых данных
    :return:
    """
    ws1.column_dimensions[get_column_letter(1)].width = 22
    for i in range(1, 32):
        ws1.column_dimensions[get_column_letter(1 + i)].width = 4
        ws1.cell(row=3, column=2 + i).value = i

    ws1.cell(row=1, column=1).value = 'Месяц'
    ws1.cell(row=1, column=2).value = month_dict.get(month)
    ws1.cell(row=3, column=1).value = 'Вид работы'

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
        cell_row = 4 + i
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

    ws1.cell(row=2, column=1).value = '№ п/п'
    ws1.cell(row=2, column=2).value = 'Время поступления'
    ws1.cell(row=2, column=3).value = 'Услуга'
    ws1.cell(row=2, column=4).value = 'Направление'
    ws1.cell(row=2, column=5).value = 'Фамилия, имя, отчество больного'
    ws1.cell(row=2, column=6).value = 'Дата рождения'
    ws1.cell(row=2, column=7).value = 'Постоянное место жительства или адрес родственников, близких и N телефона'
    ws1.cell(row=2, column=8).value = 'Каким учреждением был направлен или доставлен'
    ws1.cell(row=2, column=9).value = 'Отделение, в которое помещен больной'
    ws1.cell(row=2, column=10).value = 'N карты (стационарного) больного'
    ws1.cell(row=2, column=11).value = 'Диагноз направившего учреждения'
    ws1.cell(row=2, column=12).value = 'Диагноз при поступлении'
    ws1.cell(row=2, column=13).value = '№ ДДУ'
    ws1.cell(row=2, column=14).value = 'Полис'
    ws1.cell(row=2, column=15).value = 'Примечания'
    ws1.cell(row=2,
             column=16).value = 'Выписан, переведен в другой стационар, умер (вписать и указать дату и название стационара, куда переведен'
    ws1.cell(row=2, column=17).value = 'Отметка о сообщении родственникам или учреждению'
    ws1.cell(row=2, column=18).value = 'Если не был госпитализирован указать причину и принятые меры '
    ws1.cell(row=2, column=19).value = 'отказ в приеме первичный, повторный (вписать)'
    for i in range(20):
        ws1.cell(row=2, column=i + 1).style = style_border

    # габариты ячеек
    ws1.row_dimensions[2].height = 115
    ws1.column_dimensions[get_column_letter(1)].width = 5
    ws1.column_dimensions[get_column_letter(2)].width = 8
    ws1.column_dimensions[get_column_letter(3)].width = 14
    ws1.column_dimensions[get_column_letter(4)].width = 8
    ws1.column_dimensions[get_column_letter(5)].width = 20
    ws1.column_dimensions[get_column_letter(6)].width = 10
    ws1.column_dimensions[get_column_letter(7)].width = 23
    ws1.column_dimensions[get_column_letter(8)].width = 15
    ws1.column_dimensions[get_column_letter(9)].width = 12
    ws1.column_dimensions[get_column_letter(10)].width = 10
    ws1.column_dimensions[get_column_letter(11)].width = 7
    ws1.column_dimensions[get_column_letter(12)].width = 7
    ws1.column_dimensions[get_column_letter(13)].width = 16
    ws1.column_dimensions[get_column_letter(14)].width = 21
    ws1.column_dimensions[get_column_letter(15)].width = 10
    ws1.column_dimensions[get_column_letter(16)].width = 20
    ws1.column_dimensions[get_column_letter(17)].width = 11
    ws1.column_dimensions[get_column_letter(18)].width = 11
    ws1.column_dimensions[get_column_letter(19)].width = 11

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
        current_client_id = i[0]
        current_research_title = i[1]
        current_polis_n = i[2] if i[2] else empty
        current_polis_who_give = i[3] if i[3] else empty
        current_napravlen = i[4]
        current_datatime_confirn = i[5]
        current_time_cofirm = i[6]
        current_diagnoz = i[7] if i[7] else empty
        current_result = i[8] if i[8] else empty
        current_num_card = i[11]
        current_family = i[12] if i[12] else empty
        current_name = i[13] if i[13] else empty
        current_patronymic = i[14] if i[14] else empty
        current_birthday = i[15] if i[15] else empty
        current_main_address = i[19] if i[19] else ''
        current_fact_address = i[20] if i[20] else empty
        current_address = current_main_address if current_main_address else current_fact_address
        current_kem_napravlen = i[22] if i[22] else empty
        r = r + 1
        n = n + 1
        ws1.cell(row=r, column=1).value = n
        ws1.cell(row=r, column=2).value = current_time_cofirm
        ws1.cell(row=r, column=3).value = current_research_title
        ws1.cell(row=r, column=4).value = current_napravlen
        ws1.cell(row=r, column=5).value = current_family + ' ' + current_name + ' ' + current_patronymic
        ws1.cell(row=r, column=6).value = current_birthday
        ws1.cell(row=r, column=7).value = current_address
        ws1.cell(row=r, column=8).value = current_kem_napravlen
        ws1.cell(row=r, column=9).value = 'Приемное'
        ws1.cell(row=r, column=10).value = current_num_card
        ws1.cell(row=r, column=11).value = ' '
        ws1.cell(row=r, column=12).value = current_diagnoz
        ws1.cell(row=r, column=13).value = ' '
        ws1.cell(row=r, column=14).value = current_polis_n + ', ' + current_polis_who_give
        ws1.cell(row=r, column=15).value = ' '
        ws1.cell(row=r, column=16).value = current_result
        ws1.cell(row=r, column=17).value = ' '
        ws1.cell(row=r, column=18).value = ' '
        ws1.cell(row=r, column=19).value = ' '
        for j in range(1, 21):
            ws1.cell(row=r, column=j).style = style_border1

    return ws1

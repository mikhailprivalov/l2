from openpyxl.utils.cell import get_column_letter
from openpyxl.styles import Font, NamedStyle
from collections import OrderedDict
from openpyxl.styles import PatternFill, Border, Side, Alignment, Font, NamedStyle, Color, Fill, colors
import openpyxl

month_dict = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь',
              10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}

def job_total_base(ws1, month):
    """
    Основа(каркас) для итоговых данных
    :return:
    """
    ws1.column_dimensions[get_column_letter(1)].width = 22
    for i in range(31):
        ws1.column_dimensions[get_column_letter(2+i)].width = 4
        ws1.cell(row=3, column=2 + i).value = 1 + i

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
        cell_row = 4+i
        ws1.cell(row=cell_row, column=1).value = titles[i]
        cel_res[titles[i]] = cell_row

    return ws1, cel_res


def job_total_data(ws1, titles, data):
    for k,v in data.items():
        for res,uet in v.items():
            print(res, '-', uet)
            r = titles.get(res)
            print(r)
            ws1.cell(row=r, column=k + 1).value = uet


def passed_research_base(ws1):
    """

    :param ws1:
    :return:
    """
    ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=19)
    ws1.cell(row=1, column=1).value = 'ЖУРНАЛ учета приема и отказов в госпитализации за 31.08.2019 г. ' \
                               '(мед.документация Ф№001/У утв. МИНЗДРАВОМ СССР 04.10.1980г. №1030)'
    # ws1.column_dimensions[get_column_letter(1)].width = 22
    ws1.cell(row=1, column=1).alignment = Alignment(horizontal='center')

    ws1.cell(row=2, column=1).value = '№ п/п'
    ws1.cell(row=2, column=2).value = 'Время поступления'
    ws1.cell(row=2, column=2).alignment = Alignment(textRotation=90)
    ws1.cell(row=2, column=3).value = 'Услуга'
    ws1.cell(row=2, column=3).alignment = Alignment(textRotation=90)
    ws1.cell(row=2, column=4).value = 'Направление'
    ws1.cell(row=2, column=4).alignment = Alignment(textRotation=90)
    ws1.cell(row=2, column=5).value = 'Фамилия, имя, отчество больного'
    ws1.cell(row=2, column=6).value = 'Дата рождения'
    ws1.cell(row=2, column=7).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=7).value = 'Постоянное место жительства или адрес родственников, близких и N телефона'
    ws1.cell(row=2, column=8).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=8).value = 'Каким учреждением был направлен или доставлен'
    ws1.cell(row=2, column=9).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=9).value = 'Отделение, в которое помещен больной'
    ws1.cell(row=2, column=10).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=10).value = 'N карты (стационарного) больного'
    ws1.cell(row=2, column=11).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=11).value = 'Диагноз направившего учреждения'
    ws1.cell(row=2, column=12).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=12).value = 'Диагноз при поступлении'
    ws1.cell(row=2, column=13).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=13).value = '№ ДДУ'
    ws1.cell(row=2, column=14).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=14).value = 'Полис'
    ws1.cell(row=2, column=15).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=15).value = 'Примечания'
    ws1.cell(row=2, column=16).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=16).value = 'Выписан, переведен в другой стационар, умер (вписать и указать дату и название стационара, куда переведен'
    ws1.cell(row=2, column=17).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=17).value = 'Отметка о сообщении родственникам или учреждению'
    ws1.cell(row=2, column=18).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=18).value = 'Если не был госпитализирован указать причину и принятые меры '
    ws1.cell(row=2, column=19).alignment = Alignment(wrapText=True)
    ws1.cell(row=2, column=19).value = 'отказ в приеме первичный, повторный (вписать)'




    return ws1

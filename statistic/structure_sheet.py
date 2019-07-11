from openpyxl.utils.cell import get_column_letter
from openpyxl.styles import Font, NamedStyle
from collections import OrderedDict

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
    print(titles)
    print(data)
    for k,v in data.items():
        for res,uet in v.items():
            print(res, '-', uet)
            r = titles.get(res)
            print(r)
            ws1.cell(row=r, column=k + 1).value = uet




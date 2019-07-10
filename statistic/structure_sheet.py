from openpyxl.utils.cell import get_column_letter
from openpyxl.styles import Font, NamedStyle

month_dict = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август', 9: 'Сентябрь',
              10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}

def job_total_base(ws1, month):
    """
    Основа(каркас) для итоговых данных
    :return:
    """
    ws1.column_dimensions[get_column_letter(1)].width = 22
    for i in range(31):
        ws1.column_dimensions[get_column_letter(2+i)].width = 3
        ws1.cell(row=3, column=2 + i).value = 1 + i

    ws1.cell(row=1, column=1).value = 'Месяц'
    ws1.cell(row=1, column=2).value = month_dict.get(month)
    ws1.cell(row=3, column=1).value = 'Вид работы'

    return ws1

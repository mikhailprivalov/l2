from openpyxl.reader.excel import load_workbook

from researches.models import Tubes


def check_need_col(cols: list, need_cols: set):
    other_need_cols = set(set(cols) - need_cols)
    if len(other_need_cols) + len(need_cols) != len(cols):
        return False
    return True

def form_01(request_data):
    """
    Загрузка цен по прайсу

    На входе:
    Файл XLSX с ёмкостями для биоматериала
    Cтруктура:
    Наименование (Tube.title), Краткое наименование (Tube.short_title), Цвет (красный, зеленый)
    """

    file = request_data.get("file")
    wb = load_workbook(filename=file)
    ws = wb[wb.sheetnames[0]]
    columns = [{"field": 'title', "key": 'title', "title": 'Пробирка', "align": 'left', "width": 250}, {"field": 'reason', "key": 'reason', "title": 'Причина ошибки'}]
    incorrect_tubes = []
    title_idx, short_title_idx, color_idx = (
        '',
        '',
        '',
    )
    need_col_name = {"наименование", "код", "цвет (rgb, hex)"}
    starts = False
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "цвет (rgb, hex)" in cells:
                if not check_need_col(cells, need_col_name):
                    return {"ok": False, "result": {}, "message": "Нет обязательных полей"}
                title_idx = cells.index("наименование")
                short_title_idx = cells.index("код")
                color_idx = cells.index("цвет (rgb, hex)")
                starts = True
        else:
            title = cells[title_idx].strip()
            short_title = cells[short_title_idx].strip()
            color = cells[color_idx].strip()
            valid = Tubes.check_tube(title, short_title, color)
            if not valid:
                incorrect_tubes.append({"title": title, "reason": "Валидация не пройдена"})
                continue
            new_tube = Tubes(title=title, short_title=short_title, color=color)
            new_tube.save()
    result = {
        "colData": columns,
        "data": incorrect_tubes,
    }

    if not starts:
        return {"ok": False, "result": [], "message": "Не найдены колонка 'цвет (rgb, hex)'"}
    return {"ok": True, "result": result, "message": ""}

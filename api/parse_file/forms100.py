from openpyxl.reader.excel import load_workbook

from contracts.models import PriceName, PriceCoast
from directory.models import Researches


def form_01(request_data):
    """
    Загрузка цен по прайсу

    На входе:
    Файл XLSX с ценами прайса
    Cтруктура:
    Код по прайсу (internal_code Researches), Услуга (title_researches), следующее поле - любое текстовое название прайса (priceCoasts.coast)
    """
    price_id = request_data.get("entity_id")
    file = request_data.get("file")
    price = PriceName.objects.filter(pk=price_id).first()
    if not price:
        return {"ok": False, "result": [], "message": "Такого прайса нет"}
    wb = load_workbook(filename=file)
    ws = wb[wb.sheetnames[0]]
    internal_code_idx, coast_idx = (
        '',
        '',
    )
    starts = False
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "Код по прайсу" in cells:
                internal_code_idx = cells.index("Код по прайсу")
                try:
                    coast_idx = cells.index(price.title)
                except ValueError:
                    return {"ok": False, "result": [], "message": "Название прайса не совпадает"}
                starts = True
        else:
            internal_code = cells[internal_code_idx].strip()
            try:
                coast = float(cells[coast_idx].strip())
            except Exception:
                continue
            if internal_code == "None" or not coast:
                continue
            service = Researches.objects.filter(internal_code=internal_code).first()
            if not service:
                continue
            current_coast = PriceCoast.objects.filter(price_name_id=price.pk, research_id=service.pk).first()
            if current_coast:
                if current_coast.coast != coast:
                    current_coast.coast = coast
                    current_coast.save()
            else:
                new_coast = PriceCoast(price_name_id=price.pk, research_id=service.pk, coast=coast)
                new_coast.save()
    if not starts:
        return {"ok": False, "result": [], "message": "Не найдены колонка 'Код по прайсу' "}
    return {"ok": True, "result": [], "message": ""}

def form_02(request_data):
    """
    Загрузка посещений по файлу

    На входе:
    Файл XLSX с посещениями
    Cтруктура:
    номер карты, Заведующий отделением, Отделение, Услуга, Фамилия, Имя, Отчество, Дата рождения, СНИЛС, Диагноз, Дата услуги, Это травма
    """
    file = request_data.get("file")
    wb = load_workbook(filename=file)
    ws = wb[wb.sheetnames[0]]
    card_number_idx, head_department_idx, department_idx, service_idx, family_idx, name_idx, patronymic_idx, birthday_idx, snils_idx, diagnos_idx, service_date_idx, is_travma_idx = (
        '', '', '', '', '', '', '', '', '', '', '', '')
    starts = False
    file_data = []
    for row in ws.rows:
        cells = [str(x.value) for x in row]
        if not starts:
            if "номер карты" in cells:
                card_number_idx = cells.index("номер карты")
                head_department_idx = cells.index("Заведующий отделением")
                department_idx = cells.index("Отделение")
                service_idx = cells.index("Услуга")
                family_idx = cells.index("Фамилия")
                name_idx = cells.index("Имя")
                patronymic_idx = cells.index("Отчество")
                birthday_idx = cells.index("Дата рождения")
                snils_idx = cells.index("СНИЛС")
                diagnos_idx = cells.index("Диагноз")
                service_date_idx = cells.index("Дата услуги")
                is_travma_idx = cells.index("Это травма")
                starts = True
        else:
            print('мы идем')
            tmp_data = {
                "card_number": row[card_number_idx],
                "head_department": row[head_department_idx],
                "department": row[department_idx],
                "service": row[service_idx],
                "family": row[family_idx],
                "name": row[name_idx],
                "patronymic": row[patronymic_idx],
                "birthday": row[birthday_idx],
                "snils": row[snils_idx],
                "diagnos": row[diagnos_idx],
                "service_date": row[service_date_idx],
                "is_travma": row[is_travma_idx]
            }
            file_data.append(tmp_data)
    if not starts:
        return {"ok": False, "result": [], "message": "Не найдена колонка 'номер карты' "}
    return {"ok": True, "result": [], "message": ""}

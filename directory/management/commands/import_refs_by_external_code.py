from django.core.management.base import BaseCommand
from django.db.models import Q
from openpyxl.workbook import Workbook

from appconf.manager import SettingManager
from directory.models import Researches, Fractions, Unit
from openpyxl import load_workbook

from external_system.models import FsliRefbookTest


def is_float(str_float: str):
    if "." in str_float:
        return True
    return False


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        Фаил с  колонками "Код", "Условия", "Ед. изм", Нижняя Гр., Верхняя Гр.
        для импорта референсов в фракции по внешнему коду
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]

        starts = False
        code_idx, title_idx, conditions_idx, unit_idx, start_ref_idx, end_ref_idx = None, None, None, None, None, None
        fraction = None
        current_code, current_title = None, None
        result_wb = Workbook()
        result_ws = result_wb[result_wb.sheetnames[0]]
        result_ws.append(['Внешний код', 'Название фракции (теста)', 'Статус', 'Причина'])
        ref_m, ref_f = [], []
        step = 0
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Условия" in cells:
                    code_idx = cells.index("Код")
                    title_idx = cells.index("Тест")
                    conditions_idx = cells.index("Условия")
                    start_ref_idx = cells.index("Нижняя Гр.")
                    end_ref_idx = cells.index("Верхняя Гр.")
                    starts = True
            else:
                code = cells[code_idx].strip()
                title = cells[title_idx].strip()
                conditions = cells[conditions_idx].strip()
                start = cells[start_ref_idx].strip()
                end = cells[end_ref_idx].strip()
                if start == "None" or end == "None":
                    result_ws.append([current_code, current_title, '-', 'Нет границ'])
                    continue
                tmp_cond_str = conditions.split("Пол: ")
                age = None
                gender = None
                if len(tmp_cond_str) < 2:
                    result_ws.append([current_code, current_title, '-', 'Нет пола'])
                    continue
                tmp_cond_str = tmp_cond_str[1].split("Возр.: ")
                if len(tmp_cond_str) > 1:
                    gender = tmp_cond_str[0]
                    age = tmp_cond_str[1]
                else:
                    gender = tmp_cond_str[0]
                    age = None
                if age and is_float(age):
                    age_range = age.split("-")
                    age_start = age_range[0] * 365
                    age_end = age_range[1] * 365
                    age = f"{age_start}-{age_end}"
                elif not age:
                    age = "Все"

                if code != "None":
                    current_code = code
                    current_title = title
                    if fraction:
                        fraction.ref_m = ref_m
                        fraction.ref_f = ref_f
                        print('Мы сохранили фракцию')
                    ref_m, ref_f = [], []
                    fraction = Fractions.objects.filter(external_code__iexact=code).first()
                    if not fraction:
                        result_ws.append([current_code, title, '-', 'Нет в справочнике'])
                        continue

                    if gender.lower() == "общий" and len(fraction.ref_m) == 0 and len(fraction.ref_f) == 0:
                        ref_f.append({"age": age, "value": f"{start}-{end}"})
                        ref_m.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "мужской" and len(fraction.ref_m) == 0:
                        ref_m.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "женский" and len(fraction.ref_f) == 0:
                        ref_f.append({"age": age, "value": f"{start}-{end}"})

                    result_ws.append([current_code, fraction.title, '+', ''])

                elif code == "None" and fraction:
                    if gender.lower() == "общий" and len(fraction.ref_m) == 0 and len(fraction.ref_f) == 0:
                        ref_f.append({"age": age, "value": f"{start}-{end}"})
                        ref_m.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "мужской" and len(fraction.ref_m) == 0:
                        ref_m.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "женский" and len(fraction.ref_f) == 0:
                        ref_f.append({"age": age, "value": f"{start}-{end}"})

                    result_ws.append([fraction.external_code, fraction.title, '+', ''])
                else:
                    result_ws.append([current_code, current_title, '-', 'Фракции нет в справочнике'])
                step += 1
        dir_tmp = SettingManager.get("dir_param")
        result_wb.save(f"{dir_tmp}/result_import_refs.xlsx")

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
        result_ws.append(['Внешний код', 'Название фракции (теста)', 'Статус'])
        ref_m, ref_f = [], []
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
                    continue
                tmp_cond_str = conditions.split("Пол: ")
                age = ""
                gender = ""
                tmp_cond_str2 = ""
                if len(tmp_cond_str) < 2:
                    gender = "общий"
                    age = None
                elif len(tmp_cond_str) >= 2:
                    tmp_cond_str2 = tmp_cond_str[1].split("Возр.: ")
                if len(tmp_cond_str2) > 1:
                    gender = tmp_cond_str2[0].strip()
                    age = tmp_cond_str2[1].strip()
                else:
                    gender = tmp_cond_str2[0].strip()
                if age and is_float(age):
                    age_range = age.split("-")
                    try:
                        age_start = float(age_range[0].strip()) * 365
                        age_end = float(age_range[1].strip()) * 365
                        age = f"дней {age_start}-{age_end}"
                    except Exception as e:
                        self.stdout.write("Не удалось преобразовать в дни")
                        continue
                elif not age:
                    age = "Все"

                if code != "None":
                    if fraction and (len(ref_m) > 0 or len(ref_f) > 0):
                        ref_m, ref_f = Fractions.convert_ref(ref_m, ref_f, True)
                        if len(ref_m) > 0:
                            fraction.ref_m = ref_m
                        if len(ref_f) > 0:
                            fraction.ref_f = ref_f
                        fraction.save()
                        result_ws.append([fraction.external_code, fraction.title, '+'])
                        self.stdout.write(f"Референсы {fraction.title} обновлены")

                    ref_m, ref_f = [], []
                    fraction = Fractions.objects.filter(external_code__iexact=code).first()
                    if not fraction:
                        continue

                    if gender.lower() == "общий":
                        if len(str(fraction.ref_m)) <= 2:
                            ref_m.append({"age": age, "value": f"{start}-{end}"})
                        if len(str(fraction.ref_f)) <= 2:
                            ref_f.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "мужской" and len(str(fraction.ref_m)) <= 2:
                        ref_m.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "женский" and len(str(fraction.ref_f)) <= 2:
                        ref_f.append({"age": age, "value": f"{start}-{end}"})

                elif code == "None" and fraction:
                    if gender.lower() == "общий":
                        if len(str(fraction.ref_m)) <= 2:
                            ref_m.append({"age": age, "value": f"{start}-{end}"})
                        if len(str(fraction.ref_f)) <= 2:
                            ref_f.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "мужской" and len(str(fraction.ref_m)) <= 2:
                        ref_m.append({"age": age, "value": f"{start}-{end}"})
                    elif gender.lower() == "женский" and len(str(fraction.ref_f)) <= 2:
                        ref_f.append({"age": age, "value": f"{start}-{end}"})

        dir_tmp = SettingManager.get("dir_param")
        result_wb.save(f"{dir_tmp}/result_import_refs.xlsx")

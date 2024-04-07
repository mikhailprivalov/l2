from django.core.management.base import BaseCommand
from openpyxl.workbook import Workbook

from appconf.manager import SettingManager
from directory.models import Researches, Fractions, Unit
from openpyxl import load_workbook


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]
        wb = load_workbook(filename=fp)
        ws = wb[wb.sheetnames[0]]
        result_wb = Workbook()
        result_ws = result_wb[result_wb.sheetnames[0]]
        result_ws.append(['Название', 'Список услуг', 'Код ФСЛИ', 'статус'])

        starts = False
        title, unit, research, fsli = '', '', '', ''
        for row in ws.rows:
            cells = [str(x.value) for x in row]
            if not starts:
                if "Код ФСЛИ" in cells:
                    title = cells.index("Название")
                    unit = cells.index("Ед.Изм.")
                    research = cells.index("Список услуг")
                    fsli = cells.index("Код ФСЛИ")
                    starts = True
            else:
                research_nmy_code = cells[research].split(' - ')[0]
                if research_nmy_code != "None":
                    fraction_fsli_code = cells[fsli].split(' ')[0]
                    current_research = Researches.objects.filter(code=research_nmy_code).first()
                    if current_research:
                        current_fractions = Fractions.objects.filter(research_id=current_research.pk)
                        need_add_fractions = True
                        relation_id = None
                        for fraction in current_fractions:
                            if fraction.fsli == fraction_fsli_code:
                                need_add_fractions = False
                            relation_id = fraction.relation_id
                        if need_add_fractions:
                            unit_id = None
                            unit_db = Unit.objects.filter(short_title=cells[unit].strip()).first()
                            if unit_db:
                                unit_id = unit_db.pk
                            if relation_id is not None:
                                new_fraction = Fractions(research_id=current_research.pk, relation_id=relation_id, title=cells[title], unit_id=unit_id, fsli=fraction_fsli_code)
                                new_fraction.save()
                                self.stdout.write(f'Услуге: {current_research.title} добавлена фракция: {new_fraction.title}')
                                result_ws.append([cells[title], cells[research], cells[fsli], '+'])
                        else:
                            result_ws.append([cells[title], cells[research], cells[fsli], 'уже есть'])
                    else:
                        result_ws.append([cells[title], cells[research], cells[fsli], 'Услуга не найдена'])
                else:
                    result_ws.append([cells[title], cells[research], cells[fsli], 'Нет НМУ кода'])

        dir_tmp = SettingManager.get("dir_param")
        result_wb.save(f"{dir_tmp}/result_import_fractions.xlsx")

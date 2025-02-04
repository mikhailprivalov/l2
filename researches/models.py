import re
import sys

from django.db import models

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


class Tubes(models.Model):
    """Таблица типов пробирок"""

    id = models.AutoField(primary_key=True, db_index=True)
    color = models.CharField(max_length=7)  # Цвет в CSS формате (#1122FF)
    title = models.CharField(max_length=255)  # Название
    short_title = models.CharField(max_length=16, default="", blank=True)
    is_default_external_tube = models.BooleanField(default=False, blank=True, db_index=True)

    def __str__(self):
        return self.title

    @staticmethod
    def get_default_external_tube():
        tube = Tubes.objects.filter(is_default_external_tube=True).first()

        if not tube:
            tube = Tubes.objects.create(color="#8C95E5", title="Ёмкость", short_title="ёмк", is_default_external_tube=True)

        return tube

    def get_short_title(self):
        pr = self.short_title
        if pr == "":
            types = [
                "фиолет",
                "красн",
                "стекло",
                "черн",
                "белая",
                "серая",
                "фильтро",
                "чашка",
                "голубая",
                "зеленая",
                "желтая",
                "жёлтая",
                "зелёная",
                "контейнер",
                "зонд",
                "п ф",
                "л ф",
                "синяя",
            ]
            tb_t = self.title.lower()
            pr = ""
            for s in types:
                if s in tb_t:
                    pr = s[0]
            pr = pr.upper()
            r = re.search(u"(\d+\.\d|\d+,\d+|\d+)\s(мл)", tb_t)
            if r:
                pr += r.group(1) + r.group(2)
        return pr

    @staticmethod
    def get_all(pk_in_title=False):
        result = [
            {
                "id": tube.pk,
                "label": tube.title if not pk_in_title else f"{tube.title} ({tube.pk})",
                "shortLabel": tube.short_title,
                "color": tube.color,
            }
            for tube in Tubes.objects.all().order_by("title")
        ]
        return result

    class Meta:
        verbose_name = 'Вид ёмкости'
        verbose_name_plural = 'Виды ёмкостей'

    @staticmethod
    def check_tube(title, short_title, color):
        title_valid = 0 < len(title) < 256
        short_title_valid = len(short_title) < 17
        color_rules = '^#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$'
        color_valid = bool(re.match(color_rules, color))
        result = title_valid and short_title_valid and color_valid
        return result

    @staticmethod
    def update_tube(id: int, title: str, short_title: str, color: str):
        tube_valid = Tubes.check_tube(title, short_title, color)
        if not tube_valid:
            return {"ok": False, "message": "Валидация не пройдена"}
        tube = Tubes.objects.filter(pk=id).first()
        if not tube:
            return {"ok": False, "message": "Такой ёмкости нет"}
        tube.title = title
        tube.short_title = short_title
        tube.color = color
        tube.save()
        return {"ok": True, "message": ""}

    @staticmethod
    def create_tube(title: str, short_title: str, color: str):
        tube_valid = Tubes.check_tube(title, short_title, color)
        if not tube_valid:
            return {"ok": False, "message": "Валидация не пройдена"}
        tube = Tubes(title=title, short_title=short_title, color=color)
        tube.save()
        return {"ok": True, "message": "", "data": tube.pk}

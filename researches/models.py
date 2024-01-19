import re
import sys

from django.db import models

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


class Tubes(models.Model):
    """Таблица типов пробирок"""

    id = models.AutoField(primary_key=True, db_index=True)
    color = models.CharField(max_length=7)  # Цвет в CSS формате (#1122FF)
    title = models.CharField(max_length=255)  # Название
    short_title = models.CharField(max_length=6, default="", blank=True)
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
    def get_all():
        result = [
            {
                "id": tube.pk,
                "label": tube.title,
                "color": tube.color,
            }
            for tube in Tubes.objects.all()
        ]
        return result

    class Meta:
        verbose_name = 'Вид ёмкости'
        verbose_name_plural = 'Виды ёмкостей'

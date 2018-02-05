import sys

import re
from django.db import models

TESTING = 'test' in sys.argv[1:] or 'jenkins' in sys.argv[1:]


class Tubes(models.Model):
    """Таблица типов пробирок"""
    id = models.AutoField(primary_key=True, db_index=True)
    color = models.CharField(max_length=7)  # Цвет в CSS формате (#1122FF)
    title = models.CharField(max_length=255)  # Название
    short_title = models.CharField(max_length=6, default="", blank=True)

    def __str__(self):
        return self.title

    def get_short_title(self):
        pr = self.short_title
        if pr == "":
            types = ["фиолет", "красн", "стекло", "черн", "белая", "серая", "фильтро", "чашка", "голубая", "зеленая",
                     "желтая", "жёлтая",
                     "зелёная", "контейнер", "зонд", "п ф", "л ф", "синяя"]
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

    class Meta:
        verbose_name = 'Вид пробирки'
        verbose_name_plural = 'Виды пробирок'

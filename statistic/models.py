from django.db import models

import directory.models as directory
import slog.models as slog
import users.models as users
from laboratory.utils import localtime


class Uet(models.Model):
    user = models.ForeignKey(users.DoctorProfile, db_index=True, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, blank=True, db_index=True)
    points = models.FloatField()

    @property
    def date_local(self):
        return localtime(self.date)

    @staticmethod
    def add(user: users.DoctorProfile, research: directory.Researches, direction: int):
        isdoc = True
        # isdoc = user.labtype == 1
        pts = sum([x.uet_doc if isdoc else x.uet_lab for x in directory.Fractions.objects.filter(research__pk=research.pk)])
        if pts > 0:
            row = Uet(user=user, points=pts)
            row.save()
        slog.Log(key=str(direction), type=26, body=str(pts), user=user).save()

    def __str__(self):
        return "%s %s +%s" % (str(self.user), self.date_local, self.points)


class TypeReport(models.Model):
    title = models.CharField(max_length=255, help_text="Тип отчета")
    hide = models.BooleanField(default=False, blank=True, help_text="Скрыть", db_index=True)
    code = models.CharField(max_length=255, unique=True, default=None, blank=True, null=True, help_text="Служебный код")
    title_report_used = models.CharField(max_length=255, default=None, blank=True, null=True, help_text="Отчет, в котором применяется")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тип отчета для статистики"
        verbose_name_plural = "Типы отчетов для статистики"

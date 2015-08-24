from django.db import models
from django.contrib.auth.models import User
from podrazdeleniya.models import Podrazdeleniya


class DoctorProfile(models.Model):  # Профили врачей
    labtypes = (
        (0, "Не из лаборатории"),
        (1, "Врач"),
        (2, "Лаборант"),
    )
    user = models.OneToOneField(User, null=True, blank=True)  # Ссылка на Django-аккаунт
    fio = models.CharField(max_length=255)  # ФИО
    podrazileniye = models.ForeignKey(Podrazdeleniya, null=True, blank=True)  # Подразделение
    isLDAP_user = models.BooleanField(default=False,
                                      blank=True)  # Флаг, показывающий, что это импортированый из LDAP пользователь
    labtype = models.IntegerField(choices=labtypes, default=0, blank=True)

    def get_fio(self):  # Функция формирования фамилии и инициалов (Иванов И.И.)
        return self.fio.split(" ")[0] + " " + self.fio.split(" ")[1][0] + "." + self.fio.split(" ")[2][0] + "."

    def __str__(self):  # Получение фио при конвертации объекта DoctorProfile в строку
        if self.podrazileniye:
            return self.fio + ', ' + self.podrazileniye.title
        else:
            return self.fio

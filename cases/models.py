from django.db import models
import clients.models as clients
import users.models as users
from laboratory.utils import localtime


class Case(models.Model):
    POLY_CASE = 0
    URGENT_CASE = 1
    HOSP_CASE = 2

    CASE_TYPES = (
        (POLY_CASE, 'Поликлиническое обслуживание'),
        (URGENT_CASE, 'Неотложная помощь'),
        (HOSP_CASE, 'Госпитализация'),
    )

    CARE_TYPES = (
        (0, 'Специализированная'),
        (1, 'Скорая'),
        (2, 'Первичная специализированная медико-санитарная'),
        (3, 'Первичная доврачебная медико-санитарная'),
        (4, 'Первичная врачебная медико-санитарная'),
        (5, 'Паллиативная'),
        (6, 'Высокотехнологичная'),
    )

    CASE_REGIMENS = (
        (0, 'Амбулаторно'),
        (1, 'Скорая МП'),
        (2, 'Стационар дневной'),
        (3, 'Стационар круглосуточный'),
    )

    CASE_REGIMENS_REL = {
        POLY_CASE: [0, 1],
        URGENT_CASE: [0, 1],
        HOSP_CASE: [2, 3],
    }

    card = models.ForeignKey(clients.Card, on_delete=models.CASCADE, help_text='Карта пациента')
    doctor = models.ForeignKey(users.DoctorProfile, on_delete=models.CASCADE, help_text='Врач', related_name='case_doc_closed')
    creator = models.ForeignKey(users.DoctorProfile, on_delete=models.CASCADE, help_text='Создатель случая', related_name='case_creator')
    opened = models.DateTimeField(help_text='Дата и время открытия случая')
    closed = models.DateTimeField(blank=True, null=True, default=None, help_text='Дата и время закрытия случая')
    cancel = models.BooleanField(blank=True, default=False, help_text='Отмена случая')
    case_type = models.SmallIntegerField(choices=CASE_TYPES, help_text='Вид случая')  # DEPRECATED
    case_regimen = models.SmallIntegerField(choices=CASE_REGIMENS, help_text='Условия оказания помощи')  # DEPRECATED
    care_type = models.SmallIntegerField(choices=CARE_TYPES, help_text='Вид медицинской помощи')  # DEPRECATED

    @property
    def opened_local(self):
        return localtime(self.opened)

    @property
    def closed_local(self):
        return localtime(self.closed)

    def __str__(self):
        return "Случай №{}. Карта: {}. Открыт: {:%d.%m.%Y %H:%M}, закрыт: {:%d.%m.%Y %H:%M}. " "Врач: {}. Отмена: {}".format(
            self.pk, self.card, self.opened_local, self.closed_local, self.doctor, self.cancel
        )

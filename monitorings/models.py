from django.db import models

# import directory.models as directory
from directions.models import Issledovaniya
from directory.models import MonitoringParams, ParaclinicInputField
from hospitals.models import Hospitals
from users.models import DoctorProfile
# from directory.models import ParaclinicInputField


# class MonitoringGroup(models.Model):
#     title = models.CharField(max_length=400, help_text='Название группы мониторинга')
#     short_title = models.CharField(max_length=255, default='', blank=True)
#     hide = models.BooleanField()
#
#     class Meta:
#         verbose_name = 'Мониторинг - Группы'
#         verbose_name_plural = 'Мониторинг-Группа'
#
#
# class MonitoringParams(models.Model):
#     title = models.CharField(max_length=255, default="", help_text='Название параметра', db_index=True)
#     short_title = models.CharField(max_length=255, default='', blank=True)
#     group = models.ForeignKey(MonitoringGroup, on_delete=models.CASCADE)
#     hide = models.BooleanField()
#
#     class Meta:
#         verbose_name = 'Мониторинг - Параметры'
#         verbose_name_plural = 'Мониторинг-параметр'


class MonitoringResult(models.Model):
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Заказ на мониторинг, для которого сохранен результат', on_delete=models.CASCADE)
    monitoring_params = models.ForeignKey(MonitoringParams, db_index=True, help_text='Параметр мониторинга', on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospitals, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    doc_confirmation = models.ForeignKey(
        DoctorProfile, null=True, blank=True, related_name="doc_confirmation", db_index=True, help_text='Профиль пользователя, подтвердившего результат', on_delete=models.SET_NULL
    )
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')
    field = models.ForeignKey(ParaclinicInputField, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=ParaclinicInputField.TYPES, null=True)
    value_aggregate = models.IntegerField()
    value_text = models.TextField()

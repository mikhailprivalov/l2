from django.db import models

from directions.models import Issledovaniya, Napravleniya
from directory.models import ParaclinicInputField, Researches, ParaclinicInputGroups, Localization
from hospitals.models import Hospitals
from laboratory.utils import current_time
from users.models import DoctorProfile


class MonitoringResult(models.Model):
    PERIOD_HOUR = 'PERIOD_HOUR'
    PERIOD_DAY = 'PERIOD_DAY'
    PERIOD_WEEK = 'PERIOD_WEEK'
    PERIOD_MONTH = 'PERIOD_MONTH'
    PERIOD_QURTER = 'PERIOD_QURTER'
    PERIOD_HALFYEAR = 'PERIOD_HALFYEAR'
    PERIOD_YEAR = 'PERIOD_YEAR'

    PERIOD_TYPES = (
        (PERIOD_HOUR, 'Час'),
        (PERIOD_DAY, 'День'),
        (PERIOD_WEEK, 'Неделя'),
        (PERIOD_MONTH, 'Месяц'),
        (PERIOD_QURTER, 'Квартал'),
        (PERIOD_HALFYEAR, 'Полгода'),
        (PERIOD_YEAR, 'Год'),
    )

    napravleniye = models.ForeignKey(Napravleniya, null=True, help_text='Направление', db_index=True, on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания направления', db_index=True)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид мониторинга/исследования из справочника', db_index=True, on_delete=models.CASCADE)
    issledovaniye = models.ForeignKey(Issledovaniya, db_index=True, help_text='Заказ на мониторинг, для которого сохранен результат', on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospitals, default=None, blank=True, null=True, on_delete=models.SET_NULL)
    doc_confirmation = models.ForeignKey(
        DoctorProfile, null=True, blank=True, db_index=True, help_text='Профиль пользователя, подтвердившего результат', on_delete=models.SET_NULL
    )
    doc_confirmation_string = models.CharField(max_length=64, null=True, blank=True, default=None)
    time_confirmation = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Время подтверждения результата')
    monitoring_group = models.ForeignKey(ParaclinicInputGroups, default=None, blank=True, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field = models.ForeignKey(ParaclinicInputField, db_index=True, help_text='Поле результата', on_delete=models.CASCADE)
    field_type = models.SmallIntegerField(default=None, blank=True, choices=ParaclinicInputField.TYPES, null=True)
    value_aggregate = models.IntegerField()
    value_text = models.TextField()
    type_period = models.CharField(max_length=20, null=True, blank=True, default=None, db_index=True, choices=PERIOD_TYPES, help_text="Тип периода")
    period_param_hour = models.PositiveSmallIntegerField(default=None, blank=True)
    period_param_day = models.PositiveSmallIntegerField(default=None, blank=True)
    period_param_month = models.PositiveSmallIntegerField(default=None, blank=True)
    period_param_quarter  = models.PositiveSmallIntegerField(default=None, blank=True)
    period_param_halfyear  = models.PositiveSmallIntegerField(default=None, blank=True)
    period_year = models.PositiveSmallIntegerField(default=None, blank=True)

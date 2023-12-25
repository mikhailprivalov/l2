import math
from typing import Union
import uuid

from django.db import models
from users.models import DoctorProfile

import directory.models as directory_models


class Application(models.Model):
    """
    Модель rest приложений для безопасного доступа по ключам
    """

    PLACES_FRACTION = 'fraction'
    PLACES_APP = 'app'
    PLACES_BOTH_MIN = 'both-min'
    PLACES_BOTH_MAX = 'both-max'
    PLACES_AS_IS = 'as-is'
    PLACES = (
        (PLACES_FRACTION, 'Брать из RelationFractionASTM.signs_after_point'),
        (PLACES_APP, 'Брать из Application.decimal_places'),
        (PLACES_BOTH_MIN, 'Брать минимальное между RelationFractionASTM.signs_after_point и Application.decimal_places'),
        (PLACES_BOTH_MAX, 'Брать максимальное между RelationFractionASTM.signs_after_point и Application.decimal_places'),
        (PLACES_AS_IS, 'Не модифицировать'),
    )

    key = models.UUIDField(default=uuid.uuid4, editable=False, help_text="UUID, генерируется автоматически", db_index=True)
    name = models.CharField(max_length=255, help_text="Название приложения")
    active = models.BooleanField(default=True, help_text="Флаг активности")
    direction_work = models.BooleanField(default=False, help_text="Работа с номерами, пришедшими с анализатора как с номерами направлений")
    decimal_places = models.PositiveIntegerField(default=4)
    places_type = models.CharField(max_length=10, default=PLACES_FRACTION, choices=PLACES)
    hospitals = models.ManyToManyField('hospitals.Hospitals', blank=True)
    companies = models.ManyToManyField('contracts.Company', blank=True)
    is_superuser = False
    tube_work = models.BooleanField(default=False, help_text="Работа с номерами, пришедшими с анализатора как с номерами пробирок")
    can_access_schedule = models.BooleanField(default=False, help_text="У приложения есть доступ к расписанию")
    csv_header = models.CharField(max_length=255, blank=True, null=True, help_text="Заголовок CSV файла")
    is_background_worker = models.BooleanField(default=False)
    unlimited_access = models.BooleanField(default=False, help_text="Доступ без ограничений")
    can_load_file_result = models.BooleanField(default=False, help_text="Результаты загружаются файлом")

    def auto_set_places(self, rel: "RelationFractionASTM", value: Union[str, float, int]) -> str:
        if rel.full_round:
            return str(round(value))
        if self.places_type != Application.PLACES_AS_IS:
            if self.places_type == Application.PLACES_FRACTION and rel.signs_after_point:
                return f'{value:.{rel.signs_after_point}f}'.rstrip('0').rstrip('.')
            elif self.places_type == Application.PLACES_APP or (self.places_type == Application.PLACES_FRACTION and not rel.signs_after_point):
                return f'{value:.{self.decimal_places}f}'.rstrip('0').rstrip('.')
            elif self.places_type == Application.PLACES_BOTH_MIN:
                return f'{value:.{min(self.decimal_places, rel.signs_after_point or self.decimal_places)}f}'.rstrip('0').rstrip('.')
            elif self.places_type == Application.PLACES_BOTH_MAX:
                return f'{value:.{max(self.decimal_places, rel.signs_after_point or self.decimal_places)}f}'.rstrip('0').rstrip('.')
        return value

    @property
    def is_authenticated(self):
        return self.active

    @property
    def username(self):
        return 'API: ' + self.name

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Приложение API'
        verbose_name_plural = 'Приложения API'

    def get_issledovaniya(self, pk):
        r = []
        from directions.models import TubesRegistration, Issledovaniya

        for ps in pk:
            d = self.direction_work
            p = ps
            if p >= 4600000000000:
                d = True
                p -= 4600000000000
                p //= 10

            if d:
                t_filter = dict(issledovaniya__napravleniye__pk=p)
            else:
                t_filter = dict(number=p)
            tubes = TubesRegistration.objects.filter(**t_filter)
            for i in Issledovaniya.objects.filter(tubes__in=tubes, time_confirmation__isnull=True):
                r.append({"pk": ps, "iss": i})
        return r

    def truncate(self, f):
        return math.floor(f * 10**self.decimal_places) / 10**self.decimal_places


class RelationFractionASTM(models.Model):
    """
    Модель соответствия фракций из ASTM для LIS
    """

    MULTIPLIERS = ((0, 1), (1, 10), (2, 100), (3, 1000), (4, 1.9), (5, 2.2), (6, 2.5), (7, 0.1), (8, 0.01), (9, 0.001))
    astm_field = models.CharField(max_length=127, help_text="ASTM-поле", db_index=True)
    fraction = models.ForeignKey(directory_models.Fractions, help_text="Фракция", on_delete=models.CASCADE)
    multiplier = models.IntegerField(choices=MULTIPLIERS, default=0, help_text="Множитель результата")
    default_ref = models.ForeignKey(directory_models.References, help_text="Референс для сохранения через API", default=None, blank=True, null=True, on_delete=models.CASCADE)
    full_round = models.BooleanField(default=False, blank=True, help_text="Округлять весь результат?")
    analyzer = models.ManyToManyField('api.Analyzer', help_text="Анализаторы", blank=True, default=None)
    application_api = models.ManyToManyField('api.Application', help_text="Приложение API", blank=True, default=None)
    is_code = models.BooleanField(default=False, help_text="astm_field - это код (id)?")
    signs_after_point = models.IntegerField(default=None, null=True, blank=True, help_text="Количество знаков после запятой")
    replace_value = models.TextField(max_length=500, default=None, null=True, blank=True, help_text="подмена пришедших значений на др - анг->рус")

    def __str__(self):
        return self.astm_field + " to \"" + self.fraction.research.title + "." + self.fraction.title + "\" x " + str(self.get_multiplier_display())

    class Meta:
        verbose_name = 'Связь ASTM и фракций'
        verbose_name_plural = 'Связи ASTM и фракций'


class Analyzer(models.Model):
    PROTOCOLS = ((0, "ASTM 1394-97"), (1, "HL7 2.5"))
    MODES = ((0, "TCP Connection"),)

    title = models.CharField(max_length=60, help_text="Название")
    port = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Номер порта анализатора")
    service_name = models.CharField(max_length=60, help_text="Название службы Systemd", null=True, blank=True)
    protocol = models.IntegerField(choices=PROTOCOLS, help_text="Поддерживаемый протокол")
    mode = models.IntegerField(choices=MODES, help_text="Режим")
    connection_string = models.TextField(help_text="Строка подключения")
    applications = models.ManyToManyField(Application, help_text="Приложения анализатора", blank=True, default=None)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Анализатор'
        verbose_name_plural = 'Анализаторы'


class ManageDoctorProfileAnalyzer(models.Model):
    doctor_profile = models.ForeignKey(DoctorProfile, help_text="Пользователь, который принадлежит к этому анализатору", on_delete=models.CASCADE)
    analyzer = models.ForeignKey(Analyzer, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.doctor_profile} — {self.analyzer}"

    class Meta:
        verbose_name = 'Управление анализатором'
        verbose_name_plural = 'Управление анализаторами'


class RelationCultureASTM(models.Model):
    """
    Модель соответствия фракций из ASTM для LIS
    """

    astm_field = models.CharField(max_length=127, help_text="ASTM-поле", db_index=True)
    culture = models.ForeignKey(directory_models.Culture, help_text="Культура", on_delete=models.CASCADE)

    def __str__(self):
        return self.astm_field + " to \"" + self.culture.title

    class Meta:
        verbose_name = 'Связь ASTM и культур'
        verbose_name_plural = 'Связи ASTM и культур'

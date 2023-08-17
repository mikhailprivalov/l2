from django.db import models
from jsonfield import JSONField


class Dashboard(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название дашборда', db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие дашборда', db_index=True)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)
    interval_reload_seconds = models.SmallIntegerField(default=None, blank=True, null=True, help_text='Частота обновления дашборда в секундах')

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Дашборд'
        verbose_name_plural = 'Дашборды'


class DatabaseConnectSettings(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название', db_index=True)
    login = models.CharField(max_length=255, default="", help_text='Логин', db_index=True)
    password = models.CharField(max_length=255, default="", help_text='Пароль', db_index=True)
    database = models.CharField(max_length=255, default="", help_text='Название базы', db_index=True)
    ip_address = models.CharField(max_length=255, default="", help_text='ip-address', db_index=True)
    port = models.CharField(max_length=5, default="", help_text='Порт', db_index=False)
    driver = models.CharField(max_length=128, default="", help_text='Драйвер', db_index=False)
    encrypt = models.CharField(max_length=5, default="", help_text='Шифрование', db_index=False)

    def __str__(self):
        return f"{self.title} - {self.database}"

    class Meta:
        verbose_name = 'Подключение к БД'
        verbose_name_plural = 'Подключения к БД'


class DashboardCharts(models.Model):
    COLUMN = 'COLUMN'
    BAR = 'BAR'
    PIE = 'PIE'
    LINE = 'LINE'
    TABLE = 'TABLE'

    DEFAULT_TYPE = (
        (COLUMN, 'Столбцы'),
        (BAR, 'Полоса'),
        (PIE, 'Пирог-куски'),
        (LINE, 'Линейная диаграмма'),
        (TABLE, 'Таблица'),
    )

    title = models.CharField(max_length=255, default="", help_text='Название графика', db_index=True)
    dashboard = models.ForeignKey(Dashboard, null=True, help_text='Дашборд', db_index=True, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие графика', db_index=True)
    is_full_width = models.BooleanField(default=False, blank=True, help_text='На всю ширину страницы')
    default_type = models.CharField(max_length=20, db_index=True, choices=DEFAULT_TYPE, default=COLUMN, help_text="Тип графика по умолчанию")

    def __str__(self):
        return f"({self.dashboard.title}) - {self.title}"

    class Meta:
        verbose_name = 'График'
        verbose_name_plural = 'Графики'


class DashboardDataSet(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название набора данных')
    connect = models.ForeignKey(DatabaseConnectSettings, null=True, help_text='База данных', on_delete=models.CASCADE)
    sql_query = models.TextField(default="", help_text='SQL-запрос')
    sql_columns_settings = JSONField(default=dict, help_text="{sql-название: {синоним: название, x:true}, sql-название: {синоним: название, x:false}")

    def __str__(self):
        return f"{self.title} {self.sql_columns_settings}"

    class Meta:
        verbose_name = 'Набор данных по координатам'
        verbose_name_plural = 'Наборы данных по координатам'


class DashboardChartData(models.Model):
    chart = models.ForeignKey(DashboardCharts, null=True, help_text='График', db_index=True, on_delete=models.CASCADE)
    data_set = models.ForeignKey(DashboardDataSet, null=True, help_text='Набор даннах', db_index=True, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие набора', db_index=True)

    def __str__(self):
        return f"{self.chart.title}"

    class Meta:
        verbose_name = 'График + набор данных'
        verbose_name_plural = 'Графики + набор данных'

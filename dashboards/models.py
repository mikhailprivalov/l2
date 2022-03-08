from django.db import models


class Dashboard(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название дашборда', db_index=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие дашборда', db_index=True)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = 'Дашборд'
        verbose_name_plural = 'Дашборды'


class DatabaseConnectSettings(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название', db_index=True)
    login = models.CharField(max_length=255, default="", help_text='Логин', db_index=True)
    password = models.CharField(max_length=255, default="", help_text='Пароль', db_index=True)
    name_database = models.CharField(max_length=255, default="", help_text='Название базы', db_index=True)
    ip_address = models.CharField(max_length=255, default="", help_text='ip-address', db_index=True)
    port = models.CharField(max_length=5, default="", help_text='Порт', db_index=False)

    def __str__(self):
        return f"{self.title} - {self.name_database}"

    class Meta:
        verbose_name = 'Дашборд-подключения к БД'
        verbose_name_plural = 'Дашборд-подключения к БД'


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
        return f"{self.title} - Дашборд: {self.dashboard.title}"

    class Meta:
        verbose_name = 'Дашборд-Графики'
        verbose_name_plural = 'Дашборд-Графики'


class DashboardDataSet(models.Model):
    title = models.CharField(max_length=255, default="", help_text='Название набора данных', db_index=True)
    connect = models.ForeignKey(DatabaseConnectSettings, null=True, help_text='База данных', db_index=True, on_delete=models.CASCADE)
    sql_query = models.CharField(max_length=1255, default="", help_text='SQL-запрос', db_index=True)
    return_param_coord = models.JSONField(default={}, help_text="{x: {sql-название:синоним}, y: {sql-название:синоним}")

    def __str__(self):
        return f"{self.return_param_coord}"

    class Meta:
        verbose_name = 'Дашборд-набор данных по координатам'
        verbose_name_plural = 'Дашборд-набор данных по координатам'


class DashboardChartData(models.Model):
    charts = models.ForeignKey(DashboardCharts, null=True, help_text='График', db_index=True, on_delete=models.CASCADE)
    data_set = models.ForeignKey(DashboardDataSet, null=True, help_text='Набор даннах', db_index=True, on_delete=models.CASCADE)
    order = models.SmallIntegerField(default=-99, blank=True, null=True)
    hide = models.BooleanField(default=False, blank=True, help_text='Скрытие набора', db_index=True)

    def __str__(self):
        return f"{self.charts.title}"

    class Meta:
        verbose_name = 'Дашборд-график набор данных'
        verbose_name_plural = 'Дашборд-график набор данных'

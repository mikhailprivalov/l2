import simplejson
from django.db import models

from laboratory.utils import localtime
from users.models import DoctorProfile


class Log(models.Model):
    TYPES = (
        (0, 'Другое'),
        (1, 'Справочник: добавлена ёмкость'),
        (2, 'Справочник: изменена ёмкость'),
        (3, 'Справочник: добавлен анализ'),
        (4, 'Справочник: изменен анализ'),
        (20, 'Справочник: добавлено отношение ёмкости к фракции'),
        (19, 'Справочник: скрытие/показ анализа'),
        (5, 'Справочник: добавлена группа направления'),
        (6, 'Справочник: изменена группа направления'),
        (21, 'Направления: созданы направления'),
        (5000, 'Направления: просмотр истории направления'),
        (5001, 'Направления: отметка посещения'),
        (5002, 'Направления: отмена'),
        (5003, 'Направления: смена главного направления'),
        (9, 'Забор материала: ёмкость взята'),
        (10, 'Забор материала: напечатан акт приёма-передачи'),
        (11, 'Приём материала: материал принят'),
        (12, 'Приём материала: материал не принят'),
        (4000, 'Приём материала: замечание приёма было очищено'),
        (25, 'Приём материала: печать журнала приема'),
        (13, 'Ввод результатов: результат сохранен'),
        (14, 'Ввод результатов: результат подтвержден'),
        (15, 'Ввод результатов: результаты для направления напечатаны'),
        (24, 'Ввод результатов: подтверждение сброшено'),
        (26, 'Ввод результатов: присвоение УЕТов'),
        (28, 'Ввод результатов: печать журнала-таблицы'),
        (16, 'Администрирование: создан пользователь'),
        (17, 'Администрирование: создано подразделение'),
        (18, 'Пользователи: вход пользователя'),
        (27, 'Поиск: поиск'),
        (22, 'API: результат сохранен'),
        (23, 'API: ёмкость не найдена'),
        (6000, 'API: сообщение с сервера интеграции анализаторов'),
        (100, 'Статистика: statistic_xls'),
        (101, 'Статистика: statistic_xls – слишком большой диапазон'),
        (998, 'Подозрительное действие: печать результатов другого врача и/или отделения и/или лаборатории'),
        (999, 'Подозрительное действие: печать результатов другого отделения'),
        (1000, 'Выписки: загрузка выписки'),
        (1001, 'Выписки: поиск'),
        (2000, 'Импорт пациентов: добавление Individual в базу'),
        (2001, 'Импорт пациентов: добавление карты пациента в базу'),
        (2002, 'Импорт пациентов: объединение физ.лиц по документу'),
        (2003, 'Импорт пациентов: обновление данных из РМИС'),
        (2004, 'Импорт пациентов: отправка карты в архив'),
        (2005, 'Импорт пациентов: удаление архивной карты без направлений'),
        (2006, 'Импорт пациентов: удаление физлица без карт'),
        (3001, 'РМИС: повторная отправка направлений'),
        (3000, 'РМИС: повторная отправка результатов'),
        (7000, 'Статталоны: создание'),
        (7001, 'Статталоны: отмена/возврат'),
        (10000, 'Конструктор: создание или редактирование исследования'),
        (20000, 'Отчёт по результатам: загрузка данных'),
        (30000, 'Картотека: создание карты'),
        (30001, 'Картотека: редактирование карты'),
        (30002, 'Картотека: создание документа'),
        (30003, 'Картотека: редактирование документа'),
        (30004, 'Картотека: установка активного документа карты'),
        (30005, 'Картотека: изменение представителя'),
        (30006, 'Картотека: установка активного представителя'),
        (30007, 'Картотека: обновление полей карты'),
        (30008, 'Картотека: обновление полей документа'),
        (30009, 'Картотека: обновление использования документа картой'),
        (30010, 'Картотека: обновление данных физлица'),
        (40000, 'Д-учёт: создание записи'),
        (40001, 'Д-учёт: редактирование записи'),
        (50000, 'Льготы: создание записи'),
        (50001, 'Льготы: редактирование записи'),
        (60000, 'Выгрузка в АМД: успешно'),
        (60001, 'Выгрузка в АМД: не успешно'),
        (60002, 'Выгрузка в N3: успешно'),
        (60003, 'Выгрузка в N3: не успешно'),
        (60004, 'Выгрузка в L2.Core: успешно'),
        (60005, 'Выгрузка в L2.Core: не успешно'),
        (60006, 'Выгрузка в CRIE: установка статуса'),
        (60007, 'Выгрузка в N3.ОДЛИ: успешно'),
        (60008, 'Выгрузка в N3.ОДЛИ: не успешно'),
        (60009, 'Выгрузка в N3.ИЭМК: успешно'),
        (60010, 'Выгрузка в N3.ИЭМК: не успешно'),
        (60011, 'Выгрузка в N3.ИЭМК: успешное обновление'),
        (60012, 'Выгрузка в N3.ОДИИ: результат по заявке с протоколом — успешно'),
        (60013, 'Выгрузка в N3.ОДИИ: результат по заявке с протоколом — не успешно'),
        (60014, 'Выгрузка в N3.ОДИИ: снимок по заявке без протокола — успешно'),
        (60015, 'Выгрузка в N3.ОДИИ: снимок по заявке без протокола — не успешно'),
        (60016, 'Выгрузка в N3.ОДИИ: запрос ACSN — успешно'),
        (60017, 'Выгрузка в N3.ОДИИ: запрос ACSN — не успешно'),
        (60018, 'Выгрузка в N3.ОДИИ: результат по заявке без снимка — успешно'),
        (60019, 'Выгрузка в N3.ОДИИ: результат по заявке без снимка — не успешно'),
        (60020, 'Выгрузка в VI: успешно'),
        (60021, 'Выгрузка в VI: не успешно'),
        (60022, 'Выгрузка в ECP: успешно'),
        (60023, 'Выгрузка в ECP: не успешно'),
        (60024, 'Выгрузка в РЭМД: не успешно'),
        (60025, 'Выгрузка в РЭМД: не успешно'),
        (70000, 'Вакцинация: создание записи'),
        (70001, 'Вакцинация: редактирование записи'),
        (80001, 'План операций: создание записи'),
        (80002, 'План операций: редактирование записи'),
        (80003, 'Вызов врача: создание записи'),
        (80004, 'Вызов врача: отмена записи'),
        (80005, 'Лист ожидания: создание записи'),
        (80006, 'Лист ожидания: отмена записи'),
        (80007, 'План госпитализации: cоздание записи'),
        (80008, 'План госпитализации: изменение статуса'),
        (80009, 'Лимиты план госпитализации'),
        (90000, 'L2.Core: Приём результатов'),
        (100000, 'Стационар: Смена отделения'),
        (110000, 'Настройка организации: данные организации'),
        (110001, 'Настройка организации: добавление генератора номеров'),
        (120000, 'Профили пользователей: сброс пароля'),
        (120001, 'Профили пользователей: смена email'),
        (121000, 'Профили пользователей: забыл пароль — запрос кода'),
        (121001, 'Профили пользователей: забыл пароль — отправка нового пароля'),
        (121100, 'Сотрудники: добавление подразделения'),
        (121101, 'Сотрудники: обновление подразделения'),
        (121102, 'Сотрудники: добавление должности'),
        (121103, 'Сотрудники: обновление должности'),
        (121104, 'Сотрудники: добавление сотрудника'),
        (121105, 'Сотрудники: обновление сотрудника'),
        (121106, 'Сотрудники: добавление должности сотрудника'),
        (121107, 'Сотрудники: обновление должности сотрудника'),
        (122000, 'Гистология: регистрация материала гистологии'),
        (122001, 'Гистология: api-приём направлений'),
        (130000, 'Настройка прайсов: изменение цены'),
        (130001, 'Настройка прайсов: удаление цены'),
        (130002, 'Настройка компаний: изменение компании'),
        (130003, 'Настройка компаний: добавление компании'),
        (130004, 'Настройка компаний: добавление отдела'),
        (130005, 'Настройка компаний: изменение отдела'),
        (130006, 'Настройка прайсов: изменение прайса'),
        (130007, 'Настройка прайсов: добавление прайса'),
        (140000, 'Email: отправка результатов'),
        (140001, 'ECP: удаление записи пациента'),
        (150000, 'Факторы вредности: изменение фактора'),
        (150001, 'Факторы вредности: добавление фактора'),
        (160000, 'Параметры пациентов: изменение параметра'),
        (160001, 'Параметры пациентов: добавление параметра'),
        (170000, 'Наборы исследований: Добавление исследования'),
        (170001, 'Наборы исследований: Добавление набора'),
        (170002, 'Наборы исследований: Изменение набора'),
        (180000, 'Отправка результатов пациенту: запланировано'),
        (180001, 'Отправка результатов пациенту: отправлено'),
        (180002, 'Отправка результатов пациенту: неудачно'),
        (180003, 'Отправка результатов пациенту: отмена'),
    )

    # Виды событий, которые могут быть очищены
    CLEANUP_TYPES_LOG = (
        1,
        2,
        3,
        4,
        5,
        6,
        10,
        16,
        17,
        18,
        19,
        20,
        25,
        27,
        22,
        23,
        100,
        998,
        999,
        1001,
        2000,
        2001,
        2002,
        2003,
        2004,
        2005,
        2006,
        3000,
        3001,
        5000,
        6000,
        10000,
        20000,
        60001,
        60003,
    )

    key = models.CharField(max_length=2047)
    type = models.IntegerField(choices=TYPES)
    body = models.TextField()
    user = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, blank=True, null=True)
    time = models.DateTimeField(auto_now=True)

    @property
    def time_local(self):
        return localtime(self.time)

    @staticmethod
    def log(key, type, user=None, body=None):
        Log(key=key, type=type, body=simplejson.dumps(body), user=user).save()

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

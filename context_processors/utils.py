import simplejson
import simplejson as json

from django.core.cache import cache
import clients.models as Clients
from appconf.manager import SettingManager
from laboratory import settings
from laboratory.settings import PROTOCOL_PLAIN_TEXT, SPLIT_PRINT_RESULT
from rmis_integration.client import get_md5
from utils.common import get_system_name


def card_bases(request):
    card_bases_vars = []
    for b in Clients.CardBase.objects.filter(hide=False).order_by("pk"):
        card_bases_vars.append(dict(title=b.title, code=b.short_title, pk=b.pk, history_number=b.history_number))
    return {"card_bases": json.dumps(card_bases_vars)}


def local_settings(request):
    return {"SYSTEM_AS_VI": settings.SYSTEM_AS_VI, "PROTOCOL_PLAIN_TEXT": PROTOCOL_PLAIN_TEXT, "SPLIT_PRINT_RESULT": SPLIT_PRINT_RESULT}


def ws(request):
    return {"ws_url": json.dumps(settings.WS_URL), "ws_enabled": json.dumps(settings.WS_ENABLED)}


def menu(request):
    from laboratory import VERSION

    data = []
    if request.user.is_authenticated and not request.is_ajax():
        groups = [str(x) for x in request.user.groups.all()] if hasattr(request.user, 'groups') else []

        k = f'menu:{VERSION}:{get_md5(";".join(groups))}'
        data = cache.get(k)
        if not data:
            pages = [
                {"url": "/ui/menu", "title": f"Меню {get_system_name()}", "nt": False, "access": ["*"], "not_show_home": True},
                {"url": "/logout", "title": "Выход из профиля", "nt": False, "access": ["*"], "not_show_home": True},
                {"hr": True, "access": ["*"]},
                {
                    "url": "/ui/directions",
                    "title": "Направления и картотека",
                    "nt": False,
                    "access": ["Лечащий врач", "Врач-лаборант", "Оператор лечащего врача", "Оператор Контакт-центра", "Свидетельство о смерти-доступ"],
                },
                {
                    "url": "/mainmenu/direction/info",
                    "title": "История направления",
                    "nt": False,
                    "access": ["Лечащий врач", "Врач-лаборант", "Оператор лечащего врача", "Лаборант", "Врач-лаборант", "Просмотр журнала", "Свидетельство о смерти-доступ"],
                },
                {"url": "/mainmenu/directions/multiprint", "title": "Печать направлений", "nt": False, "access": ["Лечащий врач", "Врач-лаборант", "Оператор лечащего врача"]},
                {"url": "/ui/results-by-department-or-doctor", "title": "Печать по отделению или врачу", "nt": False, "access": ["Лечащий врач", "Оператор лечащего врача"]},
                {"url": "/ui/biomaterial/get", "title": "Забор биоматериала", "nt": False, "access": ["Заборщик биоматериала"]},
                {"url": "/mainmenu/receive", "title": "Приём биоматериала", "nt": False, "access": ["Получатель биоматериала"]},
                {"url": "/mainmenu/statistics-tickets", "title": "Статталоны", "nt": False, "access": ["Оформление статталонов", "Лечащий врач", "Оператор лечащего врача"]},
                {"url": "/mainmenu/receive/one_by_one", "title": "Приём биоматериала по одному", "nt": False, "access": ["Получатель биоматериала"]},
                {"url": "/mainmenu/receive/journal_form", "title": "Журнал приёма", "nt": False, "access": ["Получатель биоматериала"]},
                {"url": "/laboratory/results", "title": "Лабораторные результаты", "nt": False, "access": ["Врач-лаборант", "Лаборант", "Сброс подтверждений результатов"]},
                {
                    "url": "/mainmenu/employee-job",
                    "title": "Учёт косвенных услуг по лаборатории",
                    "nt": False,
                    "access": ["Врач-лаборант", "Лаборант", "Зав. лабораторией"],
                    "module": "l2_employee_job",
                },
                {
                    "url": "/ui/construct/menu",
                    "title": "Конструктор справочника",
                    "nt": False,
                    "access": [
                        "Конструктор: Лабораторные исследования",
                        "Конструктор: Параклинические (описательные) исследования",
                        "Конструктор: Консультации",
                        "Конструктор: Ёмкости для биоматериала",
                        "Конструктор: Настройка УЕТов",
                        "Конструктор: Группировка исследований по направлениям",
                        "Конструктор: Настройка скрининга",
                        "Конструктор: Настройка организации",
                    ],
                },
                {"url": "/ui/statistic", "title": "Статистика", "nt": False, "access": ["Просмотр статистики", "Врач-лаборант", 'Статистика скрининга']},
                {
                    "url": "/mainmenu/results_history",
                    "title": "Поиск",
                    "nt": False,
                    "access": ["Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант", "Врач параклиники", "Врач консультаций"],
                },
                {
                    "url": "/mainmenu/results_report",
                    "title": "Отчёт по результатам",
                    "nt": False,
                    "access": ["Лечащий врач", "Оператор лечащего врача", "Врач-лаборант", "Лаборант", "Врач параклиники", "Врач консультаций"],
                },
                {"url": "/mainmenu/discharge", "title": "Выписки", "nt": False, "access": ["Загрузка выписок", "Поиск выписок"], "module": "discharge_module"},
                {"url": "/mainmenu/create_podr", "title": "Управление подразделениями", "nt": False, "access": ["Создание и редактирование пользователей"]},
                {"url": "/mainmenu/profiles", "title": "Профили пользователей", "nt": False, "access": ["Создание и редактирование пользователей"]},
                {"url": "/mainmenu/view_log", "title": "Просмотр журнала", "nt": False, "access": ["Просмотр журнала"]},
                {"url": "/admin", "title": "Администрирование L2", "nt": False, "access": []},
                {
                    "url": "/mainmenu/direction_visit",
                    "title": "Регистрация направлений",
                    "nt": False,
                    "access": ["Посещения по направлениям", "Врач параклиники", "Врач консультаций", "Заборщик биоматериала микробиологии", "Получатель биоматериала микробиологии"],
                    "module": "paraclinic_module",
                },
                {
                    "url": "/ui/results/descriptive",
                    "title": "Ввод описательных результатов",
                    "nt": False,
                    "access": ["Врач параклиники", "Врач консультаций", "Свидетельство о смерти-доступ"],
                    "module": "paraclinic_module",
                },
                {"url": '/mainmenu/hosp', "title": "Госпитализация", "nt": True, "access": ["Госпитализация"], "module": "hosp_module"},
                {"url": '/mainmenu/stationar', "title": "Стационар", "nt": False, "access": ["Врач стационара", "t, ad, p"], "module": "l2_hosp"},
                {
                    "url": '/mainmenu/plan_operations',
                    "title": "План операций",
                    "nt": False,
                    "access": ["Врач стационара", "Лечащий врач", "Оператор лечащего врача", "Врач консультаций", "План операций"],
                    "module": "l2_hosp",
                },
                {"url": '/mainmenu/rmis_confirm', "title": "Подтверждение отправки результатов в РМИС", "nt": False, "access": ["Подтверждение отправки результатов в РМИС"]},
                {"url": '/mainmenu/list_wait', "title": "Листы ожидания", "nt": False, "access": ["Лечащий врач", "Оператор лечащего врача"], "module": "l2_list_wait"},
                {"url": '/mainmenu/doc_call', "title": "Вызовы врача и заявки", "nt": False, "access": ["Лечащий врач", "Оператор лечащего врача", "Вызов врача"], "module": "l2_doc_call"},
                {
                    "url": '/ui/extra-notification',
                    "title": "Экстренные извещения",
                    "nt": False,
                    "access": ["Лечащий врач", "Оператор лечащего врача", "Вызов врача", "Заполнение экстренных извещений"],
                    "module": "l2_extra_notifications",
                },
                {"url": '/mainmenu/procedure_list', "title": "Процедурный лист", "nt": False, "access": ["Лечащий врач", "Оператор лечащего врача"]},
                {"url": '/ui/monitorings/enter', "title": "Заполнение мониторингов", "nt": False, "access": ["Заполнение мониторингов"], "module": "l2_monitorings"},
                {"url": '/ui/monitorings/report', "title": "Просмотр мониторингов", "nt": False, "access": ["Просмотр мониторингов"], "module": "l2_monitorings"},
                {
                    "url": '/ui/schedule',
                    "title": "Расписание",
                    "nt": False,
                    "access": [
                        'Лечащий врач',
                        'Оператор лечащего врача',
                        'Врач консультаций',
                        'Врач стационара',
                        'Врач параклиники',
                        'Управление расписанием',
                        'Создание и редактирование пользователей',
                    ],
                    "module": "l2_schedule",
                },
                {
                    "url": '/ui/eds',
                    "title": "Подпись документов",
                    "nt": False,
                    "access": ["Подпись документов", "Врач параклиники", "Врач консультаций", "Врач-лаборант", "ЭЦП Медицинской организации", "Свидетельство о смерти-доступ"],
                    "module": "l2_eds",
                },
                {
                    "url": '/ui/plan-hospitalization',
                    "title": "План госпитализации",
                    "nt": False,
                    "access": [
                        "Лечащий врач",
                        "Оператор лечащего врача",
                        "Вызов врача",
                    ],
                },
                {
                    "url": '/ui/some-links',
                    "title": "Ccылки",
                    "nt": False,
                    "access": ["*"],
                    "module": "l2_some_links",
                },
                # {"url": '/cases/', "title": "Случаи обслуживания", "nt": False, "access": []},
            ]

            if settings.LDAP and settings.LDAP["enable"]:
                pages.append({"url": "/mainmenu/ldap_sync", "title": "Синхронизация с LDAP", "nt": False, "access": []})
            if settings.DEPRECATED_RMQ_ENABLED:
                pages.append({"url": "/mainmenu/rmq", "title": "Rabbit MQ", "nt": False, "access": []})
            if settings.PROFILING:
                pages.append({"url": "/silk/", "title": "Профилирование", "nt": False, "access": []})
            pages.append({"url": "/mainmenu/utils", "title": "Инструменты", "nt": False, "access": []})

            hp = SettingManager.get(key="home_page", default="false")
            if hp not in ['', 'false']:
                if not hp.startswith('http'):
                    hp = f"http://{hp}"
                pages.append({"url": hp, "title": "Домашняя страница", "nt": True, "access": ["*"]})

            sp = SettingManager.get("support", default="false")
            if sp not in ['', 'false']:
                if not sp.startswith('http'):
                    sp = f"http://{sp}"
                pages.append({"url": sp, "title": "Техническая поддержка", "nt": True, "access": ["*"]})

            vp = SettingManager.get("vks", default="false")
            if vp not in ['', 'false']:
                if not vp.startswith('http'):
                    vp = f"http://{vp}"
                pages.append({"url": vp, "title": "ВКС", "nt": True, "access": ["*"]})

            data = make_menu(pages, groups, request.user.is_superuser, request.path)
            cache.set(k, simplejson.dumps(data), 300)
        else:
            data = simplejson.loads(data)
    return {"mainmenu": data, "version": VERSION}


def make_menu(pages, groups, superuser, current_path=None):
    menu = []
    groups_set = set(groups)
    for page in pages:
        if (not superuser and "*" not in page["access"] and len(groups_set & set(page["access"])) == 0) or (
            page.get("module") and not SettingManager.get(page["module"], default='false', default_type='b')
        ):
            continue
        page["active"] = current_path == page.get("url")
        menu.append(page)
    return menu


def profile(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'doctorprofile'):
        return {}
    specialities = request.user.doctorprofile.specialities
    # return {"specialities": [x.title for x in request.user.doctorprofile.specialities.all() if not x.hide]}
    return {"specialities": [] if not specialities else [specialities.title]}

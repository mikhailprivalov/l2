ALLOWED_HOSTS = ['192.168.0.136', '127.0.0.1', 'localhost', 'testserver', '*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # 'NAME': 'l2_dev',
        # 'NAME': 'pat',
        'NAME': 'igkb9',
        'USER': 'postgres',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
}

CACHALOT_ENABLED = False
DEBUG = True
#WS_ENABLED = True
#WS_BASE = 'lis'
AFTER_DATE = '2019-01-01 10:48:07.558120'
# RMIS_PROXY = {'http':'192.168.0.7:3128', 'https':'192.168.0.7:3128'}
# FIAS_PROXY = {'http':'http://11.119.0.243:3128', 'https':'http://11.119.0.243:3128'}
# RMIS_PROXY = {'http':'192.168.35.199:3128', 'https':'192.168.35.199:3128'}
AFTER_DATE_HOLTER = '2019-10-01 10:48:07'

# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient"
#         }
#     }
# }
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "KEY_PREFIX": "l2"
    }
}

DICOM_SEARCH_TAGS = ["PatientID", "RETIRED_OtherPatientIDs", "Passport"]
DICOM_ADDRESS = '192.168.1.9'
DICOM_PORT = 8042
DICOM_SERVER = f"http://u2:2@{DICOM_ADDRESS}:{DICOM_PORT}"
L2_SERVER = f"http://127.0.0.1:8060/mainmenu/stationar#"
DICOM_SERVER_DELETE = f"http://superadminroot:20f587ec-46e0-4216-a73d-a99457f505f0@{DICOM_ADDRESS}:{DICOM_PORT}"
# DICOM_SERVERS = [f"http://u2:2@{DICOM_ADDRESS}:{DICOM_PORT}", f"http://u2:2@192.168.1.10:{DICOM_PORT}"]
ACSN_MODE = True

REMOTE_DICOM_ADDRESS = '192.168.1.7'
REMOTE_DICOM_PORT = 8042
REMOTE_DICOM_SERVER = f"http://u2:2@{DICOM_ADDRESS}:{DICOM_PORT}"
REMOTE_DICOM_PEER = "orthancentral"

N3_ODII_BASE_URL = "http://odii.miac-io.ru/imaging/exlab/api/fhir"
N3_ODII_TOKEN = "9fb9f918-7b8a-9021-d33e-480e43849838"
N3_ODII_SYSTEM_ID = "1.2.643.2.69.1.2.245"
DEFAULT_N3_DOCTOR = {
    "pk": "",
    "snils": "",
    "speciality": "27" ,
    "position": "73",
    "family": "",
    "name": "",
    "patronymic": "",
}

URL_RMIS_AUTH = "https://38.is-mis.ru/cas/login?service=https://38.is-mis.ru/frontend/j_spring_cas_security_check&ajax=true&username=userlogin&password=userpassword"
URL_ELN_MADE = "https://38.is-mis.ru/frontend/#sicklists.sicksheet_list"
URL_SCHEDULE ="https://38.is-mis.ru/plan/planning?organizationId=organization_param&service.id=service_param&employeeId=employee_param"

SECRET_KEY = "c7de7b0c-c150-11eb-8529-0242ac130003"

EXTRA_MASTER_RESEARCH_PK = 766
EXTRA_SLAVE_RESEARCH_PK = 767

PAP_ANALYSIS_ID = [68]
PAP_ANALYSIS_FRACTION_QUALITY_ID = [130]
PAP_ANALYSIS_FRACTION_CONTAIN_ID = [743]

COVID_RESEARCHES_PK = [52, 77, 72, 770]
GISTOLOGY_RESEARCH_PK = 796
# GISTOLOGY_RESEARCH_PK = None
CENTRE_GIGIEN_EPIDEMIOLOGY = "10000"
REGION = "Иркутская область"
EXCLUDE_HOSP_SEND_EPGU = [28]
RESEARCHES_NOT_PRINT_FOOTERS = [684]

# DEATH_RESEARCH_PK = 765
DEATH_RESEARCH_PK = None
PERINATAL_DEATH_RESEARCH_PK = 785
SYSTEM_AS_VI = False

SOME_LINKS = [{"title": "Рубрикатор", "link": "https://cr.minzdrav.gov.ru/", "comment": "Стандарты лечения и клин. рекомендации"}, {"title":"ВКС", "link": "https://192.168.10.214:5443"}]
DISABLED_FORMS = ["100.03"]
DISABLED_AUTO_PRINT_DATE_IN_FORMS = ["form_27", "form_03"]
DISABLED_STATISTIC_CATEGORIES = []
DISABLED_STATISTIC_REPORTS = ["Оказанные услуги-Диспасеризация"]
COVID_QUESTION_ID = 792
FORWARD_DAYS_SCHEDULE = 30
QRCODE_OFFSET_SIZE = {"x": 174, "y": 6.5, "size": 13}
LEFT_QRCODE_OFFSET_SIZE = {"x": 163, "y": 6.5, "size": 13}
LK_FORMS = [{'title': 'Согласие на обработку персональных данных', 'type': '101.02'}, {'title': 'Согласие на медицинское вмешательство', 'type': '101.03'}]
LK_USER = 3068
LK_FILE_SIZE_BYTES = 3145728
LK_FILE_COUNT = 3
SPLIT_PRINT_RESULT = False
PROTOCOL_PLAIN_TEXT = False
REQUIRED_STATTALON_FIELDS = {}
RESEARCHES_PK_REQUIRED_STATTALON_FIELDS = {358: {"purpose": "Данные статталона - Цель не указана", "result": "Результат не указан"}}
                                           # 800: {"examination_date": "Дата не указана"}}
RESEARCH_SPECIAL_REPORT = {"driver_research": 793, "weapon_research_pk": 794}
DASHBOARD_CHARTS_CACHE_TIME_SEC = 60 * 30
TITLE_REPORT_FILTER_STATTALON_FIELDS = [""]
TITLE_REPORT_FILTER_HAS_ALL_FIN_SOURCE = ["По подразделениям"]

# DISPANSERIZATION_SERVICE_PK = {"pkServiceStart": [673, 358], "pkServiceEnd": [684]}  # {"pkServiceStart": [12, 13], "pkServiceEnd": [15])}
DISPANSERIZATION_SERVICE_PK = {"pkServiceStart": [740], "pkServiceEnd": [684]}  # {"pkServiceStart": [12, 13], "pkServiceEnd": [15])}
LK_DAY_MONTH_START_SHOW_RESULT = "14.03."
#DISPANSERIZATION_STATTALON_FIELDS_RESULTS_PK = [14]
DISPANSERIZATION_STATTALON_FIELDS_PURPOSE_PK = []
EXCLUDE_DOCTOR_PROFILE_PKS_ANKETA_NEED = []
# HIDE_TITLE_BUTTONS_MAIN_MENU = {"Поступление материала": ["План госпитализаций", "Процедурный лист"]}
HIDE_TITLE_BUTTONS_MAIN_MENU = {"Скрытие кнопок": ["Поиск описательных результатов", "Подпись документов", "Выгрузка", "Ссылки", "Оставить отзыв", "Приём биоматериала", "Приём биоматериала по одному", "Журнал приёма", "План госпитализации", "Процедурный лист", "Поиск", "Статталоны", "Печать направлений", "Печать по отделению или врачу", "Отчёт по результатам"], "Скрыть ввод описательных результатов": ["Ввод описательных результатов", "История направления"], "Скрытие кнопок врач":["История направления", "Регистрация направлений"]}
BARCODE_SIZE = "43x25"
SEARCH_PAGE_STATISTIC_PARAMS = {"Статистика-патологоанатомия-бухгалтер": [{"id": "1", "label": "Отчет бухгалтера", "reserches_pk": [796]}]}
# SEARCH_PAGE_STATISTIC_PARAMS = {"Статистика-модель": [{"id": "1", "label": "Статистика-модель", "reserches_pk": [796]}]}

HIDE_TITLE_BUTTONS_MAIN_MENU = {"Только общие папки": ["Направления и картотека",
                                                       "Поиск описательных результатов",
                                                       "Подпись документов",
                                                       "Выгрузка", "Ссылки",
                                                       "Оставить отзыв",
                                                       "Приём биоматериала",
                                                       "Приём биоматериала по одному",
                                                       "Журнал приёма",
                                                       "План госпитализации",
                                                       "Процедурный лист",
                                                       "Поиск",
                                                       "Статталоны",
                                                       "Печать направлений",
                                                       "Печать по отделению или врачу",
                                                       "Отчёт по результатам",
                                                       "История направления",
                                                       "Поиск описательных результатов",
                                                       "Палаты",
                                                       "Листы ожидания",
                                                       "Расписание",
                                                       "Платн госпитализации",
                                                       ]}


OFFSET_HOURS_PLAN_OPERATIONS = 24
DISABLED_RESULT_FORMS = [10201, 10202]
MEDEXAM_FIN_SOURCE_TITLE = "профосмотр"
RESEARCHES_EXCLUDE_AUTO_MEDICAL_EXAMINATION = [800]
AMD_REMD_SYSTEM = "emdr-rmis-1784"

REMD_ONLY_RESEARCH = [796]
REMD_FIELDS_BY_TYPE_DOCUMENT = {
    "ConsultationProtocol_max": [
        "Рекомендации", "Заключение консультации", "Протокол консультации", "Анамнез жизни", "Анамнез заболевания", "Cостояние пациента"
],
    "TeleMed": [
        "Тип консультации",
        "Место проведения",
        "Дата начала", "Время начала",  "Дата окончания", "Время окончания",
        "Цель консультации",
        "Жалобы пациента", "Объективные данные", "Анамнез ТМК",
        "Заключение консультации", "Выявленные патологии", "Рекомендации", "Шифр по МКБ-10 treeselect",
    ],
    "DischargeSummary_min": [
        "вэ-Время окончания",
        "вэ-Время начала",
        "вэ-Трудовые рекомендации",
        "вэ-Рекомендованное лечение",
        "вэ-Режим и диета",
        "вэ-Хирургические вмешательства",
        "вэ-Проведенное лечение",
        "вэ-Лабораторные исследования",
        "вэ-Диагностические исследования",
        "вэ-Состояние при выписке",
        "вэ-Состояние при поступлении",
        "вэ-Заключительный клинический диагноз",
        "вэ-результат стационарного лечения",
        "вэ-Вид госпитализации",
        "вэ-Исход",
        "вэ-Дата выписки",
        "вэ-Дата начала госпитализации",
        "Шифр по МКБ-10 treeselect",
        "Шифр по МКБ-10"
    ]
}

JSON_LOADS_FIELDS_CDA = ["Шифр по МКБ-10 treeselect", "Тип консультации", "Цели ТМК", "Выявленные патологии"]

ID_MED_DOCUMENT_TYPE_IEMK_N3 = {"is_doc_refferal": "198", "DischargeSummary_min": "41"}

# DEF_LABORATORY_LEGAL_AUTH_PK = 2584
# DEF_LABORATORY_LEGAL_AUTH_PK = 2810

EMAIL_HOST = "smtp.yandex.ru"
EMAIL_PORT = 465
# EMAIL_HOST_USER = "sergeikasianenko@yandex.ru"
# EMAIL_HOST_USER = "sergeiskasianenko@yandex.ru"
EMAIL_HOST_USER = "opab4@yandex.ru"
EMAIL_HOST_PASSWORD = "hxsqkungzbsozauc"
# EMAIL_HOST_PASSWORD = "pehicxlnscwrxbzd"
# EMAIL_HOST_PASSWORD = "jynshoflwkggnitj"
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
# RMIS_PROXY = {'http':'192.168.35.199:3128', 'https':'192.168.35.199:3128'}
UNLIMIT_PERIOD_STATISTIC_GROUP = ["Врач консультаций"]

# SHOW_EXAMINATION_DATE_IN_PARACLINIC_RESULT_PAGE = {"is_paraclinic": False, "is_doc_refferal": True, "is_gistology": True}
TYPE_NUMBER_SYSTEM = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Б", "В", "Г", "Д", "Ж", "К", "Л", "М", "П", "Р", "С", "Т", "Х", "Ц", "Ч", "Ш", "Э", "+", "-", "="]
UNLIMIT_PERIOD_STATISTIC_RESEARCH = [765]
#PRINT_ADDITIONAL_PAGE_DIRECTION_FIN_SOURCE = {"платно11": "form_01"}
PRINT_APPENDIX_PAGE_DIRECTION = {"профосмотр": "form_02.form_03", "платно": "form_02.form_02"}
# SPECIAL_TYPE_SLOTS_ECP = {1: "Запись любой", 10: "Запись к себе", 13: "Запись запрет всем", 14: "Запись ЦИТО"}
HOSPITAL_PKS_NOT_CONTROL_DOCUMENT_EXTERNAL_CREATE_DIRECTION = [5]
FORM_100_08_A4_FORMAT = False
CONTROL_AGE_MEDEXAM = {"м": {40: '32', 110: "33"}, "ж": {40: "30", 110: "31"}}
CONTROL_AGE_MEDEXAM_MALE = {9: '32', 18: '32', 19: '32', 20: '32', 21: '32', 22: '32', 23: '32', 24: '32', 25: '32', 26: '32', 27: '32', 28: '32', 29: '32', 30: '32', 31: '32', 32: '32', 33: '32',
                            34: '32', 35: '32', 36: '32', 37: '32', 38: '32', 39: '32',
                            40: '33', 41: '33', 42: '33', 43: '33', 44: '33', 45: '33', 46: '33', 47: '33', 48: '33', 49: '33', 50: '33', 51: '33', 52: '33', 53: '33', 54: '33', 55: '33',
                            56: '33', 57: '33', 58: '33', 59: '33', 60: '33', 61: '33', 62: '33', 63: '33', 64: '33', 65: '33', 66: '33', 67: '33', 68: '33', 69: '33'
                            }

CONTROL_AGE_MEDEXAM_FEMALE = {
    18: '30', 19: '30', 20: '30', 21: '30', 22: '30', 23: '30', 24: '30', 25: '30', 26: '30', 27: '30', 28: '30', 29: '30', 30: '30', 31: '30', 32: '30', 33: '30', 34: '30', 35: '30',
    36: '30', 37: '30', 38: '30', 39: '30',
    40: '31', 41: '31', 42: '31', 43: '31', 44: '31', 45: '31', 46: '31', 47: '31', 48: '31', 49: '31', 50: '31', 51: '31', 52: '31', 53: '31', 54: '31', 55: '31',
    56: '31', 57: '31', 58: '31', 59: '31', 60: '31', 61: '31', 62: '31', 63: '31', 64: '31', 65: '31', 66: '31', 67: '31', 68: '31', 69: '31'}
ECP_SEARCH_PATIENT = {"search": True, "login": "l2admin", "password": "l2123456"}
#AUTO_PRINT_RESEARCH_DIRECTION = {"month_ago": 5, "researches": [308, 73, 354]}
DAYS_AGO_SEARCH_RESULT = {"isLab": 90, "isInstrumental": 365}
NEED_ORDER_DIRECTION_FOR_DEFAULT_HOSPITAL = False
EDUCATION_BASE_TITLE = 'MMIS'
EDUCATION_REASEARCH_CONTRACT_IDS = [825]
MMIS_CONNECT_WITH_PYODBC = True
TITLE_RESULT_FORM_USE_HOSPITAL_STAMP = False
QR_CODE_ANKETA = "https://anketa.minzdrav.gov.ru/stacionar/14"

PRINT_APPENDIX_PAGE_RESULT = {"is_hospital": "form_02.form_03", "6": "form_02.form_02"}
# SELF_WATERMARKS = "self_watermarks_func"
# RESULT_LABORATORY_FORM = "lab_form_1"
TYPE_COMPANY_SET_DIRECTION_PDF = "form_02.form_03"
CDA_TEMPLATE_XML_DIRECTORY = "templates/remd/"

PREFIX_TYPE_SCHEDULE = {"rmis_resource": "@R", "L2": "@L"}

FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES = {
    "msh": {
        "app_sender": "qLIS",
        "organization_sender": "LukaLab",
        "app_receiver": "qLIS",
        "organization_receiver": "LukaLab"},
    "obr": {
        "executer_code": "Л20000001"
    },
    "ftp_settings": {"address": "", "user": "", "password": "", "path": ""},
    "id_researches": [77, 73],
}

ROUTE_LIST_ROW_HEIGHTS = 9
OWN_SETUP_TO_SEND_FTP_EXECUTOR = True
# FORMS_LABORATORY_DIRECTION_DEFAULT = "directions.forms.forms680.form_01"
TUBE_MAX_RESEARCH_WITH_SHARE = True
TUBE_BARCODE_OFFSET_X = -1
# TUBE_BARCODE_WIDTH_MINDEX = 0.0125
TUBE_BARCODE_WIDTH_MINDEX = 0.015
RELATED_AGREES_FORMS_TOGETHER = {'forms.form101.form_28': ['forms.forms101.form_02'], 'forms.form101.form_18': ['forms.forms101.form_02'], }
USERS_PK_SHOW_FACT_ADDRESSES_025U = [1]

ALLOWED_FORMS_FILE = {
    "100.01": True,
    "100.02": True,
    "101.01": True,
    "102.01": True,
    "103.01": True,
}

RMIS_MIDDLE_SERVER_ADDRESS = 'http://127.0.0.1:3001'
RMIS_MIDDLE_SERVER_TOKEN = 'a-super-secret-key'
DEFECT_VARIANTS = ["Гемолиз", "Хилез", "Неправильное назначение", "Отмена назначений", "Нарушение сроков доставки"]
CDA_TITLES_FIELDS_PRIMARY_RESEARCH = ["п.п.-Дата поступления",  "п.п.-Время поступления",   "п.п.-Поступил через",  "п.п.-Тип направитель", "п.п.-Организация направитель", "п.п.-Номер направления",   "п.п.-Дата направления",    "п.п.-Количество",  "п.п.-Форма помощи",    "п.п.-Ds при направлении",  "п.п.-Дата предв. Ds",  "п.п.-Время предв. Ds", "п.п.-Основное Ds текст",   "п.п.-Основное Ds мкб", "п.п.-Осложнения табл",   "п.п.-Внешняя причина Ds текст",    "п.п.-Внешняя причина Ds мкб",  "п.п.-Сопутствующие Ds текс",   "п.п.-Сопутствующие Ds мкб",    "п.п.-Дополнительные сведения заболевания", "п.п.-Туберкулез",  "п.п.-ВИЧ-инфекция",    "п.п.-Вирусные гепатиты",   "п.п.-сифилис", "п.п.-COVID-19",    "п.п.-Педикулез осмотр",    "п.п.-Педикулез результат", "п.п.-Аллергия",    "п.п.-Трансфузии",  "п.п.-Группа крови",    "п.п.-резус",   "п.п.-антиген К1",  "п.п.-Kell",    "п.п.-Иное группа крови",   "п.п.-Кому доверяю",    "п.п.-Пациент доп сведения", "п.п.-Сопутствующие табл"]
CDA_TITLES_FIELDS_EXTRACT_RESEARCH = ["в.э.-Дата выписки", "в.э.-Время выписки", "в.э.-Кол-во дней", "в.э.-Дата клин. Ds", "в.э.-Время клин. Ds", "в.э.-Основное Ds текст", "в.э.-Основное Ds мкб", "в.э.-Осложнения Ds текст", "в.э.-Осложнения Ds мкб", "в.э.-Внешняя причина Ds текст", "в.э.-Внешняя причина Ds мкб", "в.э.-Сопутствующие Ds текс", "в.э.-Сопутствующие Ds мкб", "в.э.-Дополнительные сведения заболевания", "в.э.-Исход", "в.э.-Результат", "в.э.-Умер отделение", "в.э.-Умер дата", "в.э.-Умер время", "в.э.-Беременность срок", "в.э.-ЭЛН Номер", "в.э.-ЭЛН дата", "в.э.-дубликат ЭЛН Номер", "в.э.-дубликат ЭЛН дата", "в.э.-дубликат ЭЛН Номер", "в.э.-дубликат ЭЛН дата", "в.э.-ЭЛН с", "в.э.-ЭЛН по", "в.э.-ЭЛН с", "в.э.-ЭЛН по", "в.э.-продление ЭЛН №", "в.э.-продление ЭЛН с", "в.э.-ЭЛН продление по", "в.э.-ЭЛН к работе", "в.э.-ЭЛН по уходу", "в.э.-МСЭ дата", "п.п.-Кому доверяю", "п.п.-Пациент доп сведения", "в.э.-Врач ФИО", "в.э.-Врач специальность", "в.э.-Врач ФИО", "в.э.-Врач специальность", "в.э.-зав ФИО", "в.э.-зав специальность", "в.э.-Осложнения табл", "в.э.-Сопутствующие табл"]
CDA_TITLES_FIELDS_PROFOSMOTR = ["п.о.-СНИЛС", "п.о.-Тип медосмотра", "п.о.-Вредности", "п.о.-Группа здоровья", "п.о.-Заключение", "п.о.-"]
CDA_TITLES_FIELDS_TRANSFUSION = []
TYPE_REPORT_FORMS = {"inc-1": "forms100.form_01"}
CDA_ID_FOR_DATE_CLOSE_CASE = 113
CDA_ID_FOR_WHERE_SERVICE_DONE = 114
CDA_ID_FOR_TYPE_MEDICAL_INSPECTION = 115
RESEARCH_ID_CLOSE_CASE = (833,)
SHIFTS_VARIANTS = [{"id": "16.2", "label": "16.2 ч."}, {"id": "8", "label": "8 ч."}]
WEB_PLUGIN_LINK_STUDY = "stone-webviewer/index.html?study="

TITLES_FIELDS_MEDEXAM_DRIVER = {"resultField": "По результатам медицинского обследования врачом-психиатром", "dateField": "Дата осмотра", "returnDocument": "Медицинское освидетельствование проведено в связи с возвратом водительского удостоверения"}
API_SERVER_SEND_GISTOLOGY_RESULT = "http://127.0.0.1:3002"

from io import BytesIO
from datetime import date, datetime

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson as json
from reportlab.pdfgen import canvas
from django.core.paginator import Paginator
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4
from django.conf import settings
from django.utils import dateformat

from researches.models import Researches
from directions.models import Napravleniya, Issledovaniya, IstochnikiFinansirovaniya, TubesRegistration
from clients.models import Importedclients
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required

import directory.models as directory

w, h = A4


@csrf_exempt
@login_required
def dir_save(request):
    """Сохранение направления"""
    res = {}  # Словарь с направлениями, сгруппированными по лабораториям
    result = {"r": False, "list_id": [], "mda": ""}
    """
        r - флаг успешной вставки направлений
        list_id - список сохраненных направлений
        mda - отладка
    """
    if request.method == 'POST':
        dict = json.loads(request.POST['dict'])  # json парсинг принятых данных
        client_id = dict["client_id"]  # установка принятого идентификатора пациента
        diagnos = dict["diagnos"]  # диагноз
        finsource = dict["fin_source"]  # источник финансирования
        researches = dict["researches"]  # исследования
        researches_grouped_by_lab = []  # Лист с выбранными исследованиями по лабораториям
        i = 0  # Идентификатор направления
        if client_id and researches:  # если client_id получен и исследования получены
            for v in researches:  # нормализация исследований
                if v:
                    researches_grouped_by_lab.append(
                        {i: v})  # добавление словаря в лист, ключом которого является идентификатор исследования
                    # [{5:[0,2,5,7]},{6:[8]}] 5 - id лаборатории, [0,2,5,7] - id исследований из справочника
                i += 1
            for v in researches_grouped_by_lab:  # цикл перевода листа в словарь
                for key in v.keys():
                    res[key] = v[key]
            # {5:[0,2,5,7],6:[8]}

            # TODO: Обратить внимание!
            # TODO: Нарисовать отдельную блок-схему

            directionsForResearches = {}  # Словарь для временной записи направлений.
            # Исследование привязываются к направлению по группе

            finsource = IstochnikiFinansirovaniya.objects.get(pk=finsource)  # получение источника финансирования
            result["mda"] += json.dumps(res)

            for key in res:  # перебор лабораторий
                for v in res[key]:  # перебор выбраных исследований в лаборатории
                    research = directory.Researches.objects.get(pk=v)  # получение объекта исследования по id

                    dir_group = -1
                    if research.direction:
                        dir_group = research.direction.pk  # получение группы исследования
                    # Если группа == 0, исследование не группируется с другими в одно направление
                    if dir_group >= 0 and dir_group not in directionsForResearches.keys():
                        # Если исследование может группироваться и направление для группы не создано

                        # Создание направления для группы
                        directionsForResearches[dir_group] = Napravleniya(
                            client=Importedclients.objects.get(pk=client_id),
                            # Привязка пациента к направлению
                            doc=request.user.doctorprofile,
                            # Привязка врача к направлению
                            istochnik_f=finsource,
                            # Установка источника финансирования
                            diagnos=diagnos)  # Установка диагноза

                        directionsForResearches[dir_group].save()  # Сохранение направления

                        result["mda"] += str(dir_group)  # Отладка
                        result["list_id"].append(
                            directionsForResearches[dir_group].pk)  # Добавление ID в список созданых направлений
                    if dir_group < 0:  # если исследование не должно группироваться
                        dir_group = "id" + str(
                            research.pk)  # формирование ключа (группы) для негруппируемого исследования

                        # Создание направления для исследования
                        directionsForResearches[dir_group] = Napravleniya(
                            client=Importedclients.objects.get(pk=client_id),
                            # Привязка пациента к направлению
                            doc=request.user.doctorprofile,
                            # Привязка врача к направлению
                            istochnik_f=finsource,
                            # Установка источника финансирования
                            diagnos=diagnos)  # Установка диагноза

                        directionsForResearches[dir_group].save()  # Сохранение направления
                        result["list_id"].append(
                            directionsForResearches[dir_group].pk)  # Добавление ID в список созданых направлений
                        result["mda"] += str(dir_group) + " | "  # Добавление в отладочный вывод
                    issledovaniye = Issledovaniya(napravleniye=directionsForResearches[dir_group],
                                                  # Установка направления для группы этого исследования
                                                  research=research)  # Создание направления на исследование
                    issledovaniye.save()  # Сохранение направления на исследование

            result["r"] = True  # Флаг успешной вставки в True
            result["list_id"] = json.dumps(result["list_id"])  # Перевод списка созданых направлений в JSON строку
    return HttpResponse(json.dumps((result,)), content_type="application/json")


@cache_page(60 * 15)
@login_required
def gen_pdf_dir(request):
    """Генерация PDF направлений"""
    direction_id = json.loads(request.GET["napr_id"])  # Перевод JSON строки в объект

    response = HttpResponse(content_type='application/pdf')  # Формирование ответа типа PDF
    response['Content-Disposition'] = 'inline; filename="napr.pdf"'  # Включение режима вывода PDF в браузер

    buffer = BytesIO()  # Буфер
    c = canvas.Canvas(buffer, pagesize=A4)  # Создание холста для PDF размера А4
    framePage(c)  # Рисование разделительных линий для страницы

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os.path

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Путь до текущего скрипта

    pdfmetrics.registerFont(
        TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))  # Загрузка шрифта из файла

    p = Paginator(direction_id, 4)  # Деление списка направлений по 4

    for pg_num in p.page_range:  # Перебор страниц
        pg = p.page(pg_num)  # Выбор страницы по номеру
        i = 4  # Номер позиции направления на странице (4..1)
        for obj in pg.object_list:  # Перебор номеров направлений на странице
            printDirection(c, i,
                           Napravleniya.objects.get(pk=obj))  # Вызов функции печати направления на указанную позицию
            i -= 1
        if pg.has_next():  # Если есть следующая страница
            c.showPage()  # Создание новой страницы
            framePage(c)  # Рисование разделительных линий для страницы
    c.save()  # Сохранение отрисованного на PDF

    pdf = buffer.getvalue()  # Получение данных из буфера
    buffer.close()  # Закрытие буфера
    response.write(pdf)  # Запись PDF в ответ
    return response


def framePage(canvas):
    # Деление страницы на 4 зоны линиями
    canvas.setFont('Times-Roman', 20)
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(1)
    canvas.line(w / 2, 0, w / 2, h)
    canvas.line(0, h / 2, w, h / 2)


def printDirection(c, n, dir):
    # Нанесение одного направления на документ на свою зону
    xn = 0
    if n % 2 != 0: xn = 1
    yn = 0
    if n > 2: yn = 1
    barcode = eanbc.Ean13BarcodeWidget(dir.pk + 460000000000, humanReadable=0,
                                       barHeight=17)  # Генерация штрих-кода с номером вида 460000001005
    bounds = barcode.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(width, height)
    d.add(barcode)
    paddingx = 15

    c.setFont('OpenSans', 10)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 5) + (h / 2) * yn,
                        "Клиники ГБОУ ВПО ИГМУ Минздрава России")

    c.setFont('OpenSans', 8)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 15) + (h / 2) * yn,
                        "(г. Иркутск, б-р. Гагарина, 18. тел: 280-808, 280-809)")

    c.setFont('OpenSans', 14)
    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 30) + (h / 2) * yn, "Направление")

    renderPDF.draw(d, c, w / 2 - width + (w / 2 * xn) - paddingx / 3, (h / 2 - height - 57) + (h / 2) * yn)

    c.setFont('OpenSans', 20)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height) + (h / 2) * yn - 57, "№ " + str(dir.pk))  # Номер направления

    c.setFont('OpenSans', 9)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 70) + (h / 2) * yn,
                 "Дата: " + str(dateformat.format(dir.data_sozdaniya.date(), settings.DATE_FORMAT)))

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 80) + (h / 2) * yn,
                 "ФИО: " + dir.client.family + " " + dir.client.name + " " + dir.client.twoname)

    c.drawRightString(w / 2 * (xn + 1) - paddingx, (h / 2 - height - 90) + (h / 2) * yn, "Возраст: " + str(
        calculate_age(datetime.strptime(dir.client.birthday.split(" ")[0], "%d.%m.%Y").date())) + " лет")

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn, "Номер карты: " + str(dir.client.num))

    c.drawCentredString(w / 2 - w / 4 + (w / 2 * xn), (h / 2 - height - 90) + (h / 2) * yn, "Пол: " + dir.client.sex)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 100) + (h / 2) * yn, "Диагноз: " + dir.diagnos)

    d = {"poli": "Поликлиника", "stat": "Стационар"}

    if dir.istochnik_f:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn,
                     "Источник финансирования: " + d[dir.istochnik_f.istype] + " - " + dir.istochnik_f.tilie)
    else:
        c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 110) + (h / 2) * yn, "Источник финансирования: ")

    issledovaniya = Issledovaniya.objects.filter(napravleniye=dir)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 120) + (h / 2) * yn,
                 "Лаборатория: " + issledovaniya[0].research.subgroup.podrazdeleniye.title)

    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 134) + (h / 2) * yn, "Наименования исследований: ")
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()
    data = []

    p = Paginator(issledovaniya, 2)

    for pg_num in p.page_range:
        pg = p.page(pg_num)
        tmp = []
        for obj in pg.object_list:
            tmp.append(Paragraph('<font face="OpenSans" size="8">' + obj.research.title + "</font>",
                                 styleSheet["BodyText"]))
        if len(pg.object_list) < 2:
            tmp.append(Paragraph('<font face="OpenSans" size="8"></font>', styleSheet["BodyText"]))
        data.append(tmp)

    tw = w / 2 - paddingx * 2
    t = Table(data, colWidths=[int(tw / 2), int(tw / 2)])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                           ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                           ('LEFTPADDING', (0, 0), (-1, -1), 4),
                           ('TOPPADDING', (0, 0), (-1, -1), -0.5),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), -1),
                           ]))
    t.canv = c
    wt, ht = t.wrap(0, 0)
    t.drawOn(c, paddingx + (w / 2 * xn), ((h / 2 - height - 138) + (h / 2) * yn - ht))

    c.setFont('OpenSans', 8)
    c.drawString(paddingx + (w / 2 * xn), (h / 2 - height - 138) + (h / 2) * yn - ht - 10,
                 "Всего назначено: " + str(len(issledovaniya)))

    c.drawString(paddingx + (w / 2 * xn), 30 + (h / 2) * yn, "Отделение: " + dir.doc.podrazileniye.title)
    c.drawString(paddingx + (w / 2 * xn), 15 + (h / 2) * yn, "Врач: " + dir.doc.get_fio())
    c.setFont('OpenSans', 7)
    c.setLineWidth(0.25)
    c.line(w / 2 * (xn + 1) - paddingx, 23 + (h / 2) * yn, w / 2 * (xn + 1) - 82, 23 + (h / 2) * yn)
    c.drawRightString(w / 2 * (xn + 1) - paddingx - paddingx, 15 + (h / 2) * yn, "(подпись)")


def calculate_age(born):
    """Подсчет возраста"""
    today = date.today()
    try:
        birthday = born.replace(year=today.year)
    except ValueError:
        birthday = born.replace(year=today.year, month=born.month + 1, day=1)
    if birthday > today:
        return today.year - born.year - 1
    else:
        return today.year - born.year


@login_required
def get_one_dir(request):
    """Получение одного направления и исследований из него по пробиркам"""
    # import logging
    # logger = logging.getLogger(__name__)

    response = {}
    if request.method == 'GET':  # Проверка типа запроса
        id = int(request.GET['id'])  # Получение идентификатора направления
        if Napravleniya.objects.filter(pk=id).exists():  # Проверка на существование направления
            tmp2 = Napravleniya.objects.get(pk=id)  # Выборка направления
            tmp = Issledovaniya.objects.filter(napravleniye=tmp2)
            '''.order_by(
                '-issledovaniye__tube_weight')  # Выборка исследований по направлению'''
            response["direction"] = {"pk": tmp2.pk,
                                     "date": str(dateformat.format(tmp2.data_sozdaniya.date(), settings.DATE_FORMAT)),
                                     "doc": {"fio": tmp2.doc.get_fio(), "otd": tmp2.doc.podrazileniye.title},
                                     "lab": tmp[0].research.subgroup.podrazdeleniye.title}  # Формирование вывода
            response["tubes"] = {}
            tubes_buffer = {}
            for v in tmp:
                for val in directory.Fractions.objects.filter(research=v.research):
                    if val.id not in tubes_buffer.keys():
                        if not v.tubes.filter(type=val.relation).exists():
                            ntube = TubesRegistration(type=val.relation)
                            ntube.save()
                            v.tubes.add(ntube)
                        else:
                            ntube = v.tubes.get(type=val.relation)
                        tubes_buffer[val.relation.pk] = {"pk": ntube.pk, "researches": set()}
                    tubes_buffer[val.relation.pk]["researches"].add(v.research.title)
            for key in tubes_buffer.keys():
                tubes_buffer[key]["researches"] = list(tubes_buffer[key]["researches"])

            for key in tubes_buffer.keys():  # Перебор исследований
                v = tubes_buffer[key]
                tube = TubesRegistration.objects.get(id=v["pk"])

                barcode = ""
                if tube.barcode:  # Проверка штрих кода пробирки
                    barcode = tube.barcode
                if tube.id not in response["tubes"].keys():  # Если пробирки нет в словаре
                    response["tubes"][tube.id] = {"researches": v["researches"], "status": True,
                                                  "color": tube.type.tube.color,
                                                  "title": tube.type.tube.title, "id": tube.id,
                                                  "barcode": barcode}  # Добавление пробирки в словарь
                s = False  # Статус взятия материала для исследований
                if tube.time_get and tube.doc_get:  # Проверка статуса пробирки
                    s = True  # Установка статуса для вывода в интерфейс
                response["tubes"][tube.id]["status"] = s  # Установка статуса в объект пробирки

            response["client"] = {"fio": tmp2.client.family + " " + tmp2.client.name + " " + tmp2.client.twoname,
                                  "sx": tmp2.client.sex, "bth": str(
                dateformat.format(datetime.strptime(tmp2.client.birthday.split(" ")[0], "%d.%m.%Y").date(),
                                  settings.DATE_FORMAT))}  # Добавление информации о пациенте в вывод
    return HttpResponse(json.dumps(response), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def update_direction(request):
    """Функция обновления исследований в направлении"""
    from django.utils import timezone

    res = {"r": False, "o": []}
    if request.method == 'POST':  # Проверка типа запроса
        statuses = json.loads(request.POST["data"])

        for k, v in statuses["statuses"].items():  # Перебор ключей и значений
            val = TubesRegistration.objects.get(id=k)  # Выборка пробирки по ключу
            if v:  # Если статус выполнения забора установлен в True
                val.doc_get = request.user.doctorprofile  # Привязка профиля к пробирке
                val.time_get = timezone.now()  # Установка времени
                val.barcode = statuses["statuses"][k]  # Установка штрих-кода или номера пробирки
            val.save()  # Сохранение пробирки
            res["o"].append(val.id)
        res["r"] = True

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@login_required
def load_history(request):
    """Получение истории заборов материала за текущий день"""
    import pytz

    res = {"rows": []}
    tubes = TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('time_get').exclude(
        time_get__lt=datetime.now().date())  # Выборка материала за сегодня
    local_tz = pytz.timezone(settings.TIME_ZONE)  # Формирование временной зоны

    for v in tubes:  # Перебор пробирки
        iss = Issledovaniya.objects.filter(tubes__id=v.id)  # Выборка исследований по пробирке
        iss_list = []
        for val in iss:  # Перебор выбранных исследований
            iss_list.append(val.research.title)  # Добавление в список исследований по пробирке
        res["rows"].append({"type": v.type.tube.title, "researches": ', '.join(str(x) for x in iss_list),
                            "time": v.time_get.astimezone(local_tz).strftime("%H:%M:%S"),
                            "dir_id": iss[0].napravleniye.pk, "tube_id": v.id})  # Добавление пробирки с исследованиями
        # в вывод
    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON


@login_required
def print_history(request):
    """Печать истории забора материала за день"""
    user = request.user.doctorprofile  # Профиль текущего пользователя
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    styleSheet = getSampleStyleSheet()
    import os.path
    import collections
    import pytz

    # from pymongo import MongoClient
    '''client = MongoClient('mongodb://localhost:27017/')
    db = client['reports-db']
    collection = db['tubes']

    def get_next_id(collection_name):
        result = db.counters.find_and_modify(query={"_id": collection_name},
                                         update={"$inc": {"next": 1}},
                                         upsert=True, new=True)
        return result["next"]'''

    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  # Директория Django
    pdfmetrics.registerFont(TTFont('OpenSans', PROJECT_ROOT + '/../static/fonts/OpenSans.ttf'))  # Загрузка шрифта

    response = HttpResponse(content_type='application/pdf')  # Формирование ответа
    response[
        'Content-Disposition'] = 'inline; filename="napr.pdf"'  # Content-Disposition inline для показа PDF в браузере
    buffer = BytesIO()  # Буфер
    c = canvas.Canvas(buffer, pagesize=A4)  # Холст

    tubes = TubesRegistration.objects.filter(doc_get=request.user.doctorprofile).order_by('time_get').exclude(
        time_get__lt=datetime.now().date())  # Получение пробирок с материалом, взятым текущим пользователем
    local_tz = pytz.timezone(settings.TIME_ZONE)  # Локальная временная зона
    labs = {}  # Словарь с пробирками, сгруппироваными по лаборатории
    for v in tubes:  # Перебор пробирок
        iss = Issledovaniya.objects.filter(tube=v)  # Получение исследований для пробирки
        iss_list = []  # Список исследований
        k = iss[0].napravleniye.doc.podrazileniye.title + "@" + iss[
            0].issledovaniye.getlab()  # Формирование ключа для группировки по подгруппе лаборатории и названию подразделения направившего на анализ врача
        for val in iss:  # Цикл перевода полученных исследований в список
            iss_list.append(val.issledovaniye.s_title())
        if k not in labs.keys():  # Добавление списка в словарь если по ключу k нету ничего в словаре labs
            labs[k] = []
        for value in iss_list:  # Перебор списка исследований
            labs[k].append(
                {"type": v.type.title, "researches": value,
                 "client-type": iss[0].napravleniye.client.type,
                 "lab_title": iss[0].issledovaniye.getlab(),
                 "time": v.time_get.astimezone(local_tz).strftime("%H:%M:%S"), "dir_id": iss[0].napravleniye.pk,
                 "podr": iss[0].napravleniye.doc.podrazileniye.title,
                 "reciver": None,
                 "tube_id": str(v.id)})  # Добавление в список исследований и пробирок по ключу k в словарь labs
    labs = collections.OrderedDict(sorted(labs.items()))  # Сортировка словаря
    c.setFont('OpenSans', 20)

    paddingx = 17
    data_header = ["№ п/п", "Тип емкости", "№ емкости", "Наименования исследований", "Емкость не принята (замечания)"]
    tw = w - paddingx * 4
    tx = paddingx * 3
    ty = 90
    c.setFont('OpenSans', 9)
    styleSheet["BodyText"].fontName = "OpenSans"
    styleSheet["BodyText"].fontSize = 8
    doc_num = 0

    # mongo_cache = {"date": str(dateformat.format(date.today(), settings.DATE_FORMAT)), "user": request.user.id, "docs": {}}
    # if collection.find_one({"date": mongo_cache["date"], "user": mongo_cache["user"]}):
    #    collection.remove({"date": mongo_cache["date"], "user": mongo_cache["user"]})
    for key in labs:
        doc_num += 1
        p = Paginator(labs[key], 47)
        i = 0
        if doc_num >= 2:
            c.showPage()
        # tubes_cache = {}
        # mongo_cache["docs"][str(doc_num)] = {"tubes": [], "lab": key, "id": get_next_id("reports-db")}
        for pg_num in p.page_range:
            pg = p.page(pg_num)
            if pg_num >= 0:
                # drawTituls(c, mongo_cache["docs"][str(doc_num)]["id"], user, p.num_pages, pg_num, paddingx, pg[0])
                drawTituls(c, user, p.num_pages, pg_num, paddingx, pg[0])
            data = []
            tmp = []
            for v in data_header:
                tmp.append(Paragraph(str(v), styleSheet["BodyText"]))
            data.append(tmp)
            merge_list = {}
            num = 0
            lastid = "-1"

            for obj in pg.object_list:
                # if obj["tube_id"] not in tubes_cache.keys():
                #    tubes_cache[str(obj["tube_id"])] = {"researches": [], "reciver": obj["reciver"]}
                tmp = []
                if lastid != obj["tube_id"]:
                    i += 1
                    lastid = obj["tube_id"]
                    shownum = True
                else:
                    shownum = False
                    if lastid not in merge_list.keys():
                        merge_list[lastid] = []
                    merge_list[lastid].append(num)

                if shownum:
                    tmp.append(Paragraph(str(i), styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["type"], styleSheet["BodyText"]))
                    tmp.append(Paragraph(obj["tube_id"], styleSheet["BodyText"]))
                else:
                    tmp.append("")
                    tmp.append("")
                    tmp.append("")
                research_tmp = obj["researches"]
                # tubes_cache[obj["tube_id"]]["researches"].append(research_tmp)
                if len(research_tmp) > 40:
                    research_tmp = research_tmp[0:-(len(research_tmp) - 40)] + "..."
                tmp.append(Paragraph(research_tmp, styleSheet["BodyText"]))
                tmp.append(Paragraph("", styleSheet["BodyText"]))

                data.append(tmp)
                num += 1

            style = TableStyle([
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                ('LEFTPADDING', (0, 0), (-1, -1), 1),
                ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1)
            ])
            for span in merge_list:  # Цикл объединения ячеек
                for pos in range(0, 5):
                    style.add('INNERGRID', (pos, merge_list[span][0]),
                              (pos, merge_list[span][0] + len(merge_list[span])), 0.28, colors.white)
                    style.add('BOX', (pos, merge_list[span][0]), (pos, merge_list[span][0] + len(merge_list[span])),
                              0.2, colors.black)
            t = Table(data, colWidths=[int(tw * 0.05), int(tw * 0.25), int(tw * 0.10), int(tw * 0.35), int(tw * 0.25)],
                      style=style)

            t.canv = c
            wt, ht = t.wrap(0, 0)
            t.drawOn(c, tx, h - ht - ty)
            if pg.has_next():
                c.showPage()
                # mongo_cache["docs"][str(doc_num)]["tubes"] = tubes_cache
    # collection.insert_one(mongo_cache)
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def drawTituls(c, user, pages, page, paddingx, obj, lab=""):
    """Функция рисования шапки и подвала страницы pdf"""
    c.setFont('OpenSans', 9)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)

    c.drawCentredString(w / 2, h - 30, "Клиники ГБОУ ВПО ИГМУ Минздрава России")
    c.setFont('OpenSans', 12)
    c.drawCentredString(w / 2, h - 50, "АКТ приема-передачи емкостей с биоматериалом")

    c.setFont('OpenSans', 10)
    # c.drawString(paddingx * 3, h - 70, "№ " + str(doc_num))
    c.drawRightString(w - paddingx, h - 70,
                      "Дата: " + str(dateformat.format(date.today(), settings.DATE_FORMAT)))

    c.drawString(paddingx * 3, h - 70, "Отделение (от кого): " + str(obj["podr"]))
    c.drawString(paddingx * 3, h - 80, "Лаборатория (кому): " + str(obj["lab_title"]))
    c.drawString(paddingx * 3, 55, "Сдал: ________________/_____________________________/")
    c.setFont('OpenSans', 8)
    c.drawString(paddingx * 3 + 50, 45, "(подпись)")
    c.setFont('OpenSans', 10)
    c.drawRightString(w - paddingx, 55, "Принял: ________________/_____________________________/")
    c.setFont('OpenSans', 8)
    c.drawRightString(w - paddingx - 150, 45, "(подпись)")

    c.drawRightString(w - paddingx, 20, "Страница " + str(page) + " из " + str(pages))


@login_required
def get_issledovaniya(request):
    res = {"issledovaniya": []}
    if request.method == "GET":
        iss = []
        napr = None
        id = request.GET["id"]
        if request.GET["type"] == "0":
            iss = Issledovaniya.objects.filter(tubes__id=id).all()
            '''ishide = False
            for iss_check in iss:
                if iss_check.issledovaniye.hide == 0:
                    ishide = False

            if ishide:
                iss = Issledovaniya.objects.filter(tube=tube)
                napr = iss.first().napravleniye
                iss = napr.issledovaniya_set.filter(issledovaniye__auto_add=iss.first().issledovaniye.hide)
            else:'''
            napr = iss.first().napravleniye
        else:
            napr = Napravleniya.objects.get(pk=id)
            iss = Issledovaniya.objects.filter(napravleniye__pk=id).all()
        for issledovaniye in iss:
            if True:  # issledovaniye.research.hide == 0:
                tubes_list = issledovaniye.tubes.all()
                tubes = []
                titles = []
                for tube_o in tubes_list:
                    tubes.append(tube_o.pk)
                    titles.append(tube_o.type.tube.title)
                '''for iss_hidden in iss.filter(issledovaniye__hide=1,
                                             issledovaniye__auto_add=issledovaniye.issledovaniye.auto_add):
                    tubes.append(iss_hidden.tube.pk)'''
                res["issledovaniya"].append({"pk": issledovaniye.pk, "title": issledovaniye.research.title,
                                             "tube": {"pk": ', '.join(str(v) for v in tubes),
                                                      "title": ', '.join(titles)}})
        res["napr_pk"] = napr.pk
        res["client_fio"] = napr.client.family + " " + napr.client.name + " " + napr.client.twoname
        res["client_sex"] = napr.client.sex
        res["client_cardnum"] = napr.client.num
        res["client_vozrast"] = str(
            calculate_age(datetime.strptime(napr.client.birthday.split(" ")[0], "%d.%m.%Y").date())) + " лет"
        res["directioner"] = napr.doc.fio

    return HttpResponse(json.dumps(res), content_type="application/json")  # Создание JSON

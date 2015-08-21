from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from laboratory.decorators import group_required
from django.shortcuts import render
from users.models import Podrazdeleniya
from directions.models import Napravleniya, Issledovaniya, TubesRegistration, Tubes
import directory.models as directory
from django.http import HttpResponse


@csrf_exempt
@login_required
@group_required("Просмотр статистики")
def statistic_page(request):
    labs = Podrazdeleniya.objects.filter(isLab=True)
    tubes = directory.Tubes.objects.all()
    podrs = Podrazdeleniya.objects.filter(isLab=False,hide=False)
    return render(request, 'statistic.html', {"labs": labs, "tubes": tubes, "podrs": podrs})


@csrf_exempt
@login_required
@group_required("Просмотр статистики")
def statistic_xls(request):
    from directions.models import Issledovaniya
    import xlwt
    wb = xlwt.Workbook(encoding='utf-8')
    response = HttpResponse(content_type='application/ms-excel')
    pk = request.REQUEST["pk"]
    tp = request.REQUEST["type"]
    date_start = request.REQUEST["date-start"]
    date_end = request.REQUEST["date-end"]

    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
           u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
    tr = {ord(a):ord(b) for a, b in zip(*symbols)}

    if tp == "lab":
        lab = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate("attachment; filename='Статистика_Лаборатория_{0}_{1}-{2}.xls'".format(lab.title.replace(" ", "_"), date_start, date_end), tr)

        ws = wb.add_sheet("Выполненых анализов")

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start, date_end)
        ]

        import datetime
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()

        row = [
            lab.title
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1
        columns = [
            (u"ID анализа", 3000),
            (u"Названние", 8000),
            (u"Выполнено", 5000),
        ]


        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        all = 0
        for obj in directory.Researches.objects.filter(subgroup__podrazdeleniye__pk=lab.pk):
            row_num += 1
            c = Issledovaniya.objects.filter(research__pk=obj.pk, time_confirmation__isnull=False, time_confirmation__range=(date_start, date_end)).count()
            all += c
            row = [
                obj.pk,
                obj.title,
                c,
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1
        row = [
            "",
            "",
            "Всего: "+str(all),
        ]
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 3
        font_style.alignment.horz = 3
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    elif tp == "otd":
        otd = Podrazdeleniya.objects.get(pk=int(pk))
        response['Content-Disposition'] = str.translate("attachment; filename='Статистика_Отделение_{0}_{1}-{2}.xls'".format(otd.title.replace(" ", "_"), date_start, date_end), tr)


        ws = wb.add_sheet("Выписано направлений")
        row_num = 0

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start, date_end)
        ]

        import datetime
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()

        row = [
            otd.title
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

        font_style = xlwt.XFStyle()

        row_num += 1
        row = [
            (u"Всего выписано", 6000),
            (str(Napravleniya.objects.filter(doc__podrazileniye=otd, data_sozdaniya__range=(date_start, date_end)).count()), 3000),
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num][0], font_style)
            ws.col(col_num).width = row[col_num][1]

        row_num += 1
        iss = Issledovaniya.objects.filter(napravleniye__doc__podrazileniye=otd, napravleniye__data_sozdaniya__range=(date_start, date_end), time_confirmation__isnull=False)
        naprs = len(set([v.napravleniye.pk for v in iss]))
        row = [
            u"Завершенных",
            str(naprs)
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    elif tp == "tube":
        pass
    elif tp == "all-labs":
        labs = Podrazdeleniya.objects.filter(isLab=True)
        response['Content-Disposition'] = str.translate("attachment; filename='Статистика_Все_Лаборатории_{0}-{1}.xls'".format(date_start, date_end), tr)
        ws = wb.add_sheet("Выполненых анализов")


        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start, date_end)
        ]

        import datetime
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = [
            (u"Лаборатория", 9000),
            (u"Выполнено анализов", 8000),
        ]


        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        all = 0
        for lab in labs:
            row_num += 1
            c = Issledovaniya.objects.filter(research__subgroup__podrazdeleniye=lab, time_confirmation__isnull=False, time_confirmation__range=(date_start, date_end)).count()
            row = [
                lab.title,
                c
            ]
            all += c
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1
        row = [
            "",
            "Всего: "+str(all),
        ]
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 3
        font_style.alignment.horz = 3
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    elif tp == "tubes-using":
        response['Content-Disposition'] = str.translate("attachment; filename='Статистика_Использование_Емкостей_{0}-{1}.xls'".format(date_start, date_end), tr)
        ws = wb.add_sheet("Использование емкостей")

        font_style = xlwt.XFStyle()
        row_num = 0
        row = [
            "За период: ",
            "{0} - {1}".format(date_start, date_end)
        ]

        import datetime
        date_start = datetime.date(int(date_start.split(".")[2]), int(date_start.split(".")[1]),
                                   int(date_start.split(".")[0]))
        date_end = datetime.date(int(date_end.split(".")[2]), int(date_end.split(".")[1]),
                                 int(date_end.split(".")[0])) + datetime.timedelta(1)

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        columns = [
            (u"Тип емкости", 9000),
            (u"Материал взят в процедурном каб", 9000),
            (u"Принято лабораторией", 8000),
            (u"Не принято лабораторией", 8000),
            (u"Потеряны", 4000),
        ]


        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1
        all_get = 0
        all_rec = 0
        all_nrec = 0
        all_lost = 0
        for tube in Tubes.objects.all():
            row_num += 1
            c_get = TubesRegistration.objects.filter(type__tube=tube, time_get__isnull=False, time_get__range=(date_start, date_end)).count()
            c_rec = TubesRegistration.objects.filter(type__tube=tube, time_recive__isnull=False, notice="", time_get__range=(date_start, date_end)).count()
            c_nrec = TubesRegistration.objects.filter(type__tube=tube, time_get__isnull=False,time_get__range=(date_start, date_end)).exclude(notice="").count()
            str1 = ""
            str2 = ""
            if c_nrec > 0:
                str1 = str(c_nrec)
            if c_get-c_rec-all_nrec > 0:
                str2 = str(c_get-c_rec-all_nrec)
                all_lost += c_get-c_rec-all_nrec

            row = [
                tube.title,
                c_get,
                c_rec,
                str1,
                str2
            ]
            all_get += c_get
            all_rec += c_rec
            all_nrec += c_nrec
            for col_num in range(len(row)):
                font_style.alignment.wrap = 1
                font_style.alignment.horz = 1
                if col_num > 0:
                    font_style.alignment.wrap = 3
                    font_style.alignment.horz = 3
                ws.write(row_num, col_num, row[col_num], font_style)
        row_num += 1
        row = [
            "",
            "Всего: "+str(all_get),
            "Всего: "+str(all_rec),
            "Всего: "+str(all_nrec),
            "Всего: "+str(all_lost),
        ]
        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 3
        font_style.alignment.horz = 3
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response



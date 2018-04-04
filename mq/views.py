from datetime import datetime

from django.http import JsonResponse
from django.utils import timezone


def dt(orig: [datetime, None]) -> [float, None]:
    return None if not orig else timezone.localtime(orig).timestamp()


def get_object(request):
    model = request.GET["model"].split(".")
    pk = request.GET["pk"]
    d = {}
    app = model[0]
    mdl = model[2]
    if app == "directions":
        import directions.models as directions

        if mdl == "IstochnikiFinansirovaniya":
            if directions.IstochnikiFinansirovaniya.objects.filter(pk=pk).exists():
                n = directions.IstochnikiFinansirovaniya.objects.get(pk=pk)
                d["pk"] = n.pk
                d["title"] = n.title
                d["base"] = n.base_id

        elif mdl == "Napravleniya":
            if directions.Napravleniya.objects.filter(pk=pk).exists():
                n = directions.Napravleniya.objects.get(pk=pk)
                d["pk"] = n.pk
                d["history_num"] = n.history_num
                d["data_sozdaniya"] = dt(n.data_sozdaniya)
                d["client"] = n.client_id
                d["diagnos"] = n.diagnos
                d["doc"] = n.doc_id
                d["doc_who_create"] = n.doc_who_create_id
                d["istochnik_f"] = n.istochnik_f_id
                d["cancel"] = n.cancel
                d["result_rmis_send"] = n.result_rmis_send

        elif mdl == "TubesRegistration":
            if directions.TubesRegistration.objects.filter(pk=pk).exists():
                t = directions.TubesRegistration.objects.get(pk=pk)
                d["pk"] = t.pk
                d["type"] = t.type.tube_id
                d["doc_get"] = None if not t.doc_get else t.doc_get_id
                d["time_get"] = dt(t.time_get)
                d["doc_recive"] = None if not t.doc_recive else t.doc_recive_id
                d["time_recive"] = dt(t.time_recive)
                d["notice"] = t.notice

        elif mdl == "Issledovaniya":
            if directions.Issledovaniya.objects.filter(pk=pk).exists():
                i = directions.Issledovaniya.objects.get(pk=pk)
                d["pk"] = i.pk
                d["direction"] = i.napravleniye_id
                d["research"] = i.research_id
                d["tubes"] = [x.pk for x in i.tubes.all()]
                d["doc_save"] = None if not i.doc_save else i.doc_save_id
                d["time_save"] = dt(i.time_save)
                d["doc_confirmation"] = None if not i.doc_confirmation else i.doc_confirmation_id
                d["time_confirmation"] = dt(i.time_confirmation)
                d["lab_comment"] = i.lab_comment

        elif mdl == "Result":
            if directions.Result.objects.filter(pk=pk):
                r = directions.Result.objects.get(pk=pk)
                d["pk"] = r.pk
                d["issledovaniye"] = r.issledovaniye_id
                d["fraction"] = r.fraction_id
                d["value"] = r.value
                d["units"] = r.units
                d["is_normal"] = r.is_normal

        elif mdl == "ParaclinicResult":
            if directions.ParaclinicResult.objects.filter(pk=pk):
                r = directions.ParaclinicResult.objects.get(pk=pk)
                d["pk"] = r.pk
                d["issledovaniye"] = r.issledovaniye_id
                d["field"] = r.field_id
                d["value"] = r.value

    elif app == "clients":
        import clients.models as clients

        if mdl == "Individual":
            if clients.Individual.objects.filter(pk=pk):
                i = clients.Individual.objects.get(pk=pk)
                d["pk"] = i.pk
                d["family"] = i.family
                d["name"] = i.name
                d["patronymic"] = i.patronymic
                d["birthday"] = i.bd()
                d["sex"] = i.sex

        elif mdl == "Card":
            if clients.Card.objects.filter(pk=pk):
                c = clients.Card.objects.get(pk=pk)
                d["pk"] = c.pk
                d["number"] = c.number
                d["base"] = c.base_id
                d["individual"] = c.individual_id
                d["is_archive"] = c.is_archive

        elif mdl == "CardBase":
            if clients.CardBase.objects.filter(pk=pk):
                c = clients.CardBase.objects.get(pk=pk)
                d["pk"] = c.pk
                d["title"] = c.title
                d["short_title"] = c.short_title

    elif app == "podrazdeleniya":
        import podrazdeleniya.models as podrazdeleniya

        if mdl == "Podrazdeleniya":
            if podrazdeleniya.Podrazdeleniya.objects.filter(pk=pk):
                i = podrazdeleniya.Podrazdeleniya.objects.get(pk=pk)
                d["pk"] = i.pk
                d["title"] = i.title
                d["short_title"] = i.short_title
                d["p_type"] = i.p_type

    elif app == "users":
        import users.models as users

        if mdl == "DoctorProfile":
            if users.DoctorProfile.objects.filter(pk=pk):
                i = users.DoctorProfile.objects.get(pk=pk)
                d["pk"] = i.pk
                d["username"] = i.user.username
                d["fio"] = i.fio
                d["podrazdeleniye"] = i.podrazdeleniye_id

    elif app == "researches":
        import researches.models as researches

        if mdl == "Tubes":
            if researches.Tubes.objects.filter(pk=pk):
                i = researches.Tubes.objects.get(pk=pk)
                d["pk"] = i.pk
                d["color"] = i.color
                d["title"] = i.title
                d["short_title"] = i.get_short_title()

    elif app == "directory":
        import directory.models as directory

        if mdl == "Researches":
            if directory.Researches.objects.filter(pk=pk):
                i = directory.Researches.objects.get(pk=pk)
                d["pk"] = i.pk
                d["title"] = i.title
                d["short_title"] = i.get_title()
                d["podrazdeleniye"] = i.podrazdeleniye_id
                d["is_paraclinic"] = i.is_paraclinic
                d["code"] = i.code

        elif mdl == "Fractions":
            if directory.Fractions.objects.filter(pk=pk):
                i = directory.Fractions.objects.get(pk=pk)
                d["pk"] = i.pk
                d["title"] = i.title
                d["research"] = i.research_id
                d["order"] = i.sort_weight
                d["code"] = i.code

        elif mdl == "ParaclinicInputGroups":
            if directory.ParaclinicInputGroups.objects.filter(pk=pk):
                i = directory.ParaclinicInputGroups.objects.get(pk=pk)
                d["pk"] = i.pk
                d["title"] = i.title
                d["research"] = i.research_id
                d["order"] = i.order

        elif mdl == "ParaclinicInputField":
            if directory.ParaclinicInputField.objects.filter(pk=pk):
                i = directory.ParaclinicInputField.objects.get(pk=pk)
                d["pk"] = i.pk
                d["title"] = i.title
                d["group"] = i.group_id
                d["order"] = i.order

    return JsonResponse(d)


def get_directory(request):
    import clients.models as clients
    import directions.models as directions
    import podrazdeleniya.models as podrazdeleniya
    import users.models as users
    import researches.models as researches
    import directory.models as directory

    d = {
        "clients.models.CardBase": [{
            "pk": x.pk,
            "title": x.title,
            "short_title": x.short_title
        } for x in clients.CardBase.objects.all().order_by("pk")],

        "directions.models.IstochnikiFinansirovaniya": [{
            "pk": x.pk,
            "title": x.title,
            "base": x.base_id
        } for x in directions.IstochnikiFinansirovaniya.objects.all().order_by("pk")],

        "podrazdeleniya.models.Podrazdeleniya.TYPES": [{"pk": x[0], "title": x[1]} for x in
                                                       podrazdeleniya.Podrazdeleniya.TYPES],

        "podrazdeleniya.models.Podrazdeleniya": [{
            "pk": x.pk,
            "title": x.title,
            "short_title": x.get_title(),
            "p_type": x.p_type
        } for x in podrazdeleniya.Podrazdeleniya.objects.all().order_by("pk")],

        "users.models.DoctorProfile": [{
            "pk": x.pk,
            "username": x.user.username,
            "fio": x.fio,
            "podrazdeleniye": x.podrazdeleniye_id
        } for x in users.DoctorProfile.objects.all().order_by("pk")],

        "researches.models.Tubes": [{
            "pk": x.pk,
            "color": x.color,
            "title": x.title,
            "short_title": x.get_short_title()
        } for x in researches.Tubes.objects.all().order_by("pk")],

        "directory.models.Researches": [{
            "pk": x.pk,
            "title": x.title,
            "short_title": x.get_title(),
            "podrazdeleniye": x.podrazdeleniye_id,
            "is_paraclinic": x.is_paraclinic,
            "code": x.code,
        } for x in directory.Researches.objects.all().order_by("pk")],

        "directory.models.Fractions": [{
            "pk": x.pk,
            "title": x.title,
            "research": x.research_id,
            "order": x.sort_weight,
            "code": x.code,
        } for x in directory.Fractions.objects.all().order_by("pk")],

        "directory.models.ParaclinicInputGroups": [{
            "pk": x.pk,
            "title": x.title,
            "research": x.research_id,
            "order": x.order,
        } for x in directory.ParaclinicInputGroups.objects.all().order_by("pk")],

        "directory.models.ParaclinicInputField": [{
            "pk": x.pk,
            "title": x.title,
            "group": x.group_id,
            "order": x.order,
        } for x in directory.ParaclinicInputField.objects.all().order_by("pk")],
    }

    return JsonResponse(d)

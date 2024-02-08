import simplejson as json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import directions.models as directions
import directory.models as direct
import slog.models as slog
from directory.models import Researches, ReleationsFT, Fractions, DirectionsGroup
from podrazdeleniya.models import Podrazdeleniya


@csrf_exempt
@login_required
def directory_researches(request):
    """GET: получение списка исследований для лаборатории. POST: добавление нового исследования"""
    return_result = {"tubes_r": []}
    if request.method == "POST":
        research = json.loads(request.POST["research"])
        # if not research["title"] or not research["id"] or directions.Issledovaniya.objects.filter(
        #        research__pk=int(research["id"])).exists():
        if not research["title"] or not research["id"]:
            return_result = {"ok": False, "tubes_r": []}
        else:
            if research["id"] == -1:
                research_obj = Researches(podrazdeleniye=Podrazdeleniya.objects.get(pk=research["lab"]))
            else:
                research_obj = Researches.objects.get(pk=int(research["id"]))

            research_obj.title = research["title"]
            research_obj.short_title = research["shortTitle"]
            if not research["preparation"]:
                research["preparation"] = "Не требуется"
            research_obj.preparation = research["preparation"]
            research_obj.code = research["nmu"]
            research_obj.internal_code = research.get("internalCode") or ''
            research_obj.save()
            if research["id"] == -1:
                pass
            # slog.Log(key=str(research_obj.pk), type=type, body="{'data': " + request.POST["research"] + "}",
            #          user=request.user.doctorprofile).save()
            # Fractions.objects.filter(research=research_obj).delete()
            fractions_pk = []
            return_result["F"] = []
            sort_list = [0]
            for key in research["fraction"].keys():
                tube_relation = ReleationsFT.objects.get(pk=int(key.split("-")[1]))
                for fr in Fractions.objects.filter(relation=tube_relation):
                    sort_list.append(fr.research.sort_weight)
                for fraction in research["fraction"][key]["fractions"]:
                    if int(fraction["pk"]) < 0:
                        fraction_obj = Fractions(
                            title=fraction["title"],
                            research=research_obj,
                            units=fraction["units"],
                            relation=tube_relation,
                            ref_m=json.dumps(fraction["ref_m"]),
                            ref_f=json.dumps(fraction["ref_f"]),
                            variants=direct.ResultVariants.objects.get(pk=fraction["type"]),
                        )
                        fraction_obj.save()
                        return_result["F"].append((tube_relation.pk, fraction_obj.pk, key, int(key.split("-")[1])))
                    else:
                        fraction_obj = Fractions.objects.get(pk=fraction["pk"])
                        fraction_obj.title = fraction["title"]
                        fraction_obj.research = research_obj
                        fraction_obj.units = fraction["units"]
                        fraction_obj.ref_m = fraction["ref_m"]
                        fraction_obj.ref_f = fraction["ref_f"]
                        fraction_obj.variants = None if not direct.ResultVariants.objects.filter(pk=fraction["type"]).exists() else direct.ResultVariants.objects.get(pk=fraction["type"])
                        fractions_pk.append(fraction["pk"])
                    fraction_obj.sort_weight = fraction["num"]
                    fraction_obj.save()
            if research["id"] == -1:
                research_obj.sort_weight = max(sort_list) + 1
                research_obj.save()
            # fL = Fractions.objects.filter()
            '''fractions = Fractions.objects.filter(research=research_obj)
            for fraction in fractions:
                if fraction.pk not in fractions_pk:
                    fraction.delete()'''
            return_result = {"ok": True, "id": research_obj.pk, "title": research_obj.title, "tubes_r": return_result["tubes_r"], "F": return_result["F"]}
    elif request.method == "GET":
        return_result = {"researches": []}
        researches = Researches.objects.filter(podrazdeleniye__pk=request.GET["lab"]).order_by("sort_weight")
        i = 0
        for research in researches:
            i += 1
            resdict = {
                "pk": research.pk,
                "title": research.title,
                "shortTitle": research.get_title(),
                "tubes": {},
                "tubes_c": 0,
                "readonly": False,
                "hide": research.hide,
                "sort_weight": research.sort_weight,
            }
            if directions.Issledovaniya.objects.filter(research=research).exists():
                resdict["readonly"] = True
            fractions = Fractions.objects.filter(research=research).order_by("pk", "sort_weight")
            for fraction in fractions:
                if fraction.relation_id not in resdict["tubes"].keys():
                    resdict["tubes_c"] += 1
                    resdict["tubes"][fraction.relation_id] = {
                        "id": fraction.relation_id,
                        "color": fraction.relation.tube.color,
                        "title": fraction.relation.tube.title,
                        "num": fraction.sort_weight,
                    }
            return_result["researches"].append(resdict)
        return_result["researches"] = sorted(return_result["researches"], key=lambda d: d["pk"])
    return JsonResponse(return_result)


@csrf_exempt
@login_required
def directory_researches_list(request):
    """GET: получение списка исследований для лаборатории"""
    return_result = []
    if request.method == "POST":
        lab_id = request.POST["lab_id"]
    else:
        lab_id = request.GET["lab_id"]
    researches = (
        Researches.objects.filter(podrazdeleniye__pk=lab_id, hide=False).order_by("title").values("pk", "onlywith", "onlywith__pk", "title", "comment_variants", "comment_variants__pk")
    )
    labs = Podrazdeleniya.objects.filter(p_type=Podrazdeleniya.LABORATORY).values("pk")
    for r in researches:
        autoadd = {lab["pk"]: [x["b__pk"] for x in direct.AutoAdd.objects.filter(a__pk=r["pk"], b__podrazdeleniye__pk=lab["pk"]).values("b__pk")] for lab in labs}
        addto = {lab["pk"]: [x["a__pk"] for x in direct.AutoAdd.objects.filter(b__pk=r["pk"], a__podrazdeleniye__pk=lab["pk"]).values("a__pk")] for lab in labs}

        return_result.append(
            {
                "pk": r["pk"],
                "id": r["pk"],
                "onlywith": -1 if not r["onlywith"] else r["onlywith__pk"],
                "fields": {"id_lab_fk": lab_id, "ref_title": r["title"]},
                "isFolder": False,
                "text": r["title"],
                "comment_template": "-1" if r["comment_variants"] is None else r["comment_variants__pk"],
                "autoadd": autoadd,
                "addto": addto,
            }
        )

    return JsonResponse(return_result, safe=False)


@csrf_exempt
@login_required
def directory_researches_update_uet(request):
    """POST: обновление УЕТов"""
    return_result = {"ok": False}
    if request.method == "POST":
        b = json.loads(request.body)
        pk = b["pk"]
        fraction = Fractions.objects.get(pk=pk)
        fraction.uet_doc = b["doc"]
        fraction.uet_co_executor_1 = b["co1"]
        fraction.uet_co_executor_2 = b["co2"]
        fraction.save()
        return_result["ok"] = True
    return JsonResponse(return_result)


@csrf_exempt
@login_required
def directory_researches_update_mode(request):
    """POST: обновление режима для лаборанта"""
    return_result = {"ok": False}
    if request.method == "POST":
        pk = request.POST["pk"]
        value = request.POST["value"]
        if value != "":
            research = Researches.objects.get(pk=pk)
            research.edit_mode = value
            research.save()
            return_result["ok"] = True
    return JsonResponse(return_result)


@csrf_exempt
@login_required
def directory_researches_update_sort(request):
    """POST: обновление сортировки"""
    return_result = {"ok": False}
    if request.method == "POST":
        sort = json.loads(request.POST["sort"])
        for k in sort.keys():
            res = Researches.objects.get(pk=int(k))
            res.sort_weight = sort[k]
            res.save()
        return_result["ok"] = True
    return JsonResponse(return_result)


@csrf_exempt
@login_required
def directory_toggle_hide_research(request):
    """
    Переключение скрытия исследования для выписки
    :param request:
    :return:
    """
    if request.method == "POST":
        pk = request.POST["pk"]
    else:
        pk = request.GET["pk"]
    research = Researches.objects.get(pk=int(pk))
    research.hide = not research.hide
    research.save()
    slog.Log(key=pk, type=19, body=json.dumps({"hide": research.hide}), user=request.user.doctorprofile).save()
    return JsonResponse({"status_hide": research.hide})


@csrf_exempt
@login_required
def directory_copy_research(request):
    """
    Копирование исследования
    :param request:
    :return:
    """
    if request.method == "POST":
        pk = request.POST["pk"]
    else:
        pk = request.GET["pk"]
    research = Researches.objects.get(pk=int(pk))
    research.pk = None
    research.save()
    return JsonResponse({"pk": research.pk})


@csrf_exempt
@login_required
def directory_research(request):
    """GET: получение исследования и фракций"""
    from collections import OrderedDict

    return_result = {}
    if request.method == "GET":
        id = int(request.GET["id"])
        research = Researches.objects.get(pk=id)
        return_result["title"] = research.title
        return_result["shortTitle"] = research.short_title
        return_result["lab"] = research.podrazdeleniye.get_title()
        return_result["nmu"] = research.code
        return_result["internalCode"] = research.internal_code or ''
        return_result["preparation"] = research.preparation
        return_result["edit_mode"] = research.edit_mode
        return_result["readonly"] = bool(directions.Issledovaniya.objects.filter(research=research).exists())
        return_result["hide"] = research.hide
        return_result["onlywith"] = research.onlywith_id or -1
        return_result["fractiontubes"] = OrderedDict()
        return_result["co_executor_mode"] = research.co_executor_mode
        return_result["co_executor_title"] = research.co_executor_2_title
        return_result["uet_doc"] = {}
        return_result["uet_co_executor_1"] = {}
        return_result["uet_co_executor_2"] = {}
        fractions = Fractions.objects.filter(research=research).order_by("pk", "relation__tube__id", "sort_weight")
        for fraction in fractions:
            if "tube-" + str(fraction.relation_id) not in return_result["fractiontubes"].keys():
                return_result["fractiontubes"]["tube-" + str(fraction.relation_id)] = {
                    "fractions": [],
                    "color": fraction.relation.tube.color,
                    "title": fraction.relation.tube.title,
                    "sel": "tube-" + str(fraction.relation_id),
                }
            return_result["uet_doc"][fraction.pk] = fraction.uet_doc
            return_result["uet_co_executor_1"][fraction.pk] = fraction.uet_co_executor_1
            return_result["uet_co_executor_2"][fraction.pk] = fraction.uet_co_executor_2
            ref_m = fraction.ref_m
            ref_f = fraction.ref_f
            if isinstance(ref_m, str):
                ref_m = json.loads(ref_m)
            if isinstance(ref_f, str):
                ref_f = json.loads(ref_f)
            u = fraction.get_unit()
            return_result["fractiontubes"]["tube-" + str(fraction.relation_id)]["fractions"].append(
                {
                    "title": fraction.title,
                    "units": fraction.units,
                    "unit": u.pk if u else None,
                    "ref_m": ref_m,
                    "ref_f": ref_f,
                    "pk": fraction.pk,
                    "type": 1 if not fraction.variants else fraction.variants_id,
                    "type_values": [] if not fraction.variants else fraction.variants.get_variants(),
                    "num": fraction.sort_weight,
                }
            )
        for key in return_result["fractiontubes"].keys():
            return_result["fractiontubes"][key]["fractions"] = sorted(return_result["fractiontubes"][key]["fractions"], key=lambda k: k['num'])
    return JsonResponse(return_result)


@csrf_exempt
@login_required
def directory_researches_group(request):
    """GET: получение списка исследований для группы. POST: добавление новой или выбор существующей группы и привязка исследований к ней"""
    return_result = {}
    if request.method == "GET":
        return_result = {"researches": []}
        gid = int(request.GET["gid"])
        researches = Researches.objects.all()
        if request.GET["lab"] != "-1":
            if request.GET["lab"] == "-2":
                researches = researches.filter(is_microbiology=True)
            else:
                researches = researches.filter(podrazdeleniye__pk=request.GET["lab"])
        else:
            researches = researches.filter(podrazdeleniye__isnull=False)

        for research in researches.order_by("title", "podrazdeleniye", "hide"):
            resdict = {"pk": research.pk, "title": "{}{} | {}".format({True: "Скрыто | "}.get(research.hide, ""), research.get_title(), research.get_podrazdeleniye_title())}
            if gid < 0:
                if not research.direction:
                    return_result["researches"].append(resdict)
            else:
                if research.direction and research.direction_id == gid:
                    return_result["researches"].append(resdict)

    elif request.method == "POST":
        gid = int(request.POST["group"])
        if gid < 0:
            direction = DirectionsGroup()
            direction.save()
            type = 5
        else:
            direction = DirectionsGroup.objects.get(pk=gid)
            type = 6
        slog.Log(key=direction.pk, type=type, body="{'data': " + request.POST["researches"] + "}", user=request.user.doctorprofile).save()
        tmp_researches = Researches.objects.filter(direction=direction)
        for v in tmp_researches:
            v.direction = None
            v.save()

        researches = json.loads(request.POST["researches"])
        for k in researches.keys():
            if researches[k]:
                if k == "" or not k.isdigit() or not Researches.objects.filter(pk=k).exists():
                    continue
                research = Researches.objects.get(pk=k)
                research.direction = direction
                research.save()

        return_result["gid"] = direction.pk

    return JsonResponse(return_result)


@csrf_exempt
@login_required
def directory_get_directions(request):
    """GET: получение списка групп (по направлениям)"""
    return_result = {}
    if request.method == "GET":
        return_result = {"directions": {}}
        researches = Researches.objects.filter(not_grouping=False)
        if request.GET["lab"] != "-1":
            if request.GET["lab"] == "-2":
                researches = researches.filter(is_microbiology=True)
            else:
                researches = researches.filter(podrazdeleniye__pk=request.GET["lab"])
        for research in researches.order_by("title"):
            if not research.direction:
                continue
            if research.direction_id not in return_result["directions"].keys():
                return_result["directions"][research.direction_id] = []
            return_result["directions"][research.direction_id].append(research.title)

    return JsonResponse(return_result)


@csrf_exempt
@login_required
def researches_get_details(request):
    """GET: получение детальной информации из анализа"""
    return_result = {}
    if request.method == "GET":
        pk = request.GET["pk"]
        research_obj = Researches.objects.get(pk=pk)
        return_result["title"] = research_obj.title
        return_result["instructions"] = research_obj.instructions
        return_result["comment_template"] = research_obj.comment_variants_id or "-1"
        return_result["edit_mode"] = research_obj.edit_mode
        return_result["fractions"] = []
        return_result["template"] = research_obj.template
        for fraction in Fractions.objects.filter(research=research_obj).order_by("sort_weight"):
            return_result["fractions"].append(
                {
                    "pk": fraction.pk,
                    "title": fraction.title,
                    "hide": fraction.hide,
                    "render_type": fraction.render_type,
                    "formula": fraction.formula,
                    "sw": fraction.sort_weight,
                    "options": fraction.options,
                    "fsli": fraction.get_fsli_code() or '',
                }
            )
    else:
        data = json.loads(request.POST["data"])
        for row in data:
            if Fractions.objects.filter(pk=row["pk"]).exists():
                temp_fraction = Fractions.objects.get(pk=row["pk"])
                temp_fraction.hide = row["hide"]
                temp_fraction.render_type = row["render_type"]
                temp_fraction.options = row["options"]
                temp_fraction.formula = row["formula"].strip()
                if "fsli" in row:
                    temp_fraction.fsli = row["fsli"].strip() or None
                temp_fraction.save()
        return_result["ok"] = True
    return JsonResponse(return_result)


@csrf_exempt
@login_required
def researches_update_template(request):
    """POST: установка шаблона формы ввода результата"""
    return_result = {"ok": False}
    if request.method == "POST":
        pk = request.POST["pk"]
        research_obj = Researches.objects.get(pk=pk)
        research_obj.template = int(request.POST["template"])
        research_obj.instructions = request.POST.get("instructions", "")
        research_obj.comment_variants = None if request.POST["comment_template"] == "-1" else direct.MaterialVariants.objects.get(pk=request.POST["comment_template"])
        research_obj.save()
        return_result["ok"] = True
        # return_result["comment_template_saved"] = research_obj.comment_template
        # return_result["comment_template"] = request.POST["comment_template"]
    return JsonResponse(return_result)

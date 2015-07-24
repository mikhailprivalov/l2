from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from directory.models import Researches, Subgroups, ReleationsFT, Fractions
import simplejson as json


@csrf_exempt
@login_required
def directory_researches(request):
    return_result = {}
    if request.method == "POST":
        research = json.loads(request.POST["research"])
        if not research["title"] or not research["id"]:
            return_result = {"ok": False}
        else:
            if research["id"] == -1:
                research_obj = Researches(subgroup=Subgroups.objects.get(pk=research["lab_group"]))
            else:
                research_obj = Researches.objects.get(pk=research["id"])
            research_obj.title = research["title"]
            if not research["preparation"]:
                research["preparation"] = "Не требуется"
            research_obj.preparation = research["preparation"]
            if not research["quota_oms"] or research["quota_oms"] < 0:
                research["quota_oms"] = -1
            research_obj.quota_oms = research["quota_oms"]
            research_obj.save()
            Fractions.objects.filter(research=research_obj).delete()
            for key in research["fraction"].keys():
                tube_relation = ReleationsFT.objects.get(pk=key.split("-")[1])
                for fraction in research["fraction"][key]["fractions"]:
                    fraction_obj = Fractions(title=fraction["title"], research=research_obj, units=fraction["units"],
                                             relation=tube_relation, ref_m=json.dumps(fraction["ref_m"]),
                                             ref_f=json.dumps(fraction["ref_f"]))
                    fraction_obj.save()
            return_result = {"ok": True, "id": research_obj.pk, "title": research_obj.title}
    elif request.method == "GET":
        return_result = {"researches": []}
        subgroup_id = request.GET["lab_group"]
        researches = Researches.objects.filter(subgroup__pk=subgroup_id)
        for research in researches:
            resdict = {"pk": research.pk, "title": research.title, "tubes": {}, "tubes_c": 0}
            fractions = Fractions.objects.filter(research=research)
            for fraction in fractions:
                if fraction.relation.pk not in resdict["tubes"].keys():
                    resdict["tubes_c"] += 1
                    resdict["tubes"][fraction.relation.pk] = {"id": fraction.relation.pk,
                                                              "color": fraction.relation.tube.color,
                                                              "title": fraction.relation.tube.title}
            return_result["researches"].append(resdict)

    return HttpResponse(json.dumps(return_result), content_type="application/json")  # Создание JSON


@csrf_exempt
@login_required
def directory_research(request):
    return_result = {}
    if request.method == "GET":
        id = int(request.GET["id"])
        research = Researches.objects.get(pk=id)
        return_result["title"] = research.title
        return_result["quota"] = research.quota_oms
        return_result["preparation"] = research.preparation
        return_result["fractiontubes"] = {}
        fractions = Fractions.objects.filter(research=research)
        for fraction in fractions:
            if "tube-" + str(fraction.relation.pk) not in return_result["fractiontubes"].keys():
                return_result["fractiontubes"]["tube-" + str(fraction.relation.pk)] = {"fractions": [],
                                                                                       "color": fraction.relation.tube.color,
                                                                                       "title": fraction.relation.tube.title,
                                                                                       "sel": "tube-" + str(
                                                                                           fraction.relation.pk)}

            return_result["fractiontubes"]["tube-" + str(fraction.relation.pk)]["fractions"].append(
                {"title": fraction.title, "units": fraction.units, "ref_m": json.loads(fraction.ref_m),
                 "ref_f": json.loads(fraction.ref_f)});

        '''
        sel: id,
        color: color,
        title: title,
        '''
    return HttpResponse(json.dumps(return_result), content_type="application/json")  # Создание JSON

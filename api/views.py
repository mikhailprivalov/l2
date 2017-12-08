import simplejson as json
import yaml
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

import api.models as models
import directions.models as directions
import users.models as users
from api.to_astm import get_iss_astm
from barcodes.views import tubes
from slog import models as slog


def translit(locallangstring):
    """
    Translit func
    :param locallangstring: orign
    :return: translit of locallangstring
    """
    conversion = {
        u'\u0410': 'A', u'\u0430': 'a',
        u'\u0411': 'B', u'\u0431': 'b',
        u'\u0412': 'V', u'\u0432': 'v',
        u'\u0413': 'G', u'\u0433': 'g',
        u'\u0414': 'D', u'\u0434': 'd',
        u'\u0415': 'E', u'\u0435': 'e',
        u'\u0401': 'Yo', u'\u0451': 'yo',
        u'\u0416': 'Zh', u'\u0436': 'zh',
        u'\u0417': 'Z', u'\u0437': 'z',
        u'\u0418': 'I', u'\u0438': 'i',
        u'\u0419': 'Y', u'\u0439': 'y',
        u'\u041a': 'K', u'\u043a': 'k',
        u'\u041b': 'L', u'\u043b': 'l',
        u'\u041c': 'M', u'\u043c': 'm',
        u'\u041d': 'N', u'\u043d': 'n',
        u'\u041e': 'O', u'\u043e': 'o',
        u'\u041f': 'P', u'\u043f': 'p',
        u'\u0420': 'R', u'\u0440': 'r',
        u'\u0421': 'S', u'\u0441': 's',
        u'\u0422': 'T', u'\u0442': 't',
        u'\u0423': 'U', u'\u0443': 'u',
        u'\u0424': 'F', u'\u0444': 'f',
        u'\u0425': 'H', u'\u0445': 'h',
        u'\u0426': 'Ts', u'\u0446': 'ts',
        u'\u0427': 'Ch', u'\u0447': 'ch',
        u'\u0428': 'Sh', u'\u0448': 'sh',
        u'\u0429': 'Sch', u'\u0449': 'sch',
        u'\u042a': '', u'\u044a': '',
        u'\u042b': 'Y', u'\u044b': 'y',
        u'\u042c': '', u'\u044c': '',
        u'\u042d': 'E', u'\u044d': 'e',
        u'\u042e': 'Yu', u'\u044e': 'yu',
        u'\u042f': 'Ya', u'\u044f': 'ya',
    }
    translitstring = []
    for c in locallangstring:
        translitstring.append(conversion.setdefault(c, c))
    return ''.join(translitstring)


@csrf_exempt
def send(request):
    """
    Sysmex save results
    :param request:
    :return:
    """
    result = {"ok": False}
    try:
        if request.method == "POST":
            resdict = yaml.load(request.POST["result"])
            appkey = request.POST.get("key", "")
        else:
            resdict = yaml.load(request.GET["result"])
            appkey = request.GET.get("key", "")

        astm_user = users.DoctorProfile.objects.filter(user__username="astm").first()
        resdict["pk"] = int(resdict.get("pk", -111))
        if "LYMPH%" in resdict["result"]:
            resdict["orders"] = {}

        dpk = -1
        if "bydirection" in request.POST or "bydirection" in request.GET:
            dpk = resdict["pk"]

            if dpk >= 4600000000000:
                dpk -= 4600000000000
                dpk //= 10
            tubes(request, direction_implict_id=dpk)
            if directions.TubesRegistration.objects.filter(issledovaniya__napravleniye__pk=dpk, issledovaniya__doc_confirmation__isnull=True).exists():
                resdict["pk"] = directions.TubesRegistration.objects.filter(
                    issledovaniya__napravleniye__pk=dpk, issledovaniya__doc_confirmation__isnull=True).order_by("pk").first().pk
            else:
                resdict["pk"] = False
        result["A"] = appkey
        if resdict["pk"] and models.Application.objects.filter(key=appkey).exists() and models.Application.objects.get(key=appkey).active and directions.TubesRegistration.objects.filter(pk=resdict["pk"]).exists():
            tubei = directions.TubesRegistration.objects.get(pk=resdict["pk"])
            direction = tubei.issledovaniya_set.first().napravleniye
            for key in resdict["result"].keys():
                if models.RelationFractionASTM.objects.filter(astm_field=key).exists():
                    fractionRels = models.RelationFractionASTM.objects.filter(astm_field=key)
                    for fractionRel in fractionRels:
                        fraction = fractionRel.fraction
                        if directions.Issledovaniya.objects.filter(napravleniye=direction,
                                                                   research=fraction.research, doc_confirmation__isnull=True).exists():
                            issled = directions.Issledovaniya.objects.filter(napravleniye=direction,
                                                                             research=fraction.research, doc_confirmation__isnull=True).order_by("pk")[0]
                            fraction_result = None
                            if directions.Result.objects.filter(issledovaniye=issled,
                                                                fraction=fraction).exists():  # Если результат для фракции существует
                                fraction_result = directions.Result.objects.get(issledovaniye=issled,
                                                                                fraction__pk=fraction.pk)  # Выборка результата из базы
                            else:
                                fraction_result = directions.Result(issledovaniye=issled,
                                                                    fraction=fraction)  # Создание нового результата
                            fraction_result.value = str(resdict["result"][key]).strip()  # Установка значения
                            if fraction_result.value.isdigit():
                                fraction_result.value = "%s.0" % fraction_result.value
                            import re
                            find = re.findall("\d+.\d+", fraction_result.value)
                            if len(find) > 0:
                                val = float(find[0]) * fractionRel.get_multiplier_display()
                                if fractionRel.full_round:
                                    val = round(val)
                                fraction_result.value = fraction_result.value.replace(find[0], str(val))

                            fraction_result.iteration = 1  # Установка итерации
                            ref = fractionRel.default_ref
                            if ref:
                                fraction_result.ref_title = ref.title
                                fraction_result.ref_about = ref.about
                                fraction_result.ref_m = ref.m
                                fraction_result.ref_f = ref.f
                            fraction_result.save()  # Сохранение
                            issled.api_app = models.Application.objects.get(key=appkey)
                            issled.save()
                            fraction_result.get_ref(re_save=True)
                            fraction_result.issledovaniye.doc_save = astm_user  # Кто сохранил
                            from datetime import datetime
                            fraction_result.issledovaniye.time_save = timezone.now()  # Время сохранения
                            fraction_result.issledovaniye.save()
            slog.Log(key=appkey, type=22, body=json.dumps(resdict), user=None).save()
            result["ok"] = True
        elif not directions.TubesRegistration.objects.filter(pk=resdict["pk"]).exists():
            if dpk > -1:
                resdict["pk"] = dpk
            slog.Log(key=resdict["pk"], type=23, body=json.dumps(resdict), user=None).save()
    except Exception as e:
        result = {"ok": False, "Exception": True, "MSG": str(e)}
    return JsonResponse(result)


def endpoint(request):
    result = {"answer": False, "body": ""}
    data = json.loads(request.POST.get("data", request.GET.get("data", "{}")))
    api_key = data.get("api_key", "")
    message_type = data.get("message_type", "C")
    pk_s = str(data.get("pk", ""))
    pk = -1 if not pk_s.isdigit() else int(pk_s)
    data["app_name"] = "API key is incorrect"
    if models.Application.objects.filter(key=api_key).exists():
        astm_user = users.DoctorProfile.objects.filter(user__username="astm").first()
        if astm_user is None:
            astm_user = users.DoctorProfile.objects.filter(user__is_staff=True).order_by("pk").first()
        app = models.Application.objects.get(key=api_key)
        if app.active:
            data["app_name"] = app.name
            if message_type == "R":
                if pk != -1:
                    dw = app.direction_work
                    if pk >= 4600000000000:
                        pk -= 4600000000000
                        pk //= 10
                        dw = True
                    if dw:
                        direction = directions.Napravleniya.objects.filter(pk=pk)
                    else:
                        direction = directions.Napravleniya.objects.filter(issledovaniya__tubes__pk=pk)
                    results = data.get("result", {})
                    for key in results:
                        ok = False
                        q = models.RelationFractionASTM.objects.filter(astm_field=key)
                        if q.filter(application_api=app).exists():
                            q = q.filter(application_api=app)
                            ok = True
                        elif q.filter(application_api__isnull=True).exists():
                            q = q.filter(application_api__isnull=True)
                            ok = True
                        if ok:
                            for fraction_rel in q:
                                if directions.Issledovaniya.objects.filter(napravleniye=direction, research=fraction_rel.research, doc_confirmation__isnull=True).exists():
                                    for issled in directions.Issledovaniya.objects.filter(napravleniye=direction, research=fraction_rel.research, doc_confirmation__isnull=True):
                                        if directions.Result.objects.filter(issledovaniye=issled, fraction=fraction_rel.fraction).exists():
                                            fraction_result = directions.Result.objects.get(issledovaniye=issled, fraction=fraction_rel.fraction)
                                        else:
                                            fraction_result = directions.Result(issledovaniye=issled, fraction=fraction_rel.fraction)
                                        fraction_result.value = str(results[key]).strip()
                                        import re
                                        find = re.findall("\d+.\d+", fraction_result.value)
                                        if len(find) > 0:
                                            val_str = fraction_result.value
                                            for f in find:
                                                val = app.truncate(float(f) * fraction_rel.get_multiplier_display())
                                                val_str = val_str.replace(f, str(val))
                                            fraction_result.value = val_str

                                        fraction_result.iteration = 1
                                        ref = fraction_rel.default_ref
                                        if ref:
                                            fraction_result.ref_title = ref.title
                                            fraction_result.ref_about = ref.about
                                            fraction_result.ref_m = ref.m
                                            fraction_result.ref_f = ref.f
                                        fraction_result.save()
                                        issled.api_app = app
                                        issled.save()
                                        fraction_result.get_ref(re_save=True)
                                        fraction_result.issledovaniye.doc_save = astm_user
                                        fraction_result.issledovaniye.time_save = timezone.now()
                                        fraction_result.issledovaniye.save()
                else:
                    request["body"] = "pk '{}' is not exists".format(pk_s)
            elif message_type == "Q":
                result["answer"] = True
                pks = [int(x) for x in data.get("query", [])]
                result["body"] = [x.decode('ascii') for x in get_iss_astm(app.get_issledovaniya(pks), app)]
            else:
                pass
        else:
            data["app_name"] = "API app banned"
            request["body"] = "API app banned"
    else:
        request["body"] = "API key is incorrect"
    slog.Log(key=pk, type=6000, body=json.dumps(data), user=None).save()
    return JsonResponse(result)

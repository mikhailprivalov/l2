from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import api.models as models
import simplejson as json
import directions.models as directions
import directory.models as directory
import users.models as users

@csrf_exempt
def send(request):
    result = {"ok": False}
    resdict = json.loads(request.REQUEST["result"].replace("'", "\""))
    key = request.REQUEST["key"]
    if resdict["pk"] and resdict["pk"].isdigit() and key and models.Application.objects.filter(key=key).exists():
        direction = directions.Napravleniya.objects.get(pk=resdict["pk"])
        for key in resdict["result"].keys():
            if models.RelationFractionASTM.objects.filter(astm_field=key).exists():
                fractionRel = models.RelationFractionASTM.objects.filter(astm_field=key).first()
                fraction = fractionRel.fraction
                if directions.Issledovaniya.objects.filter(napravleniye=direction,research=fraction.research).exists():
                    issled = directions.Issledovaniya.objects.get(napravleniye=direction,research=fraction.research)
                    fraction_result = None
                    if directions.Result.objects.filter(issledovaniye=issled,
                                             fraction=fraction).exists():  # Если результат для фракции существует
                        fraction_result = directions.Result.objects.get(issledovaniye=issled,
                                                             fraction__pk=fraction.pk)  # Выборка результата из базы
                    else:
                        fraction_result = directions.Result(issledovaniye=issled,
                                                 fraction=fraction)  # Создание нового результата
                    fraction_result.value = resdict["result"][key]  # Установка значения
                    if fractionRel.get_multiplier_display() > 1:
                        import re
                        find = re.findall("\d+.\d+", fraction_result.value)
                        if len(find) > 0:
                            val = int(float(find[0]) * fractionRel.get_multiplier_display())
                            fraction_result.value = fraction_result.value.replace(find[0], str(val))
                    fraction_result.iteration = 1  # Установка итерации
                    fraction_result.save()  # Сохранение
                    fraction_result.issledovaniye.doc_save = users.DoctorProfile.objects.filter(user__pk=866).first()  # Кто сохранил
                    from datetime import datetime
                    fraction_result.issledovaniye.time_save = datetime.now()  # Время сохранения
                    fraction_result.issledovaniye.save()
        result["ok"] = True
    return HttpResponse(json.dumps(result), content_type="application/json")  # Создание JSON
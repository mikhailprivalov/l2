import codecs

from rest_framework.response import Response
from rest_framework.decorators import api_view
from api.models import Application
from directions.models import Napravleniya
import simplejson as json
from results.sql_func import get_paraclinic_results_by_direction
from xml_generate.views import gen_result_cda_files


@api_view(['POST'])
def data_by_direction(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    token = token.replace("Bearer ", "")
    if not token:
        return Response({"message": "token is empty"})
    token_is_not_valid = False
    try:
        app = Application.objects.filter(active=True, key=token).first()
        if not app:
            token_is_not_valid = True
    except:
        token_is_not_valid = True

    if token_is_not_valid:
        return Response({"message": "token is not valid"})

    data = json.loads(request.body)
    direction_id = data.get("directionId")
    direction = Napravleniya.objects.filter(pk=direction_id).first()
    result_l2 = get_direction_data_by_cda_group(direction.pk)

    result_tempalte = gen_result_cda_files("protocol/proto.js", result_l2)

    result = {
        "patient": {
            "family": "",
            "name": "",
            "patronymic": "",
            "birthday": "",
        },
        "service": {
            "date": "",
            "time": "",
            "protocol": "",
            "mainDiagnos": "",
            "code": "",
        },
        "doctor": {
            "additionalInfo": ""
        },
    }

    return Response({"direction": result_tempalte})


def get_direction_data_by_cda_group(direction_pk):
    result = get_paraclinic_results_by_direction(direction_pk)
    data = {}
    for i in result:
        if i.cda_field_code and i.value:
            if not data.get(i.cda_field_code):
                data[i.cda_field_code] = [{i.title: i.value}]
            else:
                data[i.cda_field_code].append({i.title: i.value})
            continue
        if i.cda_group_code and i.value:
            if not data.get(i.cda_group_code):
                data[i.cda_group_code] = [{i.title: i.value}]
            else:
                data[i.cda_group_code].append({i.title: i.value})
    temp_result = {}
    for k, v in data.items():
        s = ""
        for j in v:
            for key, val in j.items():
                if key:
                    s = f"{s}{key}: {val};"
                else:
                    s = f"{s}{val};"
        temp_result[k] = s
    final_result = {str(k): string_to_unicode_escape(v) for k, v in temp_result.items()}

    return {"data": final_result}


def string_to_unicode_escape(text):
    symbols_data = ''.join(f'\\u{ord(char):04x}' for char in text)
    return symbols_data

def from_escape(escaped_text):
    return codecs.decode(escaped_text, 'unicode_escape')

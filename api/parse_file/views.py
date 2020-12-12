from django.http import HttpRequest

from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json
from api.views import endpoint


def dnk_covid(request):
    prefixes = []
    var_A = [f"A{i}" for i in range(1, 13)]
    prefixes.extend(var_A)
    var_B = [f"B{i}" for i in range(1, 13)]
    prefixes.extend(var_B)
    var_C = [f"C{i}" for i in range(1, 13)]
    prefixes.extend(var_C)
    var_D = [f"D{i}" for i in range(1, 13)]
    prefixes.extend(var_D)
    var_E = [f"E{i}" for i in range(1, 13)]
    prefixes.extend(var_E)
    var_F = [f"F{i}" for i in range(1, 13)]
    prefixes.extend(var_F)
    var_G = [f"G{i}" for i in range(1, 13)]
    prefixes.extend(var_G)
    var_H = [f"H{i}" for i in range(1, 13)]
    prefixes.extend(var_H)
    var_I = [f"I{i}" for i in range(1, 13)]
    prefixes.extend(var_I)
    var_J = [f"J{i}" for i in range(1, 13)]
    prefixes.extend(var_J)
    var_K = [f"K{i}" for i in range(1, 13)]
    prefixes.extend(var_K)

    req = json.loads(request.body)
    file_data = req.get('file_data', False)
    if file_data:
        text = extract_text_from_pdf(file_data)
        if text:
            text.replace("\n", "").split("Коронавирусы подобные SARS-CoVВККоронавирус SARS-CoV-2")
        for i in text:
            if "+" in i:
                k = i.split("N")
                if k[1].split(" ")[0].isdigit():
                    http_func({"pk": k[1].split(" ")[0], "result": "Положительно"}, request.user)
            else:
                k = i.split("N")
                if k[1].split(" ")[0].isdigit():
                    http_func({"pk": k[1].split(" ")[0], "result": "Отрицательно"}, request.user)


def http_func(data, user):
    json_data = json.dumps(data)
    http_obj = HttpRequest()
    http_obj._body = json_data
    http_obj.user = user
    endpoint(http_obj)

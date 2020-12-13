from django.http import HttpRequest

from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json
from api.views import endpoint


def dnk_covid(request):
    prefixes = []
    for x in "ABCDEF":
        for i in range(1, 13):
            prefixes.append(f"{x}{i}")

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

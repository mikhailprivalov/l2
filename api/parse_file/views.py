from django.http import HttpRequest

from api.parse_file.pdf import extract_text_from_pdf
import simplejson as json
from api.views import endpoint


def dnk_covid(request):
    prefixes = []
    for x in "ABCDEF":
        prefixes.extend([f"{x}{i}" for i in range(1, 13)])
    req = json.loads(request.body)
    file_data = req.get('file_data', False)
    if file_data:
        text = extract_text_from_pdf(file_data)
        if text:
            text.replace("\n", "").split("Коронавирусы подобные SARS-CoVВККоронавирус SARS-CoV-2")
        for i in text:
            k = i.split("N")
            if len(k) > 1 and k[1].split(" ")[0].isdigit():
                result = json.dumps({"pk": k[1].split(" ")[0], "result": [{"dnk_SARS": "Положительно" if "+" in i else "Отрицательно"}]})
                http_func({"key": 'xxxx', "result": result}, request.user)


def http_func(data, user):
    http_obj = HttpRequest()
    http_obj.POST.update(data)
    http_obj.user = user
    endpoint(http_obj)


def load_file(request):
    pass

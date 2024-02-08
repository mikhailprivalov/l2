import simplejson as json
from rest_framework.response import Response
from integration_framework.researches.sql_func import get_confirm_research
from laboratory.utils import current_time
from rest_framework.decorators import api_view


@api_view()
def get_confirm_sign_research(request):
    if not hasattr(request.user, "hospitals"):
        return Response({"ok": False, "message": "Некорректный auth токен"})

    body = json.loads(request.body)
    research_id = body.get("researchId")
    date_start = body.get("dateStart", current_time(only_date=True))
    date_start = f"{date_start} 00:00:01"
    date_end = body.get("dateEnd", current_time(only_date=True))
    date_end = f"{date_end} 23:59:59"
    result = get_confirm_research(research_id, date_start, date_end)
    count_mo = {}
    for i in result:
        if not count_mo.get(i.title_mo):
            count_mo[i.title_mo] = 1
        else:
            count_mo[i.title_mo] += 1
    return Response(count_mo)

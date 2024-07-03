from directions.models import Issledovaniya


def form_01(request_data):
    file = request_data.get("file")
    issledovanie_id = request_data.get("entity_id")
    file = request_data.get("file")
    issledovanie: Issledovaniya = Issledovaniya.objects.filter(pk=issledovanie_id).select_related('research').first()
    print(file)
    print(issledovanie_id)
    print(issledovanie)
    print(issledovanie.research.title)
    return {"ok": True, "result": [], "message": ""}

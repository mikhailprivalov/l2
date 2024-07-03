from django.http import HttpRequest

from directions.models import Issledovaniya, IssledovaniyaFiles


def form_01(request_data):
    file = request_data.get("file")
    user = request_data.get('user')
    issledovanie_id = request_data.get("entity_id")
    issledovanie: Issledovaniya = Issledovaniya.objects.filter(pk=issledovanie_id).select_related('research').first()
    if issledovanie:
        iss_files = IssledovaniyaFiles.objects.filter(issledovaniye_id=issledovanie.pk)
        if file and iss_files.count() >= 5:
            return {"ok": False, "result": [], "message": "Вы добавили слишком много файлов в одну заявку"}

        if file and file.size > 5242880:
            return {"ok": False, "result": [], "message": "Файл слишком большой"}

        iss = IssledovaniyaFiles(issledovaniye_id=issledovanie.pk, uploaded_file=file, who_add_files=user.doctorprofile)
        iss.save()
    else:
        return {"ok": False, "result": [], "message": "Нет такого исследования"}
    return {"ok": True, "result": [], "message": ""}

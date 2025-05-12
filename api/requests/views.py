# import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import time

from laboratory.decorators import group_required
from utils.response import status_response


@login_required
@group_required('Создание и исполнение заявок')
def get_requests(request):
    # request_data = json.loads(request.body)
    # date = request_data.get('date')
    # search_type = request_data.get('searchType')

    time.sleep(0.3)

    rows = [
        {
            "id": 1,
            "patient": "Patient 1",
            "datetime": "2024-06-01 10:30",
            "hasImage": True,
            "cardId": 123,
        },
        {
            "id": 2,
            "patient": "Patient 2",
            "datetime": "2024-06-02 12:00",
            "hasImage": False,
            "cardId": 456,
        },
        {
            "id": 3,
            "patient": "Patient 3",
            "datetime": "2024-06-03 09:15",
            "hasImage": True,
            "cardId": 123,
        },
    ]

    return JsonResponse({"rows": rows})


@login_required
@group_required('Создание и исполнение заявок')
def get_equipment_list(request):
    time.sleep(0.3)

    rows = [
        {
            "id": 1,
            "label": "Рентген 2232",
        },
        {
            "id": 2,
            "label": "МРТ 43",
        },
        {
            "id": 3,
            "label": "МРТ 21",
        },
    ]

    return JsonResponse({"rows": rows})


@login_required
@group_required('Создание и исполнение заявок')
def get_request_images(request):
    # request_data = json.loads(request.body)
    # date = request_data.get('date')
    # equipment_id = request_data.get('equipmentId')

    time.sleep(0.3)

    rows = [
        {
            "id": 1,
            "datetime": "01.06.2024 10:00",
            "equipment": 1,
            "linked": False,
            "patient": "IVANOV IVAN",
            "requestNumber": None,
            "equipmentImageId": "RX-1001",
        },
        {
            "id": 2,
            "datetime": "01.06.2024 11:30",
            "equipment": 1,
            "linked": True,
            "patient": "PETROV PETR",
            "requestNumber": "REQ-223",
            "equipmentImageId": "RX-1002",
        },
        {
            "id": 3,
            "datetime": "01.06.2024 09:15",
            "equipment": 2,
            "linked": False,
            "patient": "SOKOLOV SERGEY",
            "requestNumber": None,
            "equipmentImageId": "MR-4301",
        },
        {
            "id": 4,
            "datetime": "02.06.2024 14:00",
            "equipment": 3,
            "linked": False,
            "patient": "IVANOVA ANNA",
            "requestNumber": None,
            "equipmentImageId": "MR-2101",
        },
        {
            "id": 5,
            "datetime": "01.06.2024 12:45",
            "equipment": 2,
            "linked": True,
            "patient": "KUZNETSOV DMITRY",
            "requestNumber": "REQ-224",
            "equipmentImageId": "MR-4302",
        },
    ]

    return JsonResponse({"rows": rows})


@login_required
@group_required('Создание и исполнение заявок')
def create_request(request):
    time.sleep(0.3)

    return status_response(True, "Заявка успешно создана")

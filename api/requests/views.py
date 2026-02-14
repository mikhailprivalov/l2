import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.core.files.base import ContentFile
import base64
import uuid
from django.utils import timezone

from appconf.manager import SettingManager
from laboratory.decorators import group_required
from laboratory.utils import strfdatetime
from utils.response import status_response
from directions.models import Napravleniya, IstochnikiFinansirovaniya, NapravleniyaFiles
from clients.models import Card
from integration_framework.models import EquipmentReceive
from users.models import DoctorProfileEquipment, PermissionHospitalProtocolDoctorProfile


def get_allowed_hospital_ids(doctor_profile):
    permissions = PermissionHospitalProtocolDoctorProfile.objects.filter(doctor_profile=doctor_profile)
    return [p.hospital_id for p in permissions if p.hospital_id]


def check_hospital_access(doctor_profile, hospital_id):
    if hospital_id == -1:
        allowed_ids = get_allowed_hospital_ids(doctor_profile)
        if not allowed_ids:
            raise ValueError("У пользователя нет доступа ни к одной организации")
        return allowed_ids
    else:
        allowed_ids = get_allowed_hospital_ids(doctor_profile)
        if hospital_id not in allowed_ids:
            raise ValueError("У пользователя нет доступа к указанной организации")
        return [hospital_id]


@login_required
@group_required('Создание и исполнение заявок')
def get_requests(request):
    request_data = json.loads(request.body)
    date_from = request_data.get('dateFrom')
    date_to = request_data.get('dateTo')
    search_type = request_data.get('searchType', 'all')
    card_id = request_data.get('cardId')
    only_mine = request_data.get('onlyMine', False)
    offset = request_data.get('offset', 0)
    limit = request_data.get('limit', 50)

    directions = (
        Napravleniya.objects.filter(is_request=True)
        .select_related("client__individual", "doc")
        .prefetch_related('issledovaniya_set__research')
        .prefetch_related('napravleniyafiles_set')
        .order_by("-data_sozdaniya")
    )

    if search_type in ('search', 'card'):
        hospital_id = request.user.doctorprofile.hospital_id
        if hospital_id:
            directions = directions.filter(hospital_id=hospital_id)
        else:
            directions = directions.filter(doc=request.user.doctorprofile)
        if only_mine:
            directions = directions.filter(doc=request.user.doctorprofile)
    else:
        directions = directions.filter(doc=request.user.doctorprofile)

    if search_type == 'card' and card_id:
        directions = directions.filter(client_id=card_id)

    if search_type == 'cancel':
        directions = directions.filter(cancel=True)
    else:
        directions = directions.filter(cancel=False)

    if date_from and date_to:
        try:
            search_date_from = datetime.strptime(date_from, '%d.%m.%Y').date()
            search_date_to = datetime.strptime(date_to, '%d.%m.%Y').date()
            directions = directions.filter(
                data_sozdaniya__date__gte=search_date_from,
                data_sozdaniya__date__lte=search_date_to,
            )
        except ValueError:
            pass

    total_count = directions.count()
    directions_list = list(directions[offset : offset + limit])

    direction_ids = [d.pk for d in directions_list]
    equipment_receives = set(EquipmentReceive.objects.filter(napravleniye_id__in=direction_ids).values_list('napravleniye_id', flat=True))

    rows = []
    for direction in directions_list:
        has_image = direction.pk in equipment_receives
        files = [
            {
                "id": f.pk,
                "name": f.uploaded_file.name.split('/')[-1] if f.uploaded_file else 'Файл',
                "url": f.uploaded_file.url if f.uploaded_file else '',
            }
            for f in direction.napravleniyafiles_set.all()
        ]

        research_titles = []
        for iss in direction.issledovaniya_set.all():
            if iss.research and iss.research.short_title:
                research_titles.append(iss.research.short_title)
            elif iss.research and iss.research.title:
                research_titles.append(iss.research.title)

        rows.append(
            {
                "id": direction.pk,
                "patient": direction.client.individual.fio(),
                "datetime": strfdatetime(direction.data_sozdaniya, '%d.%m.%Y %H:%M'),
                "hasImage": has_image,
                "hasResult": direction.total_confirmed,
                "cardId": direction.client.pk,
                "files": files,
                "researchTitle": research_titles[0] if research_titles else "",
                "isCito": direction.is_cito,
                "creator": direction.doc.get_fio() if direction.doc and direction.doc != request.user.doctorprofile else "",
            }
        )

    return JsonResponse({"rows": rows, "total": total_count, "hasMore": offset + limit < total_count})


@login_required
@group_required('Создание и исполнение заявок')
def get_equipment_list(request):
    doctor_equipments = DoctorProfileEquipment.objects.filter(doctor_profile=request.user.doctorprofile).select_related('equipment')

    rows = [
        {
            "id": doctor_equipment.equipment.pk,
            "label": doctor_equipment.equipment.title,
        }
        for doctor_equipment in doctor_equipments
        if doctor_equipment.equipment
    ]

    return JsonResponse({"rows": rows})


@login_required
@group_required('Создание и исполнение заявок')
def get_request_images(request):
    request_data = json.loads(request.body)
    date = request_data.get('date')
    equipment_id = request_data.get('equipmentId')
    page = request_data.get('page', 1)
    page_size = request_data.get('pageSize', 50)
    last_id = request_data.get('lastId')

    if not equipment_id:
        return JsonResponse({"rows": [], "hasMore": False, "total": 0})

    doctor_equipment = DoctorProfileEquipment.objects.filter(doctor_profile=request.user.doctorprofile, equipment_id=equipment_id).first()

    if not doctor_equipment:
        return JsonResponse({"rows": [], "hasMore": False, "total": 0})

    rows = []
    has_more = False
    total = 0

    if date:
        try:
            date_parts = date.split('.')
            search_date = f'{date_parts[2]}-{date_parts[1]}-{date_parts[0]}'
            equipment = doctor_equipment.equipment

            base_queryset = EquipmentReceive.objects.filter(
                created_at__date=search_date,
                equipment_model=equipment,
            ).select_related('napravleniye__client__individual', 'doc_save_link', 'doc_reset_link')

            total = base_queryset.count()

            equipment_receives_query = base_queryset.order_by('-created_at')

            if last_id:
                equipment_receives_query = equipment_receives_query.filter(id__lt=last_id)

            offset = (page - 1) * page_size if not last_id else 0
            equipment_receives = equipment_receives_query[offset : offset + page_size + 1]

            equipment_receives_list = list(equipment_receives)

            if len(equipment_receives_list) > page_size:
                has_more = True
                equipment_receives_list = equipment_receives_list[:page_size]
            else:
                has_more = False

            for equipment_receive in equipment_receives_list:
                is_linked = equipment_receive.napravleniye and equipment_receive.napravleniye.is_request

                patient_fio = ""
                if equipment_receive.napravleniye and equipment_receive.napravleniye.client:
                    patient_fio = equipment_receive.napravleniye.client.individual.fio()
                else:
                    # patient_fio = f"{equipment_receive.family} {equipment_receive.name} {equipment_receive.patronymic}".strip()
                    patient_fio = equipment_receive.tag_patient_name

                rows.append(
                    {
                        "id": equipment_receive.pk,
                        "family": equipment_receive.family,
                        "name": equipment_receive.name,
                        "patronymic": equipment_receive.patronymic,
                        "birthday": equipment_receive.birthday.strftime('%d.%m.%Y') if equipment_receive.birthday else '',
                        "sex": equipment_receive.sex,
                        "patientId": equipment_receive.tag_patient_id,
                        "orderId": equipment_receive.order_id,
                        "patient": patient_fio,
                        "datetime": strfdatetime(equipment_receive.created_at),
                        "linked": is_linked,
                        "requestId": equipment_receive.napravleniye_id or None,
                        "equipmentId": str(equipment_receive.id),
                    }
                )

        except ValueError:
            pass

    return JsonResponse({"rows": rows, "hasMore": has_more, "total": total})


@login_required
@group_required('Создание и исполнение заявок')
def get_image_details(request):
    request_data = json.loads(request.body)
    image_id = request_data.get('imageId')

    if not image_id:
        return JsonResponse({"success": False, "message": "ID изображения не указан"})

    equipment_receive = EquipmentReceive.objects.select_related('napravleniye__client__individual', 'napravleniye__doc', 'doc_save_link', 'doc_reset_link').get(pk=image_id)

    equipment = equipment_receive.equipment_model

    if not equipment:
        return JsonResponse({"success": False, "message": "Оборудование не найдено"})

    doctor_equipment = DoctorProfileEquipment.objects.filter(doctor_profile=request.user.doctorprofile, equipment=equipment).first()

    if not doctor_equipment:
        return JsonResponse({"success": False, "message": "Нет доступа к этому изображению"})

    is_linked = equipment_receive.napravleniye and equipment_receive.napravleniye.is_request

    details = {
        "id": equipment_receive.pk,
        "studyInstanceUidTag": equipment_receive.study_instance_uid_tag,
        "napravleniyeId": equipment_receive.napravleniye_id,
        "family": equipment_receive.family,
        "name": equipment_receive.name,
        "patronymic": equipment_receive.patronymic,
        "birthday": equipment_receive.birthday.strftime('%d.%m.%Y') if equipment_receive.birthday else None,
        "sex": equipment_receive.sex,
        "patientId": equipment_receive.tag_patient_id,
        "orderId": equipment_receive.order_id,
        "docSaveLink": equipment_receive.doc_save_link.get_fio() if equipment_receive.doc_save_link else None,
        "timeSaveLink": strfdatetime(equipment_receive.time_save_link) if equipment_receive.time_save_link else None,
        "docResetLink": equipment_receive.doc_reset_link.get_fio() if equipment_receive.doc_reset_link else None,
        "timeResetLink": strfdatetime(equipment_receive.time_reset_link) if equipment_receive.time_reset_link else None,
        "createdAt": strfdatetime(equipment_receive.created_at),
        "updatedAt": strfdatetime(equipment_receive.updated_at),
        "linked": is_linked,
        "equipmentTitle": equipment.title if equipment else None,
    }

    return JsonResponse({"success": True, "data": details})


@login_required
@group_required('Создание и исполнение заявок')
def create_request(request):
    request_data = json.loads(request.body)
    patient_id = request_data.get('patientId')
    research_id = request_data.get('researchId')
    request_fields = request_data.get('requestFields', {})

    if not patient_id or not research_id:
        return status_response(False, "Не указаны обязательные поля")

    if not request_fields.get('date') or not request_fields.get('time'):
        return status_response(False, "Не указана дата или время исследования")

    card = Card.objects.get(pk=patient_id)

    fin_source = IstochnikiFinansirovaniya.objects.filter(base=card.base, title="ОМС", hide=False).first()
    if not fin_source:
        fin_source = IstochnikiFinansirovaniya.objects.filter(base=card.base, hide=False).order_by('-order_weight').first()
    if not fin_source:
        return status_response(False, "Не найден источник финансирования")

    files = request_fields.get('files', [])
    for file_data in files:
        if 'url' in file_data and file_data['url'].startswith('data:'):
            _, data = file_data['url'].split(',', 1)
            file_content = base64.b64decode(data)
            file_size = len(file_content)
            if file_size > 10 * 1024 * 1024:
                return status_response(False, "Размер файла превышает 10 МБ")

    with transaction.atomic():
        result = Napravleniya.gen_napravleniya_by_issledovaniya(
            client_id=patient_id, diagnos="", finsource=fin_source.pk, history_num="", ofname_id=-1, doc_current=request.user.doctorprofile, researches={-1: [research_id]}, comments={}
        )

        if not result.get('r'):
            return status_response(False, result.get('message', 'Ошибка создания заявки'))

        direction_id = result['list_id'][0] if result['list_id'] else None
        if not direction_id:
            return status_response(False, "Не удалось получить ID заявки")

        direction = Napravleniya.objects.get(pk=direction_id)

        direction.is_cito = request_fields.get('cito', False)
        direction.is_request = True
        direction.contrast_amount = request_fields.get('contrastAmount', '')
        direction.dose = request_fields.get('dose', '')
        direction.anamnesis = request_fields.get('anamnesis', '')
        direction.direction_comment = request_fields.get('comment', '')
        direction.fact_research_date = request_fields.get('date', '') or None
        direction.fact_research_time = request_fields.get('time', '') or None
        direction.save(update_fields=['is_cito', 'is_request', 'contrast_amount', 'dose', 'anamnesis', 'direction_comment', 'fact_research_date', 'fact_research_time'])

        for file_data in files:
            if 'url' in file_data and file_data['url'].startswith('data:'):
                _, data = file_data['url'].split(',', 1)
                file_content = base64.b64decode(data)
                file_name = file_data.get('name', f'{uuid.uuid4()}.bin')

                django_file = ContentFile(file_content, name=file_name)

                napravleniya_file = NapravleniyaFiles(napravleniye=direction, uploaded_file=django_file)
                napravleniya_file.save()

    return status_response(True, "Заявка успешно создана", {"requestId": direction_id})


@login_required
@group_required('Создание и исполнение заявок')
def link_image_to_request(request):
    request_data = json.loads(request.body)
    image_id = request_data.get('imageId')
    request_id = request_data.get('requestId')

    if not image_id:
        return status_response(False, "ID изображения не указан")

    try:
        equipment_receive = EquipmentReceive.objects.get(pk=image_id)
    except EquipmentReceive.DoesNotExist:
        return status_response(False, "Изображение не найдено")

    equipment = equipment_receive.equipment_model

    if not equipment:
        return status_response(False, "Оборудование не найдено")

    doctor_equipment = DoctorProfileEquipment.objects.filter(doctor_profile=request.user.doctorprofile, equipment=equipment).first()

    if not doctor_equipment:
        return status_response(False, "Нет доступа к этому изображению")

    with transaction.atomic():
        if request_id:
            try:
                napravleniye = Napravleniya.objects.get(pk=request_id, is_request=True, doc=request.user.doctorprofile)
            except Napravleniya.DoesNotExist:
                return status_response(False, "Заявка не найдена")

            for iss in napravleniye.issledovaniya_set.all():
                iss.study_instance_uid = equipment_receive.study_instance_uid_tag
                iss.study_instance_uid_tag = equipment_receive.study_instance_uid_tag
                iss.save(update_fields=['study_instance_uid', 'study_instance_uid_tag'])

            equipment_receive.napravleniye = napravleniye
            equipment_receive.doc_save_link = request.user.doctorprofile
            equipment_receive.time_save_link = timezone.now()
            equipment_receive.doc_reset_link = None
            equipment_receive.time_reset_link = None
            equipment_receive.save(update_fields=['napravleniye', 'doc_save_link', 'time_save_link', 'doc_reset_link', 'time_reset_link'])

            return status_response(True, "Изображение успешно привязано к заявке")
        else:
            if equipment_receive.napravleniye:
                for iss in equipment_receive.napravleniye.issledovaniya_set.all():
                    iss.study_instance_uid = None
                    iss.study_instance_uid_tag = None
                    iss.save(update_fields=['study_instance_uid', 'study_instance_uid_tag'])
                equipment_receive.napravleniye = None
            equipment_receive.doc_reset_link = request.user.doctorprofile
            equipment_receive.time_reset_link = timezone.now()
            equipment_receive.save(update_fields=['napravleniye', 'doc_reset_link', 'time_reset_link'])

            return status_response(True, "Изображение отвязано от заявки")


@login_required
@group_required('Создание и исполнение заявок')
def get_request_details(request):
    request_data = json.loads(request.body)
    request_id = request_data.get('requestId')

    if not request_id:
        return JsonResponse({"success": False, "message": "ID заявки не указан"})

    try:
        direction = (
            Napravleniya.objects.select_related('client__individual', 'doc', 'doc_who_create')
            .prefetch_related('issledovaniya_set__research', 'napravleniyafiles_set')
            .get(pk=request_id, is_request=True)
        )
    except Napravleniya.DoesNotExist:
        return JsonResponse({"success": False, "message": "Заявка не найдена"})

    if direction.doc != request.user.doctorprofile:
        return JsonResponse({"success": False, "message": "Нет доступа к этой заявке"})

    researches = []
    for iss in direction.issledovaniya_set.all():
        if iss.research:
            researches.append(
                {
                    'id': iss.research.pk,
                    'title': iss.research.title,
                    'short_title': iss.research.short_title,
                }
            )

    files = []
    for file_obj in direction.napravleniyafiles_set.all():
        files.append(
            {
                'id': file_obj.pk,
                'name': file_obj.uploaded_file.name.split('/')[-1] if file_obj.uploaded_file else 'Файл',
                'url': file_obj.uploaded_file.url if file_obj.uploaded_file else '',
            }
        )

    has_image = EquipmentReceive.objects.filter(napravleniye_id=direction.pk).exists()

    details = {
        "id": direction.pk,
        "patient": direction.client.individual.fio(),
        "cardId": direction.client.pk,
        "datetime": strfdatetime(direction.data_sozdaniya, '%d.%m.%Y %H:%M'),
        "doctor": direction.doc.get_fio() if direction.doc else 'Не указан',
        "factResearchDate": strfdatetime(direction.fact_research_date, '%d.%m.%Y') if direction.fact_research_date else None,
        "factResearchTime": direction.fact_research_time.strftime('%H:%M') if direction.fact_research_time else None,
        "contrastAmount": direction.contrast_amount or '',
        "dose": direction.dose or '',
        "anamnesis": direction.anamnesis or '',
        "comment": direction.direction_comment or '',
        "isCito": direction.is_cito,
        "hasImage": has_image,
        "researches": researches,
        "files": files,
    }

    return JsonResponse({"success": True, "data": details})


@login_required
@group_required("Заполнение заявок")
def get_request_params(request):
    request_data = json.loads(request.body)
    request_id = request_data.get('requestId')
    hospital_id = request_data.get('hospitalId', -1)

    if not request_id:
        return JsonResponse({"success": False, "message": "ID заявки не указан"})

    try:
        allowed_hospital_ids = check_hospital_access(request.user.doctorprofile, hospital_id)
    except ValueError as e:
        return JsonResponse({"success": False, "message": str(e)})

    try:
        direction = Napravleniya.objects.select_related('client__individual', 'doc').prefetch_related('napravleniyafiles_set').get(pk=request_id, is_request=True)
    except Napravleniya.DoesNotExist:
        return JsonResponse({"success": False, "message": "Заявка не найдена"})

    if allowed_hospital_ids and direction.hospital_id not in allowed_hospital_ids:
        return JsonResponse({"success": False, "message": "У пользователя нет доступа к этой заявке"})

    params = {}

    if direction.doc:
        params["creator"] = direction.doc.get_fio()

    params["createdAt"] = strfdatetime(direction.data_sozdaniya, '%d.%m.%Y %H:%M')

    if direction.fact_research_date:
        params["researchDate"] = strfdatetime(direction.fact_research_date, '%d.%m.%Y')

    if direction.fact_research_time:
        params["researchTime"] = direction.fact_research_time.strftime('%H:%M')

    if direction.dose:
        params["dose"] = direction.dose

    if direction.contrast_amount:
        params["contrastAmount"] = direction.contrast_amount

    params["isCito"] = direction.is_cito

    equipment_receive = EquipmentReceive.objects.filter(napravleniye_id=direction.pk).first()
    params["hasImage"] = equipment_receive is not None
    if equipment_receive:
        params["imageId"] = equipment_receive.pk
        params["imageData"] = {
            "id": equipment_receive.pk,
            "studyInstanceUidTag": equipment_receive.study_instance_uid_tag,
            "family": equipment_receive.family,
            "name": equipment_receive.name,
            "patronymic": equipment_receive.patronymic,
            "birthday": equipment_receive.birthday.strftime('%d.%m.%Y') if equipment_receive.birthday else None,
            "sex": equipment_receive.sex,
            "patientId": equipment_receive.tag_patient_id,
            "orderId": equipment_receive.order_id,
            "createdAt": strfdatetime(equipment_receive.created_at),
            "equipmentTitle": equipment_receive.equipment_model.title if equipment_receive.equipment_model else None,
        }

    if direction.anamnesis:
        params["anamnesis"] = direction.anamnesis

    if direction.direction_comment:
        params["comment"] = direction.direction_comment

    files = []
    for file_obj in direction.napravleniyafiles_set.all():
        files.append({"name": file_obj.uploaded_file.name.split('/')[-1] if file_obj.uploaded_file else 'Файл', "url": file_obj.uploaded_file.url if file_obj.uploaded_file else ''})
    params["files"] = files

    return JsonResponse({"success": True, "params": params})


@login_required
@group_required('Создание и исполнение заявок')
def get_unlinked_requests(request):
    request_data = json.loads(request.body)
    date = request_data.get("date")

    directions = (
        Napravleniya.objects.filter(is_request=True, doc=request.user.doctorprofile)
        .select_related("client__individual")
        .prefetch_related('issledovaniya_set__research')
        .order_by("-data_sozdaniya")
    )

    if date:
        try:
            search_date = datetime.strptime(date, "%d.%m.%Y").date()
            directions = directions.filter(data_sozdaniya__date=search_date)
        except ValueError:
            pass

    rows = []
    for direction in directions:
        research_titles = []
        for iss in direction.issledovaniya_set.all():
            if iss.research and iss.research.short_title:
                research_titles.append(iss.research.short_title)
            elif iss.research and iss.research.title:
                research_titles.append(iss.research.title)

        rows.append(
            {
                "id": direction.pk,
                "patient": direction.client.individual.fio(),
                "datetime": strfdatetime(direction.data_sozdaniya, "%d.%m.%Y %H:%M"),
                "cardId": direction.client.pk,
                "researchTitle": research_titles[0] if research_titles else "",
            }
        )

    return JsonResponse({"rows": rows})


def direction_to_request(direction, doctor_profile):
    research_titles = []
    for iss in direction.issledovaniya_set.all():
        if iss.research and iss.research.short_title:
            research_titles.append(iss.research.short_title)
        elif iss.research and iss.research.title:
            research_titles.append(iss.research.title)

    return {
        "id": direction.pk,
        "patient": direction.client.individual.fio(short=True),
        "clinic": direction.doc.get_hospital_title() if direction.doc else "Не указан",
        "datetime": strfdatetime(direction.data_sozdaniya, "%H:%M"),
        "research": research_titles[0] if research_titles else "",
        "cardId": direction.client.pk,
        "waitFill": not direction.total_confirmed,
        "cito": direction.is_cito,
        "accepted": direction.accept_who_doctor is not None,
        "acceptedAt": strfdatetime(direction.accept_time) if direction.accept_time else None,
        "acceptedBy": direction.accept_who_doctor.get_fio() if direction.accept_who_doctor else None,
        "acceptedByCurrentUser": direction.accept_who_doctor == doctor_profile if direction.accept_who_doctor else False,
    }


@login_required
@group_required("Заполнение заявок")
def get_requests_by_status(request):
    request_data = json.loads(request.body)
    search_date = '-'.join(request_data.get("date").split(".")[::-1])
    is_done = request_data.get("isDone", False)
    hospital_id = request_data.get("hospitalId", -1)

    try:
        allowed_hospital_ids = check_hospital_access(request.user.doctorprofile, hospital_id)
    except ValueError as e:
        return JsonResponse({"rows": [], "error": str(e)})
    if SettingManager.get('show_directions_with_link_image', default='true', default_type='b'):
        directions = (
            Napravleniya.objects.filter(is_request=True, equipment_receive__isnull=False, equipment_receive__time_save_link__date=search_date)
            .select_related("client__individual", "doc")
            .prefetch_related("issledovaniya_set__research")
        )
    else:
        directions = (
            Napravleniya.objects.filter(is_request=True, data_sozdaniya__date=search_date).select_related("client__individual", "doc").prefetch_related("issledovaniya_set__research")
        )

    if allowed_hospital_ids:
        directions = directions.filter(hospital_id__in=allowed_hospital_ids)

    if is_done:
        directions = directions.filter(issledovaniya__doc_confirmation=request.user.doctorprofile, total_confirmed=True).order_by("-issledovaniya__time_confirmation").distinct()
    else:
        directions = directions.filter(total_confirmed=False).order_by("-last_confirmed_at").distinct()
    directions = directions.filter(cancel=False)

    directions_list = list(directions)

    rows = []
    for direction in directions_list:
        rows.append(direction_to_request(direction, request.user.doctorprofile))

    if not is_done:
        rows.sort(key=lambda x: (not x["cito"], -int(x["datetime"].replace(":", ""))))
    return JsonResponse({"rows": rows})


@login_required
@group_required("Заполнение заявок")
def get_request_by_number(request):
    request_data = json.loads(request.body)
    number = request_data.get("number")
    hospital_id = request_data.get("hospitalId", -1)

    try:
        allowed_hospital_ids = check_hospital_access(request.user.doctorprofile, hospital_id)
    except ValueError as e:
        return JsonResponse({"request": None, "error": str(e)})

    try:
        direction = Napravleniya.objects.get(pk=number, is_request=True)

        if allowed_hospital_ids and direction.hospital_id not in allowed_hospital_ids:
            return JsonResponse({"request": None, "error": "У пользователя нет доступа к этой заявке"})

        return JsonResponse({"request": direction_to_request(direction, request.user.doctorprofile)})
    except Napravleniya.DoesNotExist:
        return JsonResponse({"request": None, "error": "Заявка не найдена"})


@login_required
@group_required("Заполнение заявок")
def accept_request(request):
    request_data = json.loads(request.body)
    request_id = request_data.get("requestId")
    hospital_id = request_data.get("hospitalId", -1)

    if not request_id:
        return status_response(False, "ID заявки не указан")

    try:
        allowed_hospital_ids = check_hospital_access(request.user.doctorprofile, hospital_id)
    except ValueError as e:
        return status_response(False, str(e))

    with transaction.atomic():
        direction = Napravleniya.objects.select_for_update().get(pk=request_id, is_request=True)

        if allowed_hospital_ids and direction.hospital_id not in allowed_hospital_ids:
            return status_response(False, "У пользователя нет доступа к этой заявке")

        if direction.accept_who_doctor:
            if direction.accept_who_doctor == request.user.doctorprofile:
                return status_response(True, "Заявка уже принята вами")
            return status_response(False, "Заявка уже принята другим пользователем")

        now = timezone.now()
        direction.accept_who_doctor = request.user.doctorprofile
        direction.accept_time = now
        direction.save(update_fields=["accept_who_doctor", "accept_time"])

    return status_response(True, "Заявка успешно принята")


@login_required
@group_required("Заполнение заявок")
def cancel_accept_request(request):
    request_data = json.loads(request.body)
    request_id = request_data.get("requestId")
    hospital_id = request_data.get("hospitalId", -1)

    if not request_id:
        return status_response(False, "ID заявки не указан")

    try:
        allowed_hospital_ids = check_hospital_access(request.user.doctorprofile, hospital_id)
    except ValueError as e:
        return status_response(False, str(e))

    with transaction.atomic():
        direction = Napravleniya.objects.select_for_update().get(pk=request_id, is_request=True)

        if allowed_hospital_ids and direction.hospital_id not in allowed_hospital_ids:
            return status_response(False, "У пользователя нет доступа к этой заявке")

        if not direction.accept_who_doctor:
            return status_response(False, "Заявка не принята")

        if direction.accept_who_doctor != request.user.doctorprofile:
            return status_response(False, "Отменить принятие может только тот, кто принял заявку")

        confirmed_researches = direction.issledovaniya_set.filter(time_confirmation__isnull=False)
        if confirmed_researches.exists():
            return status_response(False, "Нельзя отменить принятие заявки, которая уже исполнена")

        direction.accept_who_doctor = None
        direction.accept_time = None
        direction.save(update_fields=["accept_who_doctor", "accept_time"])

    return status_response(True, "Принятие заявки отменено")


@login_required
@group_required("Заполнение заявок")
def get_permissions_doctor(request):
    access_hospital = PermissionHospitalProtocolDoctorProfile.get_access_hospital_by_doctor(request.user.doctorprofile)
    return JsonResponse({"hospitals": access_hospital})

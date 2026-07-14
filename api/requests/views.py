import json
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.core.files.base import ContentFile
import base64
import uuid
from django.conf import settings as django_settings
from django.utils import timezone

from appconf.manager import SettingManager
from brokers_queue.rmq.rentgen_publisher import send_request_to_rentgen_rmq, send_study_link_to_rentgen_rmq
from directory.models import Contrasts, Researches
from laboratory.decorators import group_required
from laboratory.utils import strfdatetime
from utils.response import status_response
from directions.models import Napravleniya, IstochnikiFinansirovaniya, NapravleniyaFiles
from clients.models import Card
from integration_framework.models import EquipmentReceive
from hospitals.models import Hospitals
from users.models import DoctorProfile, DoctorProfileEquipment, PermissionHospitalProtocolDoctorProfile
from slog.models import Log

ALL_LIST_PAGE_SIZE = 50
ALLOWED_ALL_LIST_PAGE_SIZES = {50, 100, 150}


def get_requests_journal_max_period_days():
    return getattr(django_settings, 'REQUESTS_JOURNAL_MAX_PERIOD_DAYS', 40)


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
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
                "acceptWhoDoctor": True if direction.accept_time else False,
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
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
        direction.is_dynamic = request_fields.get('isDynamic', False)
        direction.is_request = True
        direction.contrast_amount = request_fields.get('contrastAmount', '')
        direction.dose = request_fields.get('dose', '')
        direction.anamnesis = request_fields.get('anamnesis', '')
        direction.direction_comment = request_fields.get('comment', '')
        current_contrast = request_fields.get('currentContrast', -1)
        contrast_type = Contrasts.objects.filter(pk=int(current_contrast)).first()
        if contrast_type:
            direction.type_contrast = contrast_type
            direction.text_contrast = contrast_type.title
        direction.fact_research_date = request_fields.get('date', '') or None
        direction.fact_research_time = request_fields.get('time', '') or None
        direction.save(
            update_fields=[
                'is_cito',
                'is_request',
                'contrast_amount',
                'dose',
                'anamnesis',
                'direction_comment',
                'fact_research_date',
                'fact_research_time',
                'type_contrast',
                'text_contrast',
                'is_dynamic',
            ]
        )

        for file_data in files:
            if 'url' in file_data and file_data['url'].startswith('data:'):
                _, data = file_data['url'].split(',', 1)
                file_content = base64.b64decode(data)
                file_name = file_data.get('name', f'{uuid.uuid4()}.bin')

                django_file = ContentFile(file_content, name=file_name)

                napravleniya_file = NapravleniyaFiles(napravleniye=direction, uploaded_file=django_file)
                napravleniya_file.save()

    direction = Napravleniya.objects.select_related('client__individual', 'hospital', 'type_contrast').get(pk=direction_id)
    research = Researches.objects.filter(pk=research_id).first()
    send_request_to_rentgen_rmq(direction, request.user.doctorprofile, research)

    return status_response(True, "Заявка успешно создана", {"requestId": direction_id})


@login_required
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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

            send_study_link_to_rentgen_rmq(napravleniye, equipment_receive, request.user.doctorprofile)

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


def _is_request_editable(direction):
    return not direction.cancel and not direction.accept_who_doctor_id and not direction.total_confirmed


def _get_request_research_id(direction):
    for iss in direction.issledovaniya_set.all():
        if iss.research_id:
            return iss.research_id
    return None


def _get_request_research_title(direction):
    for iss in direction.issledovaniya_set.all():
        if iss.research:
            return iss.research.short_title or iss.research.title
    return ''


def _build_request_edit_snapshot(direction):
    files = [
        f.uploaded_file.name.split('/')[-1] if f.uploaded_file else 'Файл'
        for f in direction.napravleniyafiles_set.all()
    ]
    return {
        'researchId': _get_request_research_id(direction),
        'researchTitle': _get_request_research_title(direction),
        'date': str(direction.fact_research_date) if direction.fact_research_date else '',
        'time': direction.fact_research_time.strftime('%H:%M') if direction.fact_research_time else '',
        'dose': direction.dose or '',
        'cito': direction.is_cito,
        'isDynamic': direction.is_dynamic,
        'contrast': direction.text_contrast or '',
        'contrastAmount': direction.contrast_amount or '',
        'anamnesis': direction.anamnesis or '',
        'comment': direction.direction_comment or '',
        'files': files,
    }


def _build_edit_log_body(old_snapshot, new_snapshot):
    old = {}
    new = {}
    for key in new_snapshot:
        if old_snapshot.get(key) != new_snapshot.get(key):
            old[key] = old_snapshot.get(key)
            new[key] = new_snapshot.get(key)
    return {'old': old, 'new': new} if old else None


@login_required
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
        "isDynamic": direction.is_dynamic,
        "hasImage": has_image,
        "researches": researches,
        "files": files,
        "contrastText": direction.text_contrast or '',
        "editable": _is_request_editable(direction),
        "researchId": _get_request_research_id(direction),
        "currentContrast": direction.type_contrast_id or -1,
        "editDate": str(direction.fact_research_date) if direction.fact_research_date else '',
        "editTime": direction.fact_research_time.strftime('%H:%M') if direction.fact_research_time else '',
    }

    return JsonResponse({"success": True, "data": details})


@login_required
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
def update_request(request):
    request_data = json.loads(request.body)
    request_id = request_data.get('requestId')
    research_id = request_data.get('researchId')
    request_fields = request_data.get('requestFields', {})

    if not request_id:
        return status_response(False, "ID заявки не указан")

    if not research_id:
        return status_response(False, "Не указана услуга")

    if not request_fields.get('date') or not request_fields.get('time'):
        return status_response(False, "Не указана дата или время исследования")

    files = request_fields.get('files', [])
    for file_data in files:
        if 'url' in file_data and file_data['url'].startswith('data:'):
            _, data = file_data['url'].split(',', 1)
            file_content = base64.b64decode(data)
            if len(file_content) > 10 * 1024 * 1024:
                return status_response(False, "Размер файла превышает 10 МБ")

    try:
        direction = (
            Napravleniya.objects.select_related('type_contrast')
            .prefetch_related('issledovaniya_set__research', 'napravleniyafiles_set')
            .get(pk=request_id, is_request=True)
        )
    except Napravleniya.DoesNotExist:
        return status_response(False, "Заявка не найдена")

    if direction.doc != request.user.doctorprofile:
        return status_response(False, "Нет доступа к этой заявке")

    if not _is_request_editable(direction):
        return status_response(False, "Редактирование доступно только для новых заявок")

    if not Researches.objects.filter(pk=research_id).exists():
        return status_response(False, "Услуга не найдена")

    with transaction.atomic():
        old_snapshot = _build_request_edit_snapshot(direction)

        iss = direction.issledovaniya_set.first()
        if not iss:
            return status_response(False, "Исследование не найдено")

        if iss.research_id != research_id:
            iss.research_id = research_id
            iss.save(update_fields=['research'])

        direction.is_cito = request_fields.get('cito', False)
        direction.is_dynamic = request_fields.get('isDynamic', False)
        direction.contrast_amount = request_fields.get('contrastAmount', '')
        direction.dose = request_fields.get('dose', '')
        direction.anamnesis = request_fields.get('anamnesis', '')
        direction.direction_comment = request_fields.get('comment', '')
        current_contrast = request_fields.get('currentContrast', -1)
        contrast_type = Contrasts.objects.filter(pk=int(current_contrast)).first()
        if contrast_type:
            direction.type_contrast = contrast_type
            direction.text_contrast = contrast_type.title
        else:
            direction.type_contrast = None
            direction.text_contrast = ''
        direction.fact_research_date = request_fields.get('date', '') or None
        direction.fact_research_time = request_fields.get('time', '') or None
        direction.save(
            update_fields=[
                'is_cito',
                'is_dynamic',
                'contrast_amount',
                'dose',
                'anamnesis',
                'direction_comment',
                'fact_research_date',
                'fact_research_time',
                'type_contrast',
                'text_contrast',
            ]
        )

        for file_data in files:
            if 'url' in file_data and file_data['url'].startswith('data:'):
                _, data = file_data['url'].split(',', 1)
                file_content = base64.b64decode(data)
                file_name = file_data.get('name', f'{uuid.uuid4()}.bin')
                django_file = ContentFile(file_content, name=file_name)
                NapravleniyaFiles(napravleniye=direction, uploaded_file=django_file).save()

        direction = (
            Napravleniya.objects.select_related('type_contrast')
            .prefetch_related('issledovaniya_set__research', 'napravleniyafiles_set')
            .get(pk=request_id)
        )
        new_snapshot = _build_request_edit_snapshot(direction)
        log_body = _build_edit_log_body(old_snapshot, new_snapshot)
        if log_body:
            Log.log(key=request_id, type=250002, user=request.user.doctorprofile, body=log_body)

    direction = Napravleniya.objects.select_related('client__individual', 'hospital', 'type_contrast').get(pk=request_id)
    research = Researches.objects.filter(pk=research_id).first()
    send_request_to_rentgen_rmq(direction, request.user.doctorprofile, research)

    return status_response(True, "Заявка успешно обновлена")


@login_required
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики', 'Врач-диагностики')
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
    if direction.is_dynamic:
        params["isDynamic"] = direction.is_dynamic
    if direction.text_contrast:
        params["textContrast"] = direction.text_contrast

    files = []
    for file_obj in direction.napravleniyafiles_set.all():
        files.append({"name": file_obj.uploaded_file.name.split('/')[-1] if file_obj.uploaded_file else 'Файл', "url": file_obj.uploaded_file.url if file_obj.uploaded_file else ''})
    params["files"] = files

    return JsonResponse({"success": True, "params": params})


@login_required
@group_required('Создание и исполнение заявок', 'Лаборант-диагностики')
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
    podrzdeleniye_titles = []
    for iss in direction.issledovaniya_set.all():
        if iss.research and iss.research.short_title:
            research_titles.append(iss.research.short_title)
        elif iss.research and iss.research.title:
            research_titles.append(iss.research.title)
        podrzdeleniye_titles.append(iss.research.podrazdeleniye.title if iss.research.podrazdeleniye else "-")

    return {
        "id": direction.pk,
        "patient": direction.client.individual.fio(short=True),
        "clinic": direction.doc.get_hospital_title() if direction.doc else "Не указан",
        "datetime": strfdatetime(direction.data_sozdaniya, "%H:%M"),
        "orderDate": strfdatetime(direction.data_sozdaniya, "%d.%m"),
        "research": research_titles[0] if research_titles else "",
        "podrzdeleniye": podrzdeleniye_titles[0] if podrzdeleniye_titles else "-",
        "cardId": direction.client.pk,
        "waitFill": not direction.total_confirmed,
        "cito": direction.is_cito,
        "accepted": direction.accept_who_doctor is not None,
        "acceptedAt": strfdatetime(direction.accept_time) if direction.accept_time else None,
        "acceptedBy": direction.accept_who_doctor.get_fio() if direction.accept_who_doctor else None,
        "acceptedByCurrentUser": direction.accept_who_doctor == doctor_profile if direction.accept_who_doctor else False,
    }


def _parse_date_range(date_from, date_to, max_days=None):
    if max_days is None:
        max_days = get_requests_journal_max_period_days()
    if not date_from or not date_to:
        return None, None, None

    try:
        search_date_from = datetime.strptime(date_from, '%d.%m.%Y').date()
        search_date_to = datetime.strptime(date_to, '%d.%m.%Y').date()
    except ValueError:
        return None, None, 'Некорректный формат даты'

    if search_date_from > search_date_to:
        search_date_from, search_date_to = search_date_to, search_date_from

    if (search_date_to - search_date_from).days > max_days:
        return None, None, f'Период не может превышать {max_days} дней'

    return search_date_from, search_date_to, None


def _get_research_title(direction):
    for iss in direction.issledovaniya_set.all():
        if iss.research and iss.research.short_title:
            return iss.research.short_title
        if iss.research and iss.research.title:
            return iss.research.title
    return ''


def _get_last_confirmed_issledovaniya(direction):
    confirmed = [iss for iss in direction.issledovaniya_set.all() if iss.time_confirmation]
    if not confirmed:
        return None
    return max(confirmed, key=lambda iss: iss.time_confirmation)


def _get_request_status_label(direction):
    if direction.cancel:
        return 'Скрыта'
    if direction.total_confirmed:
        return 'Исполнена'
    if direction.accept_who_doctor_id:
        return 'В работе'
    if direction.is_cito:
        return 'CITO'
    return 'Новая'


def _get_journal_doctor_fio(direction, confirmed_by):
    if direction.total_confirmed and confirmed_by:
        return confirmed_by
    if direction.accept_who_doctor:
        return direction.accept_who_doctor.get_fio()
    return '—'


def direction_to_all_list_row(direction):
    last_confirmed = _get_last_confirmed_issledovaniya(direction)
    confirmed_by = None
    if last_confirmed:
        if last_confirmed.doc_confirmation:
            confirmed_by = last_confirmed.doc_confirmation.get_fio()
        elif last_confirmed.doc_confirmation_string:
            confirmed_by = last_confirmed.doc_confirmation_string

    hospital_title = 'Не указана'
    if direction.hospital:
        hospital_title = direction.hospital.short_title or direction.hospital.title

    return {
        'id': direction.pk,
        'hospital': hospital_title,
        'patient': direction.client.individual.fio(short=True),
        'research': _get_research_title(direction),
        'doctorFio': _get_journal_doctor_fio(direction, confirmed_by),
        'createdAt': strfdatetime(direction.data_sozdaniya, '%d.%m.%Y %H:%M'),
        'acceptedAt': strfdatetime(direction.accept_time, '%d.%m.%Y %H:%M') if direction.accept_time else None,
        'acceptedBy': direction.accept_who_doctor.get_fio() if direction.accept_who_doctor else None,
        'confirmedAt': strfdatetime(direction.last_confirmed_at, '%d.%m.%Y %H:%M') if direction.last_confirmed_at else None,
        'confirmedBy': confirmed_by,
        'status': _get_request_status_label(direction),
        'cito': direction.is_cito,
        'hidden': direction.cancel,
        'canHide': not direction.cancel,
    }


def _apply_status_filter(directions, statuses):
    if not statuses:
        return directions.filter(cancel=False)

    status_filter = Q()
    if 'hidden' in statuses:
        status_filter |= Q(cancel=True)
    if 'new' in statuses:
        status_filter |= Q(accept_who_doctor__isnull=True, total_confirmed=False, cancel=False)
    if 'cito' in statuses:
        status_filter |= Q(is_cito=True, cancel=False)
    if 'accepted' in statuses:
        status_filter |= Q(accept_who_doctor__isnull=False, total_confirmed=False, cancel=False)
    if 'confirmed' in statuses:
        status_filter |= Q(total_confirmed=True, cancel=False)

    return directions.filter(status_filter).distinct()


def _apply_doctor_filter(directions, doctor_id, statuses):
    if not doctor_id or doctor_id == -1:
        return directions

    doctor_q = Q()

    if not statuses:
        doctor_q = (
            Q(doc_id=doctor_id)
            | Q(accept_who_doctor_id=doctor_id)
            | Q(
                issledovaniya__doc_confirmation_id=doctor_id,
                issledovaniya__time_confirmation__isnull=False,
            )
        )
    else:
        if 'new' in statuses:
            doctor_q |= Q(
                doc_id=doctor_id,
                accept_who_doctor__isnull=True,
                total_confirmed=False,
                is_cito=False,
            )
        if 'cito' in statuses:
            doctor_q |= Q(is_cito=True) & (
                Q(doc_id=doctor_id, accept_who_doctor__isnull=True, total_confirmed=False)
                | Q(accept_who_doctor_id=doctor_id, total_confirmed=False)
                | Q(
                    total_confirmed=True,
                    issledovaniya__doc_confirmation_id=doctor_id,
                    issledovaniya__time_confirmation__isnull=False,
                )
            )
        if 'accepted' in statuses:
            doctor_q |= Q(accept_who_doctor_id=doctor_id, total_confirmed=False)
        if 'confirmed' in statuses:
            doctor_q |= Q(
                total_confirmed=True,
                issledovaniya__doc_confirmation_id=doctor_id,
                issledovaniya__time_confirmation__isnull=False,
            )

    return directions.filter(doctor_q).distinct()


def _apply_sort(directions, sort_by, sort_dir, default_order='-data_sozdaniya'):
    allowed_sort_fields = {
        'created': 'data_sozdaniya',
        'accepted': 'accept_time',
        'confirmed': 'last_confirmed_at',
        'status': 'status_sort',
    }
    if sort_by not in allowed_sort_fields:
        return directions.order_by(default_order, '-pk')

    if sort_dir not in ('asc', 'desc'):
        sort_dir = 'desc'

    if sort_by == 'status':
        directions = directions.annotate(
            status_sort=Case(
                When(cancel=True, then=Value(4)),
                When(total_confirmed=True, then=Value(3)),
                When(accept_who_doctor__isnull=False, total_confirmed=False, then=Value(2)),
                When(is_cito=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )

    prefix = '' if sort_dir == 'asc' else '-'
    field = allowed_sort_fields[sort_by]
    return directions.order_by(f'{prefix}{field}', '-pk')


def _get_visible_hospitals():
    return Hospitals.objects.filter(hide=False).order_by('short_title', 'title')


def _get_diagnostic_doctors_options(hospital_id=-1):
    if hospital_id and hospital_id != -1:
        hospital = _get_visible_hospitals().filter(pk=hospital_id).first()
    else:
        hospital = Hospitals.get_default_hospital()

    doctors = [{'id': -1, 'label': 'Все'}]
    if not hospital:
        return doctors

    diagnostic_doctors = (
        DoctorProfile.objects.filter(
            hospital=hospital,
            dismissed=False,
            user__groups__name='Врач-диагностики',
        )
        .distinct()
        .order_by('fio')
    )
    doctors.extend({'id': doctor.pk, 'label': doctor.get_fio()} for doctor in diagnostic_doctors)
    return doctors


def _get_all_list_filter_options(hospital_id=-1):
    hospitals = [
        {'id': -1, 'label': 'Все'},
        *[{'id': hospital.pk, 'label': hospital.short_title or hospital.title} for hospital in _get_visible_hospitals()],
    ]

    return {
        'hospitals': hospitals,
        'doctors': _get_diagnostic_doctors_options(hospital_id),
    }


@login_required
@group_required('Журнал заявок')
def get_requests_all_list(request):
    request_data = json.loads(request.body)
    date_type = request_data.get('dateType', 'created')
    date_from = request_data.get('dateFrom')
    date_to = request_data.get('dateTo')
    hospital_id = request_data.get('hospitalId', -1)
    doctor_id = request_data.get('doctorId', -1)
    statuses = request_data.get('statuses') or []
    sort_by = request_data.get('sortBy', '')
    sort_dir = request_data.get('sortDir', 'desc')
    offset = request_data.get('offset', 0)
    try:
        limit = int(request_data.get('limit', ALL_LIST_PAGE_SIZE))
    except (TypeError, ValueError):
        limit = ALL_LIST_PAGE_SIZE
    if limit not in ALLOWED_ALL_LIST_PAGE_SIZES:
        limit = ALL_LIST_PAGE_SIZE

    date_type_fields = {
        'created': 'data_sozdaniya__date',
        'accepted': 'accept_time__date',
        'confirmed': 'last_confirmed_at__date',
    }
    date_type_orders = {
        'created': '-data_sozdaniya',
        'accepted': '-accept_time',
        'confirmed': '-last_confirmed_at',
    }
    if date_type not in date_type_fields:
        date_type = 'created'

    search_date_from, search_date_to, date_error = _parse_date_range(date_from, date_to)
    if date_error:
        return JsonResponse({'rows': [], 'total': 0, 'error': date_error})

    if not search_date_from or not search_date_to:
        return JsonResponse({'rows': [], 'total': 0, 'error': 'Укажите период дат'})

    date_field = date_type_fields[date_type]
    date_filter = {
        f'{date_field}__gte': search_date_from,
        f'{date_field}__lte': search_date_to,
    }

    directions = (
        Napravleniya.objects.filter(
            is_request=True,
            **date_filter,
        )
        .filter(
            Q(hospital__isnull=True) | Q(hospital__hide=False),
        )
        .select_related(
            'client__individual',
            'doc',
            'hospital',
            'accept_who_doctor',
        )
        .prefetch_related(
            'issledovaniya_set__research',
            'issledovaniya_set__doc_confirmation',
        )
    )

    directions = _apply_status_filter(directions, statuses)

    if hospital_id and hospital_id != -1:
        if not _get_visible_hospitals().filter(pk=hospital_id).exists():
            return JsonResponse({'rows': [], 'total': 0, 'error': 'Больница недоступна'})
        directions = directions.filter(hospital_id=hospital_id)

    directions = _apply_doctor_filter(directions, doctor_id, statuses)
    directions = _apply_sort(directions, sort_by, sort_dir, default_order=date_type_orders[date_type])
    total = directions.count()
    directions_list = list(directions[offset : offset + limit])

    rows = [direction_to_all_list_row(direction) for direction in directions_list]
    filter_options = _get_all_list_filter_options(hospital_id)

    return JsonResponse(
        {
            'rows': rows,
            'total': total,
            'maxPeriodDays': get_requests_journal_max_period_days(),
            **filter_options,
        }
    )


@login_required
@group_required("Заполнение заявок", "Врач-диагностики")
def get_requests_by_status(request):
    request_data = json.loads(request.body)
    date_from = request_data.get("dateFrom")
    date_to = request_data.get("dateTo")
    is_done = request_data.get("isDone", False)
    hospital_id = request_data.get("hospitalId", -1)

    try:
        allowed_hospital_ids = check_hospital_access(request.user.doctorprofile, hospital_id)
    except ValueError as e:
        return JsonResponse({"rows": [], "error": str(e)})

    date_filter = {}
    if date_from and date_to:
        try:
            search_date_from = datetime.strptime(date_from, '%d.%m.%Y').date()
            search_date_to = datetime.strptime(date_to, '%d.%m.%Y').date()
            if search_date_from > search_date_to:
                search_date_from, search_date_to = search_date_to, search_date_from
            if (search_date_to - search_date_from).days > 40:
                return JsonResponse({"rows": [], "error": "Период не может превышать 40 дней"})
            if SettingManager.get('show_directions_with_link_image', default='true', default_type='b'):
                date_filter = {
                    'equipment_receive__isnull': False,
                    'equipment_receive__time_save_link__date__gte': search_date_from,
                    'equipment_receive__time_save_link__date__lte': search_date_to,
                }
            else:
                date_filter = {
                    'data_sozdaniya__date__gte': search_date_from,
                    'data_sozdaniya__date__lte': search_date_to,
                }
        except ValueError:
            pass
    elif request_data.get("date"):
        search_date = '-'.join(request_data.get("date").split(".")[::-1])
        if SettingManager.get('show_directions_with_link_image', default='true', default_type='b'):
            date_filter = {
                'equipment_receive__isnull': False,
                'equipment_receive__time_save_link__date': search_date,
            }
        else:
            date_filter = {'data_sozdaniya__date': search_date}

    directions = Napravleniya.objects.filter(is_request=True, **date_filter).select_related("client__individual", "doc", "accept_who_doctor").prefetch_related("issledovaniya_set__research")

    if allowed_hospital_ids:
        directions = directions.filter(hospital_id__in=allowed_hospital_ids)

    if is_done:
        directions = directions.filter(issledovaniya__doc_confirmation=request.user.doctorprofile, total_confirmed=True).order_by("-issledovaniya__time_confirmation").distinct()
    else:
        directions = (
            directions.filter(
                total_confirmed=False,
            )
            .filter(
                Q(accept_who_doctor__isnull=True) | Q(accept_who_doctor=request.user.doctorprofile),
            )
            .order_by("-last_confirmed_at")
            .distinct()
        )
    directions = directions.filter(cancel=False)

    directions_list = list(directions)

    rows = []
    for direction in directions_list:
        rows.append(direction_to_request(direction, request.user.doctorprofile))
    filter_department = list(set([i.get("podrzdeleniye", "-") for i in rows]))

    if not is_done:
        rows.sort(key=lambda x: (not x["cito"], -int(x["datetime"].replace(":", ""))))
    return JsonResponse({"rows": rows, "filterDepartment": filter_department})


@login_required
@group_required("Заполнение заявок", "Врач-диагностики")
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
@group_required("Заполнение заявок", "Врач-диагностики")
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
@group_required("Заполнение заявок", "Врач-диагностики")
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
@group_required("Заполнение заявок", "Врач-диагностики")
def get_permissions_doctor(request):
    access_hospital = PermissionHospitalProtocolDoctorProfile.get_access_hospital_by_doctor(request.user.doctorprofile)
    return JsonResponse({"hospitals": access_hospital})

from django.db import transaction

from directions.models import Napravleniya
from hospitals.models import Hospitals
from integration_framework.views import limit_str
from slog.models import Log


def _get_permission_hospitals(request):
    if not hasattr(request.user, 'hospitals'):
        return None, {'ok': False, 'message': 'Некорректный auth токен'}
    return list(request.user.hospitals.all()), None


def _get_hospital_by_oid(oid, permission_hospitals):
    if not oid:
        return None
    hospital = Hospitals.objects.filter(oid=oid).first()
    if not hospital:
        return None
    if permission_hospitals and hospital not in permission_hospitals:
        return None
    return hospital


def _find_request_direction(body, permission_hospitals):
    direction_num = body.get('directionNum')
    internal_id = body.get('internalId')
    hospital = _get_hospital_by_oid(body.get('oid'), permission_hospitals)

    directions_qs = Napravleniya.objects.filter(is_request=True)
    if hospital:
        directions_qs = directions_qs.filter(hospital=hospital)
    elif permission_hospitals:
        directions_qs = directions_qs.filter(hospital__in=permission_hospitals)

    direction = None
    if direction_num:
        direction = directions_qs.filter(pk=int(direction_num)).first()
        if direction and internal_id and str(direction.id_in_hospital or '') != str(internal_id):
            direction_by_pair = directions_qs.filter(pk=int(direction_num), id_in_hospital=limit_str(str(internal_id), 15)).first()
            if direction_by_pair:
                direction = direction_by_pair
    elif internal_id:
        direction = directions_qs.filter(id_in_hospital=limit_str(str(internal_id), 15)).first()

    return direction, hospital


def _resolve_external_direction_number(body, direction):
    external_num = body.get('externalDirectionNum') or body.get('externalInternalId')
    if external_num:
        return limit_str(str(external_num), 15)

    internal_id = body.get('internalId')
    if internal_id and str(internal_id) not in {str(direction.pk), str(direction.id_in_hospital or '')}:
        return limit_str(str(internal_id), 15)

    directions = body.get('directions') or []
    for direction_id in directions:
        direction_id = str(direction_id)
        if direction_id not in {str(direction.pk), str(direction.id_in_hospital or '')}:
            return limit_str(direction_id, 15)
    return None


def process_dcm_order_create_status(request, body):
    permission_hospitals, error = _get_permission_hospitals(request)
    if error:
        return error

    direction, hospital = _find_request_direction(body, permission_hospitals)
    if not direction:
        return {'ok': False, 'message': 'Заявка не найдена'}

    if not body.get('ok', True):
        return {
            'ok': False,
            'message': body.get('message') or 'Ошибка создания заявки во внешней системе',
            'directionNum': direction.pk,
        }

    update_fields = []
    external_num = _resolve_external_direction_number(body, direction)
    if external_num:
        direction.id_in_hospital = external_num
        update_fields.append('id_in_hospital')

    if body.get('status') == 'created' or body.get('ok', True):
        direction.received_by_rmq = True
        update_fields.append('received_by_rmq')

    if update_fields:
        direction.save(update_fields=update_fields)

    Log.log(
        str(direction.pk),
        60029,
        None,
        {
            'type': 'dcm_order_create_status',
            'body': body,
            'directionNum': direction.pk,
            'id_in_hospital': direction.id_in_hospital,
            'hospital': hospital.safe_short_title if hospital else direction.hospital.safe_short_title if direction.hospital else None,
        },
    )

    return {
        'ok': True,
        'directionNum': direction.pk,
        'id_in_hospital': direction.id_in_hospital,
        'status': body.get('status') or 'created',
    }


def process_dcm_study_link_status(request, body):
    permission_hospitals, error = _get_permission_hospitals(request)
    if error:
        return error

    direction, hospital = _find_request_direction(body, permission_hospitals)
    if not direction:
        return {'ok': False, 'message': 'Заявка не найдена'}

    status = body.get('status') or ('linked' if body.get('ok', True) else 'error')
    message = body.get('message') or ''

    with transaction.atomic():
        direction.dcm_study_link_status = limit_str(status, 32)
        direction.dcm_study_link_message = message
        update_fields = ['dcm_study_link_status', 'dcm_study_link_message']
        if body.get('ok', True) and status == 'linked':
            direction.received_by_rmq = True
            update_fields.append('received_by_rmq')
        direction.save(update_fields=update_fields)

    Log.log(
        str(direction.pk),
        60029,
        None,
        {
            'type': 'dcm_study_link_status',
            'body': body,
            'directionNum': direction.pk,
            'status': direction.dcm_study_link_status,
            'hospital': hospital.safe_short_title if hospital else direction.hospital.safe_short_title if direction.hospital else None,
        },
    )

    return {
        'ok': True,
        'directionNum': direction.pk,
        'status': direction.dcm_study_link_status,
        'message': direction.dcm_study_link_message,
    }

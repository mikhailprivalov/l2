import logging

import pika
import simplejson as json

import slog.models as slog
from clients.models import Document
from laboratory.settings import RMQ_AUTH_PARAM_RENTGEN
from laboratory.utils import current_time

logger = logging.getLogger(__name__)


def build_dcm_order_create_payload(direction, doc_profile, research):
    hospital = direction.hospital or doc_profile.hospital
    card = direction.client
    individual = card.individual

    snils_doc = Document.objects.filter(individual=individual, document_type__title__startswith='СНИЛС').first()
    snils = snils_doc.number if snils_doc else ''
    enp = (individual.tfoms_enp or '').replace(' ', '')

    date_study = ''
    if direction.fact_research_date:
        if hasattr(direction.fact_research_date, 'strftime'):
            date_str = direction.fact_research_date.strftime('%Y-%m-%d')
        else:
            date_str = str(direction.fact_research_date)
        if direction.fact_research_time:
            time_str = direction.fact_research_time.strftime('%H:%M') if hasattr(direction.fact_research_time, 'strftime') else str(direction.fact_research_time)
        else:
            time_str = '00:00'
        date_study = f'{date_str} {time_str}'

    nmu_code = ''
    if research and research.code:
        nmu_code = research.code.split(';')[0].strip()

    contrast_type_id = direction.type_contrast_id if direction.type_contrast_id else -1

    return {
        'oid': hospital.oid if hospital else '',
        'patient': {
            'internalId': individual.owner_patient_id or str(card.pk),
            'enp': enp,
            'snils': snils,
            'lastname': individual.family or '',
            'firstname': individual.name or '',
            'patronymic': individual.patronymic or '',
            'birthdate': individual.birthday.strftime('%Y-%m-%d') if individual.birthday else '',
            'sex': individual.sex or 'м',
            'email': card.email or '',
            'phone': card.phone or '',
            'mainAddress': card.main_address or '',
            'factAddress': card.fact_address or '',
        },
        'orderData': {
            'internalId': str(direction.id_in_hospital or direction.pk),
            'fsidiCode': (research.nsi_id or '') if research else '',
            'nmuCode': nmu_code,
            'codePrice': (research.internal_code or '') if research else '',
            'operatorCreatedId': doc_profile.get_operator_created_id_for_external(),
            'dateStudy': date_study,
            'cito': direction.is_cito,
            'contrastAmount': direction.contrast_amount or '',
            'dose': direction.dose or '',
            'anamnesis': direction.anamnesis or '',
            'comment': direction.direction_comment or '',
            'isDynamic': direction.is_dynamic,
            'contrastTypeId': contrast_type_id,
        },
    }


def build_dcm_study_link_payload(direction, equipment_receive, doc_profile):
    return {
        'internalId': str(direction.id_in_hospital or direction.pk),
        'directionNum': direction.pk,
        'studyInstanceUID': equipment_receive.study_instance_uid_tag or '',
        'deviceId': equipment_receive.equipment_model_id,
        'operatorCreatedId': doc_profile.get_operator_created_id_for_external(),
    }


def _broker_publish_rentgen_message(message, exchange_name, routing_key, message_type, log_key):
    if not RMQ_AUTH_PARAM_RENTGEN.get('address'):
        return False

    credentials = pika.PlainCredentials(RMQ_AUTH_PARAM_RENTGEN.get('login'), RMQ_AUTH_PARAM_RENTGEN.get('password'))
    parameters = pika.ConnectionParameters(
        host=RMQ_AUTH_PARAM_RENTGEN.get('address'),
        port=RMQ_AUTH_PARAM_RENTGEN.get('port'),
        credentials=credentials,
        virtual_host=RMQ_AUTH_PARAM_RENTGEN.get('virtual_host', '/'),
    )

    cur_time = current_time().strftime('%Y%m%d%H:%M:%S')
    message_data = {'timestamp': cur_time, 'data': message, 'type': message_type, 'exchange': exchange_name, 'routing_key': routing_key}

    with pika.BlockingConnection(parameters) as conn:
        with conn.channel() as ch:
            ch.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                ),
                mandatory=True,
            )
            slog.Log(key=str(log_key), type=60028, body=f'Отправлено в RMQ rentgen {message_data}').save()
    return True


def broker_publish_rentgen_order(message):
    exchange_name = RMQ_AUTH_PARAM_RENTGEN.get('exchange_name', 'l2.dicom.orders')
    routing_key = RMQ_AUTH_PARAM_RENTGEN.get('routing_key', 'order.create')
    log_key = message.get('orderData', {}).get('internalId', '')
    return _broker_publish_rentgen_message(message, exchange_name, routing_key, 'dcm_order_create', log_key)


def broker_publish_rentgen_study_link(message):
    exchange_name = RMQ_AUTH_PARAM_RENTGEN.get('study_link_exchange_name', 'l2.dicom.study')
    routing_key = RMQ_AUTH_PARAM_RENTGEN.get('study_link_routing_key', 'study.link')
    log_key = message.get('internalId', '')
    return _broker_publish_rentgen_message(message, exchange_name, routing_key, 'dcm_study_link', log_key)


def send_request_to_rentgen_rmq(direction, doc_profile, research):
    try:
        payload = build_dcm_order_create_payload(direction, doc_profile, research)
        return broker_publish_rentgen_order(payload)
    except Exception:
        logger.exception('Failed to send request %s to rentgen RMQ', direction.pk)
        return False


def send_study_link_to_rentgen_rmq(direction, equipment_receive, doc_profile):
    try:
        payload = build_dcm_study_link_payload(direction, equipment_receive, doc_profile)
        return broker_publish_rentgen_study_link(payload)
    except Exception:
        logger.exception('Failed to send study link for request %s to rentgen RMQ', direction.pk)
        return False

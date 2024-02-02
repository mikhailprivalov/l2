import logging
import traceback
from datetime import timedelta

import firebase_admin
from django.utils import timezone
from firebase_admin import messaging
from firebase_admin import credentials

from clients.models import Phones
from integration_framework.idgtl import IDGTLApi
from integration_framework.models import IndividualAuth
from laboratory.celery import app
from laboratory.settings import FCM_CERT_PATH

logger = logging.getLogger(__name__)


@app.task(bind=True)
def send_has_result(self, feed_unique_id: str):
    from results_feed.models import ResultFeed

    cred = credentials.Certificate(FCM_CERT_PATH)
    if firebase_admin._DEFAULT_APP_NAME not in firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    logger.info(f"send_has_result {feed_unique_id}")
    feed = ResultFeed.objects.get(unique_id=feed_unique_id)

    phones = [Phones.format_as_plus_7(phone) for phone in [x.normalize_number() for x in Phones.objects.filter(card__individual=feed.individual, card__is_archive=False)]]

    individual_auth = IndividualAuth.objects.filter(used_phone__in=phones, is_confirmed=True, last_activity__gte=timezone.now() - timedelta(days=100))

    fcm_tokens = [auth.fcm_token for auth in individual_auth]

    logger.info(f"FCM tokens: {fcm_tokens}")

    if len(fcm_tokens) == 0:
        return

    message_title = "Результаты готовы"
    message_body = f"Результаты по направлению №{feed.direction.pk} от {feed.direction.data_sozdaniya.strftime('%d.%m.%Y %H:%M')} готовы"

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=message_title,
            body=message_body,
        ),
        tokens=fcm_tokens,
    )

    result = messaging.send_each_for_multicast(message)

    resp: messaging.SendResponse
    for resp in result.responses:
        if resp.exception:
            logger.error(f"FCM error: {resp.exception}")
        else:
            logger.info(f"FCM success: {resp.message_id}")


@app.task(bind=True)
def send_code_cascade(self, phone: str, auth_id: int):
    individual_auth = IndividualAuth.objects.get(pk=auth_id)

    if individual_auth.is_confirmed:
        logger.error(f"Individual already confirmed: {phone}")
        return

    if not individual_auth.individuals.exists():
        logger.error(f"Individual not found: {phone}")
        return

    api = IDGTLApi()

    if individual_auth.confirmation_message_id:
        try:
            api.stop([individual_auth.confirmation_message_id])
        except Exception as e:
            logger.error(f"IDGTL error: {e}")
            logger.error(traceback.format_exc())
    try:
        resp = api.send_code_cascade(phone, individual_auth.confirmation_code)
        logger.info(f"IDGTL response: {resp.json()}")
        message_id = resp.json()['items'][0]['messageUuid']
        individual_auth.confirmation_message_id = message_id
        individual_auth.save(update_fields=['confirmation_message_id'])
    except Exception as e:
        logger.error(f"IDGTL error: {e}")
        logger.error(traceback.format_exc())


@app.task(bind=True)
def stop_code_cascade(self, auth_id: int):
    individual_auth = IndividualAuth.objects.get(pk=auth_id)

    if not individual_auth.confirmation_message_id:
        return

    api = IDGTLApi()

    try:
        resp = api.stop([individual_auth.confirmation_message_id])
        logger.info(f"IDGTL response: {resp.json()}")
    except Exception as e:
        logger.error(f"IDGTL error: {e}")
        logger.error(traceback.format_exc())

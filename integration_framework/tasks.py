import logging
from datetime import timedelta

import firebase_admin
from django.utils import timezone
from firebase_admin import messaging
from firebase_admin import credentials

from clients.models import Phones
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

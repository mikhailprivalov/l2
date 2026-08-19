import logging
import traceback

from integration_framework.idgtl import IDGTLApi
from integration_framework.models import IndividualAuth
from laboratory.celery import app

logger = logging.getLogger(__name__)


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

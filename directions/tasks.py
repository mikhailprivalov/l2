import base64
import logging

from django.core.files.base import ContentFile

from integration_framework.common_func import directions_pdf_result
from laboratory.celery import app

from laboratory.utils import strdatetime
from slog.models import Log


logger = logging.getLogger(__name__)


@app.task(bind=True)
def send_result(self, direction_pk):
    from directions.models import Napravleniya, Issledovaniya

    direction = Napravleniya.objects.get(pk=direction_pk)
    task_id = self.request.id
    direction.celery_send_task_ids = [x for x in direction.celery_send_task_ids if x != task_id]
    direction.save(update_fields=['celery_send_task_ids'])

    if not direction.is_all_confirm() or not direction.client:
        Log.log(key=direction_pk, type=180003, body={"task_id": task_id, "reason": "Нет подтверждения" if direction.client else "Некорректная карта"})
        return

    send_to_email = direction.client.send_to_email
    email = direction.client.email

    if not send_to_email or not email:
        Log.log(key=direction_pk, type=180003, body={"task_id": task_id, "reason": "Нет email" if send_to_email else "Отправка пациенту запрещена"})
        return
    try:
        hospital = direction.get_hospital()

        pdf = directions_pdf_result([direction_pk])

        filename = f"results_{direction_pk}.pdf"
        file = ContentFile(base64.b64decode(pdf), name=filename)

        body_lines = [
            f"Результаты №{direction_pk} от {strdatetime(direction.data_sozdaniya)}",
            "",
        ]

        for iss in Issledovaniya.objects.filter(napravleniye=direction):
            body_lines.append(f" - {iss.research.title}")
        body_lines.append("")

        body = "\n".join(body_lines)
        hospital.send_email_with_pdf_file(f"Результаты №{direction_pk} от {strdatetime(direction.data_sozdaniya)}", body, file, to=email)
        Log.log(key=direction_pk, type=180001, body={"task_id": task_id})
    except Exception as e:
        logger.exception(e)
        Log.log(key=direction_pk, type=180002, body={"task_id": task_id, "reason": "Ошибка", "error": str(e)})

from django.db import models
from clients.models import Card
from directory.models import Researches
from users.models import DoctorProfile
import datetime
from laboratory.utils import current_time
import slog.models as slog
import simplejson as json


class ListWait(models.Model):
    STATUS = (
        (0, "Ожидает"),
        (1, "Выполнено"),
        (2, "Отменено"),
    )
    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, db_index=True, help_text='Вид исследования из справочника', on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    exec_at = models.DateTimeField(help_text='Дата для записи', db_index=True)
    comment = models.TextField()
    work_status = models.PositiveSmallIntegerField(choices=STATUS, db_index=True, default=0, blank=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель листа ожидания', on_delete=models.SET_NULL)
    phone = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        verbose_name = 'Лист ожидания'
        verbose_name_plural = 'Лист ожидания'

    @staticmethod
    def list_wait_save(data, doc_who_create):
        patient_card = Card.objects.get(pk=data['card_pk']) if 'card' not in data else data['card']
        research_obj = Researches.objects.get(pk=data['research'])
        list_wait = ListWait(
            client=patient_card,
            research=research_obj,
            exec_at=datetime.datetime.strptime(data['date'], '%Y-%m-%d'),
            comment=data['comment'],
            phone=data['phone'],
            doc_who_create=doc_who_create,
            work_status=0,
        )
        list_wait.save()

        slog.Log(
            key=list_wait.pk,
            type=80005,
            body=json.dumps(
                {
                    "card_pk": patient_card.pk,
                    "research": research_obj.title,
                    "date": data['date'],
                    "comment": data['comment'],
                }
            ),
            user=doc_who_create,
        ).save()
        return list_wait.pk

    @staticmethod
    def list_wait_change_status(data, doc_who_create):
        list_wait = ListWait.objects.filter(pk=data['pk_list_wait'])[0]
        list_wait.doc_who_create = doc_who_create
        list_wait.work_status = data['status']
        list_wait.save()

        slog.Log(
            key=list_wait.pk,
            type=80006,
            body=json.dumps({"card_pk": list_wait.client.pk, "status": list_wait.work_status}),
            user=doc_who_create,
        ).save()
        return list_wait.pk

    @staticmethod
    def list_wait_get(data):
        if data.get('d1', None):
            d1 = datetime.datetime.strptime(data.get('d1'), '%d.%m.%Y')
        else:
            d1 = current_time()
        if data.get('d2', None):
            d2 = datetime.datetime.strptime(data.get('d2'), '%d.%m.%Y')
        else:
            d2 = current_time()

        start_date = datetime.datetime.combine(d1, datetime.time.min)
        end_date = datetime.datetime.combine(d2, datetime.time.max)
        if data.get('research', None):
            research_obj = Researches.objects.filter(pk=data.get('research'))
            result = ListWait.objects.filter(research=research_obj, exec_at__range=(start_date, end_date)).order_by("exec_at")
        elif data.get('patient_pk', None):
            result = ListWait.objects.filter(client__pk=data.get('patient_pk')).order_by("exec_at")
        else:
            result = ListWait.objects.filter(exec_at__range=(start_date, end_date)).order_by("pk", "exec_at", "research")

        return result

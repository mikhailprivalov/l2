from django.db import models
from clients.models import Card, District
from directory.models import Researches
from users.models import DoctorProfile
import datetime
from laboratory.utils import current_time
import slog.models as slog
import simplejson as json


class DoctorCall(models.Model):
    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, help_text='Вид исследования из справочника', on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    exec_at = models.DateTimeField(auto_now_add=True, help_text='Дата вызова на дом', db_index=True)
    comment = models.TextField()
    cancel = models.BooleanField(default=False, blank=True, help_text='Отмена вызова')
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель вызова на дом', on_delete=models.SET_NULL)
    district = models.ForeignKey(District, default=None, null=True, blank=True, db_index=True, help_text="Участок", on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Вызов'
        verbose_name_plural = 'Вызова на дом'

    @staticmethod
    def doctor_call_save(data, doc_who_create):
        patient_card = Card.objects.filter(pk=data['card_pk'])[0]
        research_obj = Researches.objects.get(pk=data['research'])
        district_obj = District.objects.get(pk=data.get('district'))
        doc_call = DoctorCall(client=patient_card, research=research_obj, exec_at=datetime.datetime.strptime(data['date'], '%Y-%m-%d'), comment=data['comment'],
                              doc_who_create=doc_who_create, cancel=False, district=district_obj)
        doc_call.save()

        slog.Log(
            key=doc_call.pk,
            type=80003,
            body=json.dumps(
                {
                    "card_pk": data['card_pk'],
                    "research": research_obj.title,
                    "distric": district_obj.title,
                    "date": datetime.datetime.strptime(data['date']),
                    "comment": data['comment'],
                }
            ),
            user=doc_who_create,
        ).save()
        return doc_call.pk

    @staticmethod
    def doctor_call_cancel(data, doc_who_create):
        doc_call = DoctorCall.objects.filter(pk=data['pk_doc_call'])[0]
        doc_call.doc_who_create = doc_who_create
        doc_call.cancel = not doc_call.canceled
        doc_call.save()

        slog.Log(
            key=doc_call.pk,
            type=80004,
            body=json.dumps(
                {
                    "card_pk": doc_call.client.pk,
                    "status": doc_call.cancel
                }
            ),
            user=doc_who_create,
        ).save()
        return doc_call.pk


    @staticmethod
    def doctor_call_get(data):
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
        if data.get('district', None):
            district_obj = District.objects.filter(pk__in=data.get('district'))
            result = DoctorCall.objects.filter(district__in=district_obj, exec_at__range=(start_date, end_date)).order_by("district")
        elif data.get('patient_pk', None):
            result = DoctorCall.objects.filter(client__pk=data.get('patient_pk')).order_by("exec_at")
        else:
            result = DoctorCall.objects.filter(exec_at__range=(start_date, end_date)).order_by("exec_at, district")

        return result

from clients.models import Card
from django.db import models
from users.models import DoctorProfile
from datetime import datetime
from laboratory.utils import current_time, strdatetime
import slog.models as slog
import simplejson as json


class PlanOperations(models.Model):
    patient_card = models.ForeignKey(Card, null=True, help_text='Карта пациента', db_index=True, on_delete=models.SET_NULL)
    direction = models.CharField(max_length=128, default=None, blank=True, null=True, help_text="Номер истории")
    date = models.DateTimeField(null=True, blank=True, help_text='Время на операцию', db_index=True)
    doc_operate = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_operate", help_text='Кто опрерирует', on_delete=models.SET_NULL)
    type_operation = models.TextField(default=None, blank=True, null=True, help_text="Вид операции")
    canceled = models.BooleanField(default=False, help_text='Операция отменена')
    doc_anesthetist = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_anesthetist", help_text='Кто опрерирует', on_delete=models.SET_NULL)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_create_plan", help_text='Создатель планирвоания', on_delete=models.SET_NULL)
    create_at = models.DateTimeField(default=None, null=True, blank=True, help_text='Дата создания', db_index=True)

    @staticmethod
    def save_data(data, doc_who_create):
        patient_card = Card.objects.filter(pk=data['card_pk'])[0]
        direction_obj = data['direction']
        type_operation = data.get('type_operation', '')
        doc_operate_obj = DoctorProfile.objects.filter(pk=data['hirurg'])[0]
        doc_anesthetist = data.get('doc_anesthetist', None)
        doc_anesthetist_obj = None
        if doc_anesthetist:
            doc_anesthetist_obj = DoctorProfile.objects.filter(pk=doc_anesthetist)[0]

        date_now = current_time()
        print(data['date'], type(data['date']))

        if data['pk_plan'] == -1:
            plan_obj = PlanOperations(
                patient_card=patient_card,
                direction=direction_obj,
                date=datetime.strptime(data['date'], '%Y-%m-%d'),
                doc_operate=doc_operate_obj,
                type_operation=type_operation,
                doc_anesthetist=doc_anesthetist_obj,
                doc_who_create=doc_who_create,
                canceled=False,
                create_at=date_now,
            )
            plan_obj.save()
            print(plan_obj.pk)

            slog.Log(
                key=plan_obj.pk,
                type=80001,
                body=json.dumps({"card_pk": data['card_pk'], "direction": direction_obj, "date_operation": data['date'], "create_at": strdatetime(date_now), "doc_operate": data['hirurg'],
                                 "type_operation": type_operation }),
                user=doc_who_create,
            ).save()
        else:
            plan_obj = PlanOperations.objects.filter(pk=data['pk_plan'])[0]
            plan_obj.doc_operate = doc_operate_obj
            plan_obj.type_operation = type_operation
            if 'doc_anesthetist' in data:
                plan_obj.doc_anesthetist = doc_anesthetist_obj
            plan_obj.doc_who_create = doc_who_create
            plan_obj.date = datetime.strptime(data['date'], '%Y-%m-%d') if '-' in data['date'] else datetime.strptime(data['date'], '%d.%m.%Y')
            plan_obj.direction = direction_obj
            plan_obj.patient_card = patient_card
            plan_obj.canceled = False
            plan_obj.save()
            slog.Log(
                key=data['pk_plan'],
                type=80002,
                body=json.dumps({"card_pk": data['card_pk'], "direction": direction_obj,
                                 "date_operation": data['date'], "update_at": strdatetime(date_now),
                                 "doc_operate": data['hirurg'], "type_operation": type_operation,
                                 }),
                user=doc_who_create,
            ).save()

        return plan_obj.pk

    @staticmethod
    def cancel_operation(data, doc_who_create):
        plan_obj = PlanOperations.objects.get(pk=data['pk_plan'])
        plan_obj.doc_who_create = doc_who_create
        plan_obj.canceled = not plan_obj.canceled
        plan_obj.save()
        return plan_obj.canceled

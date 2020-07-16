from clients.models import Card
from django.db import models
from users.models import DoctorProfile
from datetime import datetime


class PlanOperations(models.Model):

    patient_card = models.ForeignKey(Card, null=True, help_text='Карта пациента', db_index=True, on_delete=models.SET_NULL)
    direction = models.CharField(max_length=128, default=None, blank=True, null=True, help_text="Номер истории")
    date = models.DateTimeField(null=True, blank=True, help_text='Время на операцию', db_index=True)
    doc_operate = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_operate", help_text='Кто опрерирует', on_delete=models.SET_NULL)
    type_operation = models.TextField(default=None, blank=True, null=True, help_text="Вид операции")
    doc_anesthetist = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_anesthetist", help_text='Кто опрерирует', on_delete=models.SET_NULL)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_create_plan", help_text='Создатель планирвоания', on_delete=models.SET_NULL)

    @staticmethod
    def save_data(data, doc_who_create):
        patient_card = Card.objects.filter(pk=data['card_pk'])[0]
        direction_obj = data['direction']
        type_examinations = data['type_examination']
        type_operation = data['type_operation']
        doc_operate_obj = DoctorProfile.objects.filter(pk=data['hirurg'])[0]
        doc_anesthetist = data.get('doc_anesthetist', None)
        doc_anesthetist_obj = None
        if doc_anesthetist:
            doc_anesthetist_obj = DoctorProfile.objects.filter(pk=doc_anesthetist)[0]

        if data['pk_plan'] == -1:
            PlanOperations(patient_card=patient_card,
                            direction=direction_obj,
                            date=datetime.strptime(data['date'], '%Y-%m-%d'),
                            doc_operate=doc_operate_obj,
                            type_examinations=type_examinations,
                            type_operation=type_operation,
                            doc_anesthetist=doc_anesthetist_obj,
                            doc_who_create=doc_who_create).save()

        return True

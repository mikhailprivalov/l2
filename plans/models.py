import os
import uuid

from dateutil.relativedelta import relativedelta

from clients.models import Card
from django.db import models

from directory.models import Researches
from doctor_schedule.models import SlotFact
from plans.sql_func import get_messages_by_plan_hospitalization, get_messages_by_card_id
from podrazdeleniya.models import Podrazdeleniya
from users.models import DoctorProfile
from datetime import datetime
import slog.models as slog
import simplejson as json
from laboratory.utils import current_time


class PlanOperations(models.Model):
    patient_card = models.ForeignKey(Card, null=True, help_text='Карта пациента', db_index=True, on_delete=models.SET_NULL)
    direction = models.CharField(max_length=128, default=None, blank=True, null=True, help_text="Номер истории")
    date = models.DateTimeField(null=True, blank=True, help_text='Время на операцию', db_index=True)
    doc_operate = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_operate", help_text='Кто опрерирует', on_delete=models.SET_NULL)
    type_operation = models.TextField(default=None, blank=True, null=True, help_text="Вид операции")
    canceled = models.BooleanField(default=False, help_text='Операция отменена')
    doc_anesthetist = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_anesthetist", help_text='Кто опрерирует', on_delete=models.SET_NULL)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, related_name="doc_create_plan", help_text='Создатель планирования', on_delete=models.SET_NULL)

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
            )
            plan_obj.save()

            slog.Log(
                key=plan_obj.pk,
                type=80001,
                body=json.dumps(
                    {
                        "card_pk": data['card_pk'],
                        "direction": direction_obj,
                        "date_operation": data['date'],
                        "doc_operate": data['hirurg'],
                        "type_operation": type_operation,
                    }
                ),
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
                body=json.dumps(
                    {
                        "card_pk": data['card_pk'],
                        "direction": direction_obj,
                        "date_operation": data['date'],
                        "doc_operate": data['hirurg'],
                        "type_operation": type_operation,
                    }
                ),
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


class PlanHospitalization(models.Model):
    STATUS = (
        (0, "Ожидает"),
        (1, "Выполнено"),
        (2, "Отменено"),
        (3, "Утверждено"),
    )
    ACTION = (
        (0, "Поступление"),
        (1, "Выбытие"),
    )
    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    research = models.ForeignKey(Researches, null=True, blank=True, db_index=True, help_text='Вид исследования из справочника', on_delete=models.CASCADE)
    create_at = models.DateTimeField(auto_now_add=True, help_text='Дата создания')
    exec_at = models.DateTimeField(help_text='Дата для записи', db_index=True)
    comment = models.TextField()
    work_status = models.PositiveSmallIntegerField(choices=STATUS, db_index=True, default=0, blank=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель листа ожидания', on_delete=models.SET_NULL)
    phone = models.CharField(max_length=20, blank=True, default='')
    hospital_department = models.ForeignKey(Podrazdeleniya, blank=True, null=True, default=None, help_text="Отделение стационара", on_delete=models.SET_NULL)
    action = models.PositiveSmallIntegerField(choices=ACTION, db_index=True, default=0, blank=True)
    diagnos = models.CharField(max_length=511, help_text='Диагноз Д-учета', default='', blank=True)
    slot_fact = models.ForeignKey(SlotFact, blank=True, null=True, default=None, help_text="Время фактической госпитализации", on_delete=models.SET_NULL)
    why_cancel = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'План коечного фонда'
        verbose_name_plural = 'План коечного фонда'

    @staticmethod
    def plan_hospitalization_save(data, doc_who_create):
        patient_card = Card.objects.get(pk=data['card_pk']) if 'card' not in data else data['card']
        research_obj = Researches.objects.get(pk=data['research'])
        plan_hospitalization = PlanHospitalization(
            client=patient_card,
            research=research_obj,
            exec_at=datetime.strptime(data['date'], '%Y-%m-%d'),
            comment=data['comment'],
            phone=data['phone'],
            doc_who_create=doc_who_create,
            work_status=0,
            hospital_department_id=data['hospital_department_id'],
            action=data['action'],
            diagnos=data.get('diagnos') or '',
        )
        plan_hospitalization.save()
        slog.Log(
            key=plan_hospitalization.pk,
            type=80007,
            body=json.dumps(
                {
                    "card_pk": patient_card.pk,
                    "research": research_obj.title,
                    "date": data['date'],
                    "comment": data['comment'],
                    "hospital_department_id": data['hospital_department_id'],
                }
            ),
            user=doc_who_create,
        ).save()
        return plan_hospitalization.pk

    @staticmethod
    def plan_hospitalization_change_status(data, doc_who_create):
        plan_hosp = PlanHospitalization.objects.get(pk=data['pk_plan'])
        plan_hosp.doc_who_create = doc_who_create
        if data["status"] == 2:
            plan_hosp.why_cancel = data.get('cancelReason') or ''
            if plan_hosp.work_status == 2:
                plan_hosp.work_status = 0
            else:
                plan_hosp.work_status = 2
        plan_hosp.save()

        slog.Log(
            key=plan_hosp.pk,
            type=80008,
            body=json.dumps({"card_pk": plan_hosp.client.pk, "status": plan_hosp.work_status, "action": data["action"]}),
            user=doc_who_create,
        ).save()
        return plan_hosp.pk

    @staticmethod
    def plan_hosp_get(data):
        if data.get('d1', None):
            d1 = datetime.strptime(data.get('d1'), '%d.%m.%Y')
        else:
            d1 = current_time()
        if data.get('d2', None):
            d2 = datetime.strptime(data.get('d2'), '%d.%m.%Y')
        else:
            d2 = current_time()

        start_date = datetime.combine(d1, datetime.time.min)
        end_date = datetime.combine(d2, datetime.time.max)
        if data.get('research', None):
            result = PlanHospitalization.objects.filter(research_id=data.get('research'), exec_at__range=(start_date, end_date)).order_by("exec_at")
        elif data.get('patient_pk', None):
            result = PlanHospitalization.objects.filter(client__pk=data.get('patient_pk')).order_by("exec_at")
        else:
            result = PlanHospitalization.objects.filter(exec_at__range=(start_date, end_date)).order_by("pk", "exec_at", "research")

        return result


def get_file_path(instance: 'PlanHospitalizationFiles', filename):
    return os.path.join('plan_hospitalization_uploads', str(instance.plan.pk), str(uuid.uuid4()), filename)


class PlanHospitalizationFiles(models.Model):
    plan = models.ForeignKey(PlanHospitalization, db_index=True, on_delete=models.CASCADE)
    uploaded_file = models.FileField(upload_to=get_file_path, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_count_files_by_plan(plan):
        return PlanHospitalizationFiles.objects.filter(plan=plan, uploaded_file__isnull=False).count()


class LimitDatePlanHospitalization(models.Model):
    research = models.ForeignKey(Researches, null=True, blank=True, db_index=True, help_text='Вид исследования из справочника', on_delete=models.CASCADE)
    date = models.DateTimeField(help_text='Планируемая дата госпитализации')
    hospital_department = models.ForeignKey(Podrazdeleniya, blank=True, null=True, default=None, help_text="Отделение стационара", on_delete=models.SET_NULL)
    max_count = models.SmallIntegerField(default=0, help_text='Квота для планирования', blank=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель плана', on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'Лимит на дату плана госпитализации'
        verbose_name_plural = 'Лимиты плана госпитализация'

    @staticmethod
    def limit_date_hospitalization_save(data, doc_who_create):
        research_obj = Researches.objects.get(pk=data['research'])
        limit_plan_hospitalization = LimitDatePlanHospitalization(
            research=research_obj,
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            doc_who_create=doc_who_create,
            hospital_department_id=data['hospital_department_id'],
            count=data['count'],
        )
        limit_plan_hospitalization.save()
        slog.Log(
            key=limit_plan_hospitalization.pk,
            type=80009,
            body=json.dumps(
                {
                    "research": research_obj.title,
                    "date": data['date'],
                    "hospital_department_id": data['hospital_department_id'],
                }
            ),
            user=doc_who_create,
        ).save()
        return limit_plan_hospitalization.pk

    @staticmethod
    def limit_plan_hosp_get(research_pk):
        start_date = current_time()
        end_date = start_date + relativedelta(days=30)
        result = LimitDatePlanHospitalization.objects.filter(exec_at__range=(start_date, end_date), research_pk=research_pk).order_by("date")

        return result


class Messages(models.Model):
    message = models.TextField(default=None, blank=True, null=True, help_text="Вид операции")
    client = models.ForeignKey(Card, db_index=True, help_text='Пациент', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    doc_who_create = models.ForeignKey(DoctorProfile, default=None, blank=True, null=True, help_text='Создатель сообщения', on_delete=models.SET_NULL)
    plan = models.ForeignKey(PlanHospitalization, db_index=True, default=None, blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Сообщения'
        verbose_name_plural = 'Сообщения'

    @staticmethod
    def message_save(data, doc_who_create):
        patient_card = Card.objects.get(pk=data['card_pk'])
        pk_plan = data.get("plan_pk", None)
        plan = PlanHospitalization.objects.get(pk=pk_plan) if pk_plan else None
        message = Messages(client=patient_card, message=data['message'], doc_who_create=doc_who_create, plan=plan)
        message.save()
        return message.pk

    @staticmethod
    def get_messages_by_plan_hosp(pk_plan, last=True):
        messages_obj = get_messages_by_plan_hospitalization(pk_plan)
        result = [{"message": i.message, "createdAt": f"{i.date_create}:{i.time_create}", "who_create": i.fio_create} for i in messages_obj]
        if last and len(result) > 0:
            return {"count": len(result), "last": result[-1]['message']}
        if last and len(result) == 0:
            return {"count": 0, "last": None}
        return result

    @staticmethod
    def get_message_by_card(card_id):
        messages_obj = get_messages_by_card_id(card_id)
        result = [{"message": i.message, "date": i.date_create, "time": i.time_create} for i in messages_obj]
        return result

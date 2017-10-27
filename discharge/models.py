from django.db import models
import podrazdeleniya.models as pod
import users.models as users


class Discharge(models.Model):
    client_surname = models.CharField(max_length=60, help_text="Фамилия", db_index=True)
    client_name = models.CharField(max_length=60, help_text="Имя", db_index=True)
    client_patronymic = models.CharField(max_length=60, help_text="Отчество", db_index=True)
    client_birthday = models.CharField(max_length=11, help_text="Дата рождения", blank=True, null=True)
    client_sex = models.CharField(max_length=1, help_text="Пол", blank=True, null=True)
    client_cardnum = models.CharField(max_length=20, help_text="Номер карты", blank=True, null=True, db_index=True)
    client_historynum = models.CharField(max_length=20, help_text="Номер истории", blank=True, null=True)

    otd = models.ForeignKey(pod.Podrazdeleniya, help_text="Отделение", db_index=True)
    doc_fio = models.CharField(max_length=255, help_text="Врач", db_index=True)
    creator = models.ForeignKey(users.DoctorProfile)

    file = models.FileField(upload_to='discharges/%Y/%m/%d/')

    created_at = models.DateTimeField(auto_now_add=True)

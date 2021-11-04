from django.core.management.base import BaseCommand

from users.models import DoctorProfile


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        doctors_users = DoctorProfile.objects.all()
        for doctor in doctors_users:
            fio = f"{doctor.family} {doctor.name} {doctor.patronymic}"
            podr = doctor.podrazdeleniye.title if doctor.podrazdeleniye else "Подразделение не заполнено"
            snils = doctor.snils if doctor.snils else "СНИЛС не заполнен"
            spec = doctor.specialities if doctor.specialities else "Специальность не заполнена"
            position = doctor.position.title if doctor.position else "Должность не заполнена"
            print(f"{fio}@{podr}@{snils}@{spec}@{position}")

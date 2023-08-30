from clients.models import Individual
from education.models import ApplicationEducation, EducationSpeciality, EntranceExam, Subjects, ExamType


def update_education_individual(person_data, user_hospital_obj, person_applications, person_grade, person_achievements):
    try:
        card = Individual.import_from_simple_data(
            {
                "family": person_data.Фамилия,
                "name": person_data.Имя,
                "patronymic": person_data.Отчество,
                "sex": "м" if "м" in person_data.Пол.lower() else "ж",
                "birthday": person_data.Дата_Рождения.strftime("%d.%m.%Y"),
                "snils": person_data.СНИЛС if person_data.СНИЛС else "",
            },
            user_hospital_obj,
            person_data.ID,
            "",
            "",
            filter_mmis_id=True
        )
        card.phone = person_data.Мобильный if person_data.Мобильный else ""
        card.save()

        for pa in person_applications:
            pa_mmis_id_application = pa.get("Код_Заявления")
            application = ApplicationEducation.objects.filter(mmis_id=pa_mmis_id_application).first()
            education_speciality = EducationSpeciality.objects.filter(mmis_id=pa.get("Код_Специальности")).first()
            personal_number = pa.get("НомерЛД")
            is_enrolled = pa.get("Зачислен")
            is_expelled = pa.get("ОтказалсяОтЗачисления")
            date = pa.get("Дата_Подачи")
            is_checked = pa.get("Проверено")
            if application.exist():
                application.speciality = education_speciality
                application.personal_number = personal_number
                application.is_enrolled = is_enrolled
                application.is_expelled = is_expelled
                application.date = date
                application.is_checked = is_checked
            else:
                application = ApplicationEducation(mmis_id=pa_mmis_id_application, card=card).save()
                application.speciality = education_speciality
                application.personal_number = personal_number
                application.is_enrolled = is_enrolled
                application.is_expelled = is_expelled
                application.date = date
                application.is_checked = is_checked
            application.save()

            for pg in person_grade:
                pg_mmis_id = pg.get("Код")
                subject_code = pg.get("Код_Дисциплины")
                subject = Subjects.objects.filter(mmis_id=subject_code).first()
                grade = pg.get("Оценка")
                type_test_code = pg.get("Код_Испытания")
                mmis_id_application = pg.get("Код_Заявления")
                entrance_exam = EntranceExam.objects.filter(card=card, mmis_id=pg_mmis_id).first()
                application = ApplicationEducation.objects.filter(card=card, mmis_id=mmis_id_application)
                if entrance_exam.exist():
                    entrance_exam.grade = grade
                    entrance_exam.subjects = subject
                    entrance_exam.type_test = ExamType.objects.filter(mmis_id=type_test_code).first()
                    entrance_exam.application_education = application
                else:
                    entrance_exam = EntranceExam(card=card, mis_id=pg_mmis_id).save()
                    entrance_exam.grade = grade
                    entrance_exam.subjects = subject
                    entrance_exam.type_test = ExamType.objects.filter(mmis_id=type_test_code).first()
                    entrance_exam.application_education = application
                entrance_exam.save()

        return card
    except Exception as e:
        return f"Exception: {e}"

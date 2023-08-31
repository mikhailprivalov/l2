from clients.models import Individual, Card
from education.models import ApplicationEducation, EducationSpeciality, EntranceExam, Subjects, ExamType, Faculties, Achievement, AchievementType


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
            filter_mmis_id=True,
        )
        card.phone = person_data.Мобильный if person_data.Мобильный else ""
        card.save()
        result_application = []
        step_app = 0
        for pa in person_applications:
            step_app += 1
            pa_mmis_id_application = int(pa.get("Код_Заявления"))
            application = ApplicationEducation.objects.filter(card=card, mmis_id=pa_mmis_id_application).first()
            education_speciality = EducationSpeciality.objects.filter(mmis_id=int(pa.get("Код_Специальности"))).first()
            personal_number = pa.get("НомерЛД")
            is_enrolled = pa.get("Зачислен")
            is_expelled = pa.get("ОтказалсяОтЗачисления")
            date = pa.get("Дата_Подачи")
            is_checked = pa.get("Проверено")
            facultet = pa.get("Факультет")
            if application:
                application.speciality = education_speciality
                application.personal_number = personal_number
                application.is_enrolled = is_enrolled
                application.is_expelled = is_expelled
                application.date = date
                application.is_checked = is_checked
                application.facultet = Faculties.objects.filter(mmis_id=facultet).first()
                application.save()
            else:
                application = ApplicationEducation.objects.create(
                    mmis_id=pa_mmis_id_application,
                    card=card,
                    speciality=education_speciality,
                    personal_number=personal_number,
                    is_enrolled=is_enrolled,
                    is_expelled=is_expelled,
                    date=date,
                    is_checked=is_checked,
                    facultet = Faculties.objects.filter(mmis_id=facultet).first()
                )
                application.save()
            result_application.append(application.pk)

        result_exam = []
        step_exam = 0
        for pg in person_grade:
            step_exam += 1
            pg_mmis_id = int(pg.get("Код"))
            subject_code = int(pg.get("Код_Дисциплины"))
            grade = pg.get("Оценка")
            if grade == "None":
                grade = 0
            type_test_code = int(pg.get("Код_Испытания"))
            mmis_id_application = int(pg.get("Код_Заявления"))
            subject = Subjects.objects.filter(mmis_id=subject_code).first()
            entrance_exam = EntranceExam.objects.filter(card=card, mmis_id=pg_mmis_id).first()
            application = ApplicationEducation.objects.filter(card=card, mmis_id=mmis_id_application).first()
            if application:
                if entrance_exam:
                    entrance_exam.grade = grade
                    entrance_exam.subjects = subject
                    entrance_exam.type_test = ExamType.objects.filter(mmis_id=type_test_code).first()
                    entrance_exam.application_education = application
                    entrance_exam.save()
                else:
                    entrance_exam = EntranceExam.objects.create(
                        card=card,
                        mmis_id=pg_mmis_id,
                        grade=grade,
                        subjects=subject,
                        type_test=ExamType.objects.filter(mmis_id=type_test_code).first(),
                        application_education=application
                    )
                    entrance_exam.save()
                result_exam.append(entrance_exam.pk)

        result_achievements = []

        for pach in person_achievements:
            pach_mmis_id = int(pach.get("Код"))
            pach_code = int(pach.get("КодИД"))
            achievement_type = AchievementType.objects.filter(mmis_id=pach_code).first()
            pach_date = pach.get("ДатаИД")
            pach_grade = int(pach.get("БаллИД"))
            pach_serial = pach.get("СерияИД")
            pach_number = pach.get("НомерИД")
            pach_organization = pach.get("ОрганизацияИД")

            achievement_person = Achievement.objects.filter(card=card, mmis_id=pach_mmis_id).first()
            if achievement_person:
                achievement_person.type = achievement_type
                achievement_person.document_number = pach_number
                achievement_person.document_serial = pach_serial
                achievement_person.document_date = pach_date
                achievement_person.grade = pach_grade
                achievement_person.organization = pach_organization
                achievement_person.save()
            else:
                achievement_person = Achievement.objects.create(
                    card=card,
                    mmis_id=pach_mmis_id,
                    type=achievement_type,
                    document_number=pach_number,
                    document_serial=pach_serial,
                    document_date=pach_date,
                    grade=pach_grade,
                    organization=pach_organization
                )
                achievement_person.save()
            result_achievements.append(achievement_person.pk)
        return {
            "card": card,
            "result_application": result_application,
            "result_exam": result_exam,
            "result_chievements": result_achievements
        }
    except Exception as e:
        return f"Exception: {e}"


def get_all_enrollees(request):
    individuals_mmis = Individual.objects.filter(mmis_id__isnull=False)
    cards_mmis = Card.objects.filter(individual__in=individuals_mmis)
    applications_mmis = ApplicationEducation.objects.filter(card__in=cards_mmis)
    grades_mmis = EntranceExam.objects.filter(application_education__in=applications_mmis)

    # "card": 1,
    # "fio": 'Котова Аделия Ивановна',
    # "application": '1-СТОМ-ОО',
    # "сhemistry": 33,
    # "biology": 43,
    # "mathematics": 55,
    # "russian_language": 33,
    # "achievement": 3,
    # "achievementСhecked": 3,
    # "totalPoints": 555,
    # "is_original": True,
    # "status": 'Принято',
    # "create_date": '12.07.2023 16:59', }

    result = []
    for i in grades_mmis:
        result.append({
            "card": i.card_id,
            "fio": i.card.individual.fio(),
            "application": f"{i.application_education.speciality} {i.application_education.personal_number}",
            "сhemistry": "",
            "biology": 43,
            "mathematics": 55,
            "russian_language": 33,
            "achievement": "0",
            "totalPoints": 555,
            "is_original": i.application_education,
            "status": i.application_education.is_checked,
            "create_date": i.application_education.date,
        })

    return result

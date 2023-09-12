from clients.models import Individual
from directory.models import Researches
from education.models import ApplicationEducation, EducationSpeciality, EntranceExam, Subjects, ExamType, Faculties, Achievement, AchievementType
from education.sql_func import get_dashboard_data
import simplejson as json

from laboratory.settings import MMIS_CONNECT_WITH_PYODBC
from laboratory.utils import current_year
from slog.models import Log
from users.models import DoctorProfile


def change_encoding_cp1251(text):
    if not MMIS_CONNECT_WITH_PYODBC and text:
        text = text.encode("latin-1").decode('cp1251')
    return text


def update_education_individual(person_data, user_hospital_obj, person_applications, person_grade, person_achievements):
    try:
        card = Individual.import_from_simple_data(
            {
                "family": change_encoding_cp1251(person_data.Фамилия),
                "name": change_encoding_cp1251(person_data.Имя),
                "patronymic": change_encoding_cp1251(person_data.Отчество) if person_data.Отчество else '',
                "sex": "м" if "м" in change_encoding_cp1251(person_data.Пол.lower()) else "ж",
                "birthday": person_data.Дата_Рождения.strftime("%d.%m.%Y"),
                "snils": person_data.СНИЛС if person_data.СНИЛС else "",
            },
            user_hospital_obj,
            person_data.ID,
            "",
            "",
            filter_mmis_id=True,
        )
        tel = person_data.Мобильный if person_data.Мобильный else ""
        tel = tel.replace("+7", "")
        card.phone = tel
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
            facultet_id = pa.get("Факультет")
            original = pa.get("Оригинал") or False
            facultet = Faculties.objects.filter(mmis_id=facultet_id).first()
            if application:
                application.speciality = education_speciality
                application.personal_number = personal_number
                application.is_enrolled = is_enrolled
                application.is_expelled = is_expelled
                application.date = date
                application.is_checked = is_checked
                application.facultet = facultet
                application.original = original
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
                    facultet=facultet,
                    original=original,
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
                        card=card, mmis_id=pg_mmis_id, grade=grade, subjects=subject, type_test=ExamType.objects.filter(mmis_id=type_test_code).first(), application_education=application
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
            pach_mmis_id_application = pach.get("Код_Заявления")
            app_obj = ApplicationEducation.objects.filter(mmis_id=pach_mmis_id_application).first()
            achievement_person = Achievement.objects.filter(card=card, mmis_id=pach_mmis_id).first()
            if achievement_person:
                achievement_person.type = achievement_type
                achievement_person.document_number = pach_number
                achievement_person.document_serial = pach_serial
                achievement_person.document_date = pach_date
                achievement_person.grade = pach_grade
                achievement_person.organization = pach_organization
                achievement_person.application_source_pk = pach_mmis_id_application
                achievement_person.application = app_obj
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
                    organization=pach_organization,
                    application_source_pk=pach_mmis_id_application,
                    application=app_obj,
                )
                achievement_person.save()
            result_achievements.append(achievement_person.pk)
        return {"card": card, "result_application": result_application, "result_exam": result_exam, "result_chievements": result_achievements}
    except Exception as e:
        system_user = DoctorProfile.objects.filter(is_system_user=True).first()
        except_data = {"mmis_id": person_data.ID, "last_name": change_encoding_cp1251(person_data.Фамилия), "first_name": change_encoding_cp1251(person_data.Имя),
                       "patronymic": change_encoding_cp1251(person_data.Отчество), "exception": str(e)}
        Log.log(
            person_data.ID,
            200000,
            system_user,
            except_data
        )


def get_all_enrollees(request):
    request_data = json.loads(request.body)
    filters = request_data.get("filters", {})
    specialities_pk = filters.get("specialities", {})
    year_study = filters.get("yearStudy", {})
    enrolled = filters.get("enrolled", {})
    expelled = filters.get("expelled", {})
    if not year_study:
        year_study = current_year()
    else:
        year_study = year_study.get('label')
    research_contract_ids = Researches.objects.filter(is_contract=True).values_list('id', flat=True)
    data = get_dashboard_data(year_study, tuple(research_contract_ids))
    last_app_id = -1
    template_result = {
        "card": "",
        "fio": "",
        "applicationSpeciality": "",
        "applicationPersonNumber": "",
        "сhemistry": 0,
        "biology": 0,
        "mathematics": 0,
        "russian_language": 0,
        "achievementPoint": 0,
        "totalPoints": 0,
        "is_original": "",
        "status": "",
        "create_date": "",
        "researchContractId": None,
    }
    step = 0
    data_res = []
    temp_result = template_result.copy()
    for i in data:
        date = i.app_data.strftime('%d.%m.%Y')
        if specialities_pk and (i.special_id not in specialities_pk):
            continue
        if enrolled and (not i.is_enrolled or i.is_expelled):
            continue
        if expelled and (not i.is_expelled):
            continue
        if last_app_id != i.app_id and step != 0:
            temp_result["totalPoints"] = temp_result["сhemistry"] + temp_result["biology"] + temp_result["russian_language"] + temp_result["achievementPoint"]
            data_res.append(temp_result.copy())
            temp_result = template_result.copy()
        temp_result["card"] = i.card_id
        temp_result["fio"] = f"{i.ind_family} {i.ind_name} {i.ind_patronymic}"
        temp_result["applicationSpeciality"] = i.special_title
        temp_result["applicationPersonNumber"] = i.personal_number
        temp_result["is_original"] = i.original
        temp_result["is_enrolled"] = i.is_enrolled
        if i.is_enrolled and research_contract_ids:
            temp_result["researchContractId"] = i.direction_id
        temp_result["is_expelled"] = i.is_expelled
        temp_result["create_date"] = date
        if i.subj_title.lower() in ["химия", "основы химии"]:
            temp_result["сhemistry"] = i.grade if i.grade else 0
        if i.subj_title.lower() in ["биология"]:
            temp_result["biology"] = i.grade if i.grade else 0
        if i.subj_title.lower() in ["русский язык"]:
            temp_result["russian_language"] = i.grade if i.grade else 0

        last_app_id = i.app_id
        step += 1
    if temp_result.get("card"):
        temp_result["totalPoints"] = temp_result["сhemistry"] + temp_result["biology"] + temp_result["russian_language"] + temp_result["achievementPoint"]
        data_res.append(temp_result.copy())
    return data_res

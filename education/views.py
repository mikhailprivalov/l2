from clients.models import Individual


def update_education_individual(person_data, user_hospital_obj, person_grade, person_applications, person_achievements):
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
        )

        return card
    except Exception as e:
        return f"Exception: {e}"

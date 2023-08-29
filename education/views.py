from clients.models import Individual


def save_education_individual(person_data, person_grade, user_hospital_obj):
    try:
        print(person_data.Дата_Рождения.strftime("%d.%m.%Y"))
        card = Individual.import_from_simple_data(
            {
                "family": person_data.Фамилия,
                "name": person_data.Имя,
                "patronymic": person_data.Отчество,
                "sex": "м" if "м" in person_data.Пол.lower() else "ж" ,
                "birthday": person_data.Дата_Рождения.strftime("%d.%m.%Y"),
                "snils": person_data.СНИЛС if person_data.СНИЛС else "" ,
            },
            user_hospital_obj,
            person_data.ID,
            "",
            "",
        )

        return card
    except Exception as e:
        return f"Exception: {e}"

from django.db import connection

from utils.db import namedtuplefetchall


def get_applications():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT education_applicationeducation.card_id, family, name, patronymic, speciality_id, users_speciality.title, score FROM public.education_applicationeducation
            LEFT JOIN public.clients_card ON public.education_applicationeducation.card_id = public.clients_card.id
            LEFT JOIN public.clients_individual ON clients_card.individual_id = clients_individual.id
            LEFT JOIN public.users_speciality ON public.education_applicationeducation.speciality_id = public.users_speciality.id
            LEFT JOIN public.education_entranceexam on education_entranceexam.card_id = education_applicationeducation.card_id
        """,
            params={},
        )

        rows = namedtuplefetchall(cursor)
    return rows

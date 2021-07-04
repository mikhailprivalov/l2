from django.db import connection
from utils.db import namedtuplefetchall


def get_extra_notification_data_for_pdf(directions):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                directions_issledovaniya.id as slave_iss,
                directions_issledovaniya.research_id as slave_research_id,
                directions_napravleniya.parent_id as master_iss,
                directions_issledovaniya.napravleniye_id as slave_dir,
                master_direction.master_dir as master_dir,
                master_direction.master_research_id,
                epid_data.epid_title,
                epid_data.epid_value,
                master_book_data.master_field_title,
                master_book_data.master_value,
                master_book_data.master_field_sort
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                
                LEFT JOIN (
                  SELECT  directions_issledovaniya.napravleniye_id as master_dir,
                    directions_issledovaniya.id,
                    directions_issledovaniya.research_id as master_research_id
                    FROM directions_issledovaniya
                ) as master_direction
                ON master_direction.id = directions_napravleniya.parent_id 
                
                LEFT JOIN (
                    SELECT 
                      issledovaniye_id as epid_iss, 
                      value as epid_value, 
                      field_id as epid_field, 
                      directory_paraclinicinputfield.title as epid_title
                    FROM directions_paraclinicresult
                    LEFT JOIN directory_paraclinicinputfield
                    ON directions_paraclinicresult.field_id = directory_paraclinicinputfield.id
                ) as epid_data
                ON directions_issledovaniya.id=epid_data.epid_iss
                RIGHT JOIN (
                    SELECT 
                      issledovaniye_id as master_iss, 
                      value as master_value, 
                      field_id as master_field, 
                      directory_paraclinicinputfield.title as master_field_title,
                      directory_paraclinicinputfield.order as master_field_sort
                    FROM directions_paraclinicresult
                    LEFT JOIN directory_paraclinicinputfield
                    ON directions_paraclinicresult.field_id = directory_paraclinicinputfield.id
                    ) as master_book_data
                ON directions_napravleniya.parent_id=master_book_data.master_iss
                WHERE directions_issledovaniya.napravleniye_id = any(ARRAY[%(num_dirs)s]) 
                AND directions_issledovaniya.time_confirmation is not null 
                AND directions_issledovaniya.research_id = 767 and master_direction.master_research_id=766
                ORDER BY master_dir, master_field_sort
        """,
            params={'num_dirs': directions},
        )
        rows = namedtuplefetchall(cursor)
    return rows


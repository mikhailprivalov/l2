from django.db import connection
from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def extra_notification_sql(master_research, slave_research, date_start, date_end, hospital_id, status):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    directions_issledovaniya.napravleniye_id as dir_id,
                    directions_issledovaniya.research_id as research_id,
                    directions_issledovaniya.time_confirmation as confirm,
                    dirslave.r_research_id,
                    dirslave.r_dir_id,
                    dirslave.r_confirm,
                    dirslave.r_iss_id,
                    individual.pfam,
                    individual.pname,
                    individual.twoname,
                    individual.birthday,
                    dirslave.num_value,
                    hospitals_hospitals.title,
                    directions_napravleniya.hospital_id,
	                hospitals_hospitals.short_title
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN hospitals_hospitals
                ON hospitals_hospitals.id=directions_napravleniya.hospital_id
                LEFT JOIN( 
                        SELECT
                        directions_issledovaniya.id as r_iss_id, 
                        directions_napravleniya.client_id as r_card_id,
                        directions_napravleniya.parent_id as r_paren_id,
                        directions_issledovaniya.napravleniye_id as r_dir_id,
                        directions_issledovaniya.research_id as r_research_id,
                        directions_issledovaniya.time_confirmation as r_confirm,
                        directions_paraclinicresult.value as num_value
                        FROM directions_issledovaniya
                        LEFT JOIN directions_napravleniya
                        ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                        LEFT JOIN directions_paraclinicresult
                        ON directions_paraclinicresult.issledovaniye_id = directions_issledovaniya.id
                        WHERE 
                        directions_issledovaniya.research_id = %(slave_research)s) as dirslave
                ON dirslave.r_paren_id=directions_issledovaniya.id
                LEFT JOIN (
                        SELECT  
                        clients_card.individual_id,
                        clients_individual.id,
                        clients_individual.family  as pfam,
                        clients_individual.name as pname,
                        clients_individual.patronymic as twoname,
                        to_char(clients_individual.birthday, 'DD.MM.YYYY') as birthday,
                        clients_card.id as cl_card
                        FROM clients_card
                        LEFT JOIN clients_individual
                        ON clients_individual.id = clients_card.individual_id
                        ) as individual
                ON directions_napravleniya.client_id=individual.cl_card
                WHERE CASE 
                WHEN  %(hospital_id)s > -1 and %(status)s = 2 THEN 
                    directions_napravleniya.hospital_id = %(hospital_id)s and directions_issledovaniya.research_id = %(master_research)s and
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                
                WHEN  %(hospital_id)s > -1 and %(status)s = 1 THEN 
                    directions_napravleniya.hospital_id = %(hospital_id)s and directions_issledovaniya.research_id = %(master_research)s and
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and dirslave.r_confirm is not null
                
                WHEN  %(hospital_id)s > -1 and %(status)s = 0 THEN 
                    directions_napravleniya.hospital_id = %(hospital_id)s and directions_issledovaniya.research_id = %(master_research)s and
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and dirslave.r_confirm is null
                
                WHEN  %(hospital_id)s = -2 and %(status)s = 2 THEN 
                    directions_issledovaniya.research_id = %(master_research)s and
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                
                WHEN  %(hospital_id)s = -2 and %(status)s = 1 THEN 
                    directions_issledovaniya.research_id = %(master_research)s and
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and dirslave.r_confirm is not null
                    
                WHEN  %(hospital_id)s = -2 and %(status)s = 0 THEN 
                    directions_issledovaniya.research_id = %(master_research)s and
                    directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s and dirslave.r_confirm is null
                
                
                END
                ORDER BY directions_napravleniya.client_id
            """,
            params={'tz': TIME_ZONE, 'master_research': master_research, 'slave_research': slave_research,
                    'd_start': date_start, 'd_end': date_end, 'hospital_id': hospital_id, 'status': status},
        )
        rows = namedtuplefetchall(cursor)
    return rows

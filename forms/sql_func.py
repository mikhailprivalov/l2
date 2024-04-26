from django.db import connection

from laboratory.settings import TIME_ZONE
from utils.db import namedtuplefetchall


def get_extra_notification_data_for_pdf(directions, extra_master_research_id, extra_slave_research_id, with_confirm):
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
                master_book_data.master_field_sort,
                master_book_data.master_field
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
                      directions_paraclinicresult.field_type as master_field,  
                      directory_paraclinicinputfield.title as master_field_title,
                      directory_paraclinicinputfield.order as master_field_sort
                    FROM directions_paraclinicresult
                    LEFT JOIN directory_paraclinicinputfield
                    ON directions_paraclinicresult.field_id = directory_paraclinicinputfield.id
                    ) as master_book_data
                ON directions_napravleniya.parent_id=master_book_data.master_iss
                WHERE directions_issledovaniya.napravleniye_id = any(ARRAY[%(num_dirs)s]) 
                AND
                CASE 
                  WHEN %(with_confirm)s = 1 THEN
                    directions_issledovaniya.time_confirmation is not null
                  WHEN  %(with_confirm)s < 1 THEN
                    directions_issledovaniya.time_confirmation is null
                END
                AND directions_issledovaniya.research_id = %(slave_research_id)s and master_direction.master_research_id = %(master_research_id)s
                ORDER BY master_dir, master_field_sort
        """,
            params={'num_dirs': directions, 'master_research_id': extra_master_research_id, 'slave_research_id': extra_slave_research_id, 'with_confirm': with_confirm},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_covid_to_json(researches, d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT 
                DISTINCT ON (directions_issledovaniya.napravleniye_id)
                    directions_issledovaniya.napravleniye_id as number_direction,
                    hospitals_hospitals.id as hosp_id,
                    hospitals_hospitals.title as laboratoryName,
                    hospitals_hospitals.ogrn laboratoryOgrn,
                    directions_napravleniya.title_org_initiator,
                    directions_napravleniya.ogrn_org_initiator, 
                    tubes.get_tubes,
                    to_char(directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s, 'YYYY-MM-DD') AS date_confirm,
                    directions_issledovaniya.doc_confirmation_id as doc, users_doctorprofile.fio as doc_fio,    
                    individual.pfam,
                    individual.pname,
                    individual.twoname,
                    individual.birthday,
                    individual.psex,
                    individual.ind_id,
                    directory_fractions.title,
                    directory_fractions.fsli,
                    value as value_result,
                    doc_oms.serial as oms_serial,
                    doc_oms.doc_number as oms_number,
                    doc_passport.serial as passport_serial,
                    doc_passport.doc_number as passport_number,
                    doc_snils.doc_number as snils_number,
                    tube_number
                FROM directions_issledovaniya
                LEFT JOIN directions_napravleniya 
                ON directions_issledovaniya.napravleniye_id=directions_napravleniya.id
                LEFT JOIN users_doctorprofile
                ON directions_issledovaniya.doc_confirmation_id=users_doctorprofile.id
                LEFT JOIN hospitals_hospitals
                ON directions_napravleniya.hospital_id=hospitals_hospitals.id
                LEFT JOIN directions_result
                ON directions_issledovaniya.id=directions_result.issledovaniye_id
                LEFT JOIN directory_fractions
                ON directions_result.fraction_id=directory_fractions.id
                LEFT JOIN (
                    SELECT issledovaniya_id,
                    tubesregistration_id,
                    to_char(directions_tubesregistration.time_get AT TIME ZONE %(tz)s, 'YYYY-MM-DD') AS get_tubes,
                    "number" as tube_number
                    FROM directions_issledovaniya_tubes
                    LEFT JOIN directions_tubesregistration
                    ON directions_tubesregistration.id = directions_issledovaniya_tubes.tubesregistration_id
                ) as tubes
                ON tubes.issledovaniya_id = directions_issledovaniya.id
                LEFT JOIN (
                    SELECT  
                    clients_card.individual_id as ind_id,
                    clients_card.polis_id,
                    clients_individual.id,
                    clients_individual.family  as pfam,
                    clients_individual.name as pname,
                    clients_individual.patronymic as twoname,
                    clients_individual.sex as psex,
                    to_char(clients_individual.birthday, 'YYYY-MM-DD') as birthday,
                    clients_card.id as cl_card
                    FROM clients_card
                    LEFT JOIN clients_individual
                    ON clients_individual.id = clients_card.individual_id
                    ) as individual
                ON directions_napravleniya.client_id=individual.cl_card
                LEFT JOIN (
                    SELECT
                    clients_document.individual_id as ind_id,
                    serial, number as doc_number
                    FROM clients_carddocusage
                    LEFT JOIN clients_document
                    ON clients_carddocusage.document_id = clients_document.id
                    WHERE document_type_id in (SELECT id from clients_documenttype where title = 'Полис ОМС')
                    ) as doc_oms
                ON doc_oms.ind_id=individual.ind_id   
                LEFT JOIN (
                    SELECT
                    clients_document.individual_id as ind_id,
                    serial, number as doc_number
                    FROM clients_carddocusage
                    LEFT JOIN clients_document
                    ON clients_carddocusage.document_id = clients_document.id
                    WHERE document_type_id in (SELECT id from clients_documenttype where title = 'Паспорт гражданина РФ')
                    ) as doc_passport
                ON doc_passport.ind_id=individual.ind_id 
                LEFT JOIN (
                    SELECT
                    clients_document.individual_id as ind_id,
                    number as doc_number
                    FROM clients_carddocusage
                    LEFT JOIN clients_document
                    ON clients_carddocusage.document_id = clients_document.id
                    WHERE document_type_id in (SELECT id from clients_documenttype where title = 'СНИЛС')
                    ) as doc_snils
                ON doc_snils.ind_id=individual.ind_id
                
                WHERE directions_issledovaniya.time_confirmation AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                AND directions_issledovaniya.research_id = any(ARRAY[%(researches_pk)s]) 
        """,
            params={'researches_pk': researches, 'd_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def sort_direction_by_file_name_contract(directions, is_create_contract):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT directions_issledovaniya.research_id,
            directory_researches.file_name_contract,
            directions_issledovaniya.napravleniye_id,
            directions_napravleniya.num_contract
            FROM public.directions_issledovaniya
            LEFT JOIN directory_researches on
            directory_researches.id = directions_issledovaniya.research_id
            LEFT JOIN directions_napravleniya on
            directions_napravleniya.id = directions_issledovaniya.napravleniye_id
            where directions_issledovaniya.napravleniye_id in %(directions)s AND  
            CASE 
                WHEN %(is_create_contract)s = '1' THEN directions_napravleniya.num_contract is Null
                WHEN %(is_create_contract)s = '0'THEN directions_napravleniya.num_contract is not Null
            END
            order by directions_napravleniya.num_contract, directory_researches.file_name_contract, directions_issledovaniya.napravleniye_id       
        """,
            params={'directions': directions, 'is_create_contract': is_create_contract},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_research_data_for_contract_specification(price_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            contracts_pricecoast.research_id,
            contracts_pricecoast.coast,
            contracts_pricecoast.number_services_by_contract,
            directory_researches.title as research_title,
            directory_researches.code as research_code
            FROM contracts_pricecoast
            LEFT JOIN directory_researches on
            directory_researches.id = contracts_pricecoast.research_id
            WHERE contracts_pricecoast.price_name_id = %(price_id)s       
        """,
            params={'price_id': price_id},
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_researches():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, internal_code, title, code FROM directory_researches
            WHERE hide=False and internal_code != ''
            ORDER BY internal_code
        """,
        )
        rows = namedtuplefetchall(cursor)
    return rows


def get_coasts(prices_ids):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT coast, price_name_id, research_id FROM contracts_pricecoast
            WHERE price_name_id in %(prices_ids)s
            ORDER BY price_name_id
        """,
            params={"prices_ids": prices_ids},
        )
        rows = namedtuplefetchall(cursor)
    return rows

def get_prices(date_end):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, symbol_code FROM contracts_pricename
            WHERE date_end >= %(date_end)s OR date_end is null
            ORDER BY title
        """,
            params={"date_end": date_end},
        )
        rows = namedtuplefetchall(cursor)
    return rows

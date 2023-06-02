import datetime
import hashlib
import pickle
import threading
import urllib.parse
import logging
from typing import Union, Optional

import requests
import simplejson as json
from django.core.cache import cache
from django.core.management.base import OutputWrapper
from django.db import connections
from django.db.models import Q
from django.test import Client as TC
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder
from simplejson import JSONDecodeError
from zeep import Client as zeepClient, helpers
from zeep.cache import Base
from zeep.exceptions import Fault
from zeep.transports import Transport

import clients.models as clients_models
import slog.models as slog
from appconf.manager import SettingManager
from directions.models import Napravleniya, Result, Issledovaniya, RmisServices, ParaclinicResult, RMISOrgs, RMISServiceInactive, TubesRegistration, Diagnoses
from directory.models import Fractions, ParaclinicInputGroups, Researches
from ecp_integration.integration import search_patient_ecp_by_fio, search_patient_ecp_by_person_id
from hospitals.models import Hospitals
from laboratory import settings as l2settings
from laboratory.settings import MAX_RMIS_THREADS, RMIS_PROXY, ECP_SEARCH_PATIENT
from laboratory.utils import strdate, strtime, localtime, strfdatetime, current_time
from podrazdeleniya.models import Podrazdeleniya
from rmis_integration.sql_func import get_confirm_direction
from utils.common import get_system_name, select_key_by_one_of_values_includes, replace_values_by_keys

logger = logging.getLogger("RMIS")


class Utils:
    @staticmethod
    def get_column_value(row, column):
        try:
            for col in row["column"]:
                if col["name"] == column:
                    return col["data"]
        except:
            return ""

    @staticmethod
    def fix_nmu_code(s: Optional[str]):
        if not s:
            return s
        return s.strip().replace("А", "A").replace("В", "B")

    @staticmethod
    def make_dict(rows, key_column="NAME", value_column="ID"):
        return_dict = {}
        for row in rows:
            return_dict[Utils.get_column_value(row, key_column)] = Utils.get_column_value(row, value_column)
        return return_dict

    @staticmethod
    def get_fin_src_id(typetxt, fin_src: dict):
        if typetxt == "платно":
            typetxt = 'Средства граждан'
        if typetxt == "бюджет":
            typetxt = 'Бюджет муниципальный'
        return fin_src.get(typetxt, fin_src['Безвозмездно'])

    @staticmethod
    def escape(str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        str = str.replace("\"", "&quot;")
        return Utils.fix_sub(str)

    @staticmethod
    def fix_sub(str):
        to_replace = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}
        for k in to_replace.keys():
            str = str.replace(k, to_replace[k])
        return str


class Settings:
    @staticmethod
    def get(key, default=None, default_type='s'):
        return SettingManager.get("rmis_" + key, default=default, default_type=default_type)


def get_md5(s):
    m = hashlib.md5()
    m.update(s.encode())
    return m.hexdigest()


class DjangoCache(Base):
    def __init__(self, timeout=3600):
        self._timeout = timeout

    def k(self, url):
        return "zp_{}".format(str(hashlib.sha256(url.encode()).hexdigest()))

    def add(self, url, content):
        logger.debug("Caching contents of %s", url)
        key = self.k(url)
        cache.set(key, pickle.dumps(content, protocol=4), self._timeout)

    def get(self, url):
        key = self.k(url)
        r = cache.get(key)
        if r:
            logger.debug("Cache HIT for %s", url)
            return pickle.loads(r, encoding="utf8")
        logger.debug("Cache MISS for %s", url)
        return None


class Client(object):
    def __init__(self, login=None, password=None, modules=None):
        if login is None:
            login = Settings.get("login")
        if password is None:
            password = Settings.get("password")
        if modules is None:
            modules = ["patients", "services", "directions", "rendered_services", "dirservices", "hosp", "department", "tc", "case", "visit"]
        self.base_address = Settings.get("address")
        self.session = Session()
        self.session.auth = HTTPBasicAuth(login, password)
        if RMIS_PROXY:
            self.session.proxies = RMIS_PROXY
        self.clients = {}
        self.directories = {}
        if "patients" in modules:
            self.patients = Patients(self)
        if "services" in modules:
            self.services = Services(self)
        if "directions" in modules:
            self.directions = Directions(self)
        if "rendered_services" in modules:
            self.rendered_services = RenderedServices(self)
        if "dirservices" in modules:
            self.dirservices = DirServices(self)
        if "hosp" in modules:
            self.hosp = Hosp(self)
        if "department" in modules:
            self.department = Department(self)
        if "individuals" in modules:
            self.individuals = Individuals(self)
        if "tc" in modules:
            self.localclient = TC(enforce_csrf_checks=False)
        if "case" in modules:
            self.case = CaseServices(self)
        if "visit" in modules:
            self.visit = VisitServices(self)

    def get_addr(self, address):
        return urllib.parse.urljoin(self.base_address, address)

    def get_client(self, address_key: str, default_path=None) -> zeepClient:
        address = Settings.get(address_key, default_path)
        if address not in self.clients:
            self.clients[address] = zeepClient(self.get_addr(address), transport=Transport(session=self.session, cache=DjangoCache(timeout=300), timeout=25))
        return self.clients[address]

    def load_directories(self, titles: list):
        for title in titles:
            self.directories[title] = Directory(self, title)

    def get_directory(self, title: str):
        if title not in self.directories:
            self.load_directories([title])
        return self.directories[title]

    def search_organization_id(self, q=None, check=False):
        def_hosp = Hospitals.get_default_hospital()
        if not q and def_hosp and def_hosp.rmis_org_id:
            return def_hosp.rmis_org_id
        query = q or Settings.get("orgname")
        key = 'rmis_organization_id_' + get_md5(query)
        id = cache.get(key)
        if check and id is not None:
            cache.delete(key)
        if id is None:
            id = self.get_directory("pim_organization").get_first("ID", "FULL_NAME", query)
            cache.set(key, id, 24 * 3600)
        return id

    def get_org_id_for_direction(self, direction: Napravleniya):
        if not direction.hospital:
            return self.search_organization_id()
        if direction.hospital.rmis_org_id:
            return direction.hospital.rmis_org_id
        org_id = self.search_organization_id(q=direction.hospital.title)
        if org_id:
            return org_id
        return self.search_organization_id()

    def get_organization_title(self, pk, full=False):
        key = 'rmis_org_t_%s_%s' % (pk, full)
        data = cache.get(key)
        if not data:
            data = self.get_directory("pim_organization").get_first("SHORT_NAME" if not full else "FULL_NAME", "ID", pk)
            cache.set(key, data, 6 * 3600)
            ex = RMISOrgs.objects.filter(rmis_id=pk).exists()
            if ex and RMISOrgs.objects.get(rmis_id=pk).title != data:
                r = RMISOrgs.objects.get(rmis_id=pk)
                r.title = data
                r.save()
            elif not ex:
                r = RMISOrgs(rmis_id=pk, title=data)
                r.save()
        return data

    def search_dep_id(self, q=None, check=False, org_id=None):
        def_q = Settings.get("depname")
        query = q or def_q
        try:
            key = 'rmis_dep_id_' + get_md5(query)
            id = cache.get(key)
            if check and id is not None:
                cache.delete(key)
            if id is None:
                id = self.get_directory("pim_department").get_first("ID", "NAME", query, org_id=org_id)
                cache.set(key, id, 24 * 60 * 60)
        except:
            id = None
            if def_q != query:
                id = self.search_dep_id(q=def_q)
        return id

    def get_fin_dict(self):
        rp = self.get_directory("fin_funding_source_type").get_all_values()
        fin_src = {}
        for r in rp:
            rr = r['column']
            id = ''
            val = ''
            for rrr in rr:
                if rrr["name"] == "NAME":
                    id = rrr["data"]
                if rrr["name"] == "ID":
                    val = rrr["data"]
            fin_src[id] = val
        return fin_src

    def put_content(self, filename, content, path, filetype='application/pdf', method="PUT", stdout: OutputWrapper = None):
        multipart_data = MultipartEncoder(
            fields={'file': (filename, content, filetype)},
        )

        resip = requests.request(method, path, data=multipart_data, headers={'Content-Type': "multipart/form-data"}, auth=self.session.auth, proxies=RMIS_PROXY)
        if stdout:
            stdout.write("put_content ANSWER: [{}] {}".format(resip.status_code, resip.text))
        return str(resip.status_code) == "200"

    def get_content(self, path):
        resip = requests.request("GET", path, auth=self.session.auth, proxies=RMIS_PROXY)
        return resip.text

    def req(self, path, method="DELETE", ret="bool"):
        resip = requests.request(method, path, auth=self.session.auth)
        if ret == "bool":
            return str(resip.status_code) == "200"
        elif ret == "json":
            try:
                return json.loads(resip.content)
            except JSONDecodeError:
                return []
        else:
            return resip.content

    def local_get(self, addr: str, params: dict):
        return self.localclient.get(addr, params).content


class BaseRequester(object):
    def __init__(self, client: Client, client_path: str, default_path=None):
        self.main_client = client
        self.client = self.main_client.get_client(client_path, default_path).service


class Directory(BaseRequester):
    def __init__(self, client: Client, title: str):
        super().__init__(client, "path_directory")
        self.title = title
        key_code = "d_cd_{}".format(title)
        self.code = cache.get(key_code)
        if not self.code:
            refbook_list = self.main_client.get_client("path_directory").service.getRefbookList()
            self.refbook_list = refbook_list
            for refbook in self.refbook_list:
                if Utils.get_column_value(refbook, "TABLE_NAME") == self.title:
                    self.code = Utils.get_column_value(refbook, "CODE")
                    cache.set(key_code, self.code, 43200)
                    break

    def get_values_by_data(self, search_name="NAME", search_data=""):
        key = "d_g_v_b_d_{}:{}-{}".format(self.code, search_name, search_data).replace(" ", "^")
        if "MemcachedCache" in l2settings.CACHES.get("default", {}).get("BACKEND", ""):
            key = str(hashlib.sha256(key.encode()).hexdigest())
        rrd_src = cache.get(key)
        if rrd_src:
            r = pickle.loads(rrd_src, encoding="utf8")
        else:
            r = self.client.getRefbookRowData(refbookCode=self.code, version="CURRENT", column={"name": search_name, "data": search_data})
            cache.set(key, pickle.dumps(r, protocol=4), 3600)
        return r

    def get_all_values(self):
        key = "d_g_a_v_{}".format(self.code)
        gav_src = cache.get(key)
        if gav_src:
            r = pickle.loads(gav_src, encoding="utf8")
        else:
            r = self.client.getRefbook(refbookCode=self.code, version="CURRENT")
            cache.set(key, pickle.dumps(r, protocol=4), 3600)
        return r

    def get_with_filter(self, value_column, filter_column, filter_data, search_name="NAME", search_data=""):
        rows = self.get_values_by_data(search_name=search_name, search_data=search_data)
        for row in rows:
            if Utils.get_column_value(row, filter_column) == filter_data:
                return Utils.get_column_value(row, value_column)

    def get_first(self, column, search_name="NAME", search_data="", org_id=None):
        values = self.get_values_by_data(search_name, search_data)
        if len(values) > 0:
            if not org_id:
                return Utils.get_column_value(values[0], column)
            for row in values:
                OID = Utils.get_column_value(row, "ORG_ID")
                if OID == org_id:
                    return Utils.get_column_value(row, column)
        return None


class Individuals(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_individuals")

    def update_patient_data(self, card: clients_models.Card):
        data = {
            "individualId": card.number,
            "individualData": {
                "name": card.individual.name,
                "patrName": card.individual.patronymic,
                "surname": card.individual.family,
                "gender": {"ж": "2"}.get(card.individual.sex.lower(), "1"),
                "birthDate": card.individual.birthday,
            },
        }
        d = self.client.editIndividual(**data)
        return d

    def documents(self, card: clients_models.Card):
        return self.client.getIndividualDocuments(card.number)

    def createIndividual(self, individual: clients_models.Individual):
        data = {
            "name": individual.name,
            "patrName": individual.patronymic,
            "surname": individual.family,
            "gender": {"ж": "2"}.get(individual.sex.lower(), "1"),
            "birthDate": individual.birthday,
        }
        return self.client.createIndividual(**data)


class Patients(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_patients")
        key = "zeep_pat_v2"
        r = cache.get(key)

        if not r:
            r = {}
            document_types_directory = client.get_directory("pc_doc_type")
            dts = document_types_directory.get_values_by_data(search_data="Полис")
            r["polis_types_id_list"] = [Utils.get_column_value(x, "ID") for x in dts]
            r["local_types"] = {}
            r["reverse_types"] = {}

            for t in clients_models.DocumentType.objects.all():
                if 'Полис ОМС' in t.title:
                    for dtp in r["polis_types_id_list"]:
                        r["reverse_types"][dtp] = t.pk
                tmp = [Utils.get_column_value(x, "ID") for x in document_types_directory.get_values_by_data(search_data=t.title)]
                if len(tmp) > 0:
                    r["local_types"][t.pk] = tmp[0]
                    r["reverse_types"][tmp[0]] = t.pk
                elif t.title == "СНИЛС":
                    r["local_types"][t.pk] = Settings.get("snils_id", default="19")
                    r["reverse_types"][Settings.get("snils_id", default="19")] = t.pk
                elif t.title == "Иностранный паспорт":
                    r["local_types"][t.pk] = Settings.get("foreign_passport_id", default="18")
                    r["reverse_types"][Settings.get("foreign_passport_id", default="18")] = t.pk
                if t.rmis_type != r["local_types"][t.pk]:
                    t.rmis_type = r["local_types"][t.pk]
                    t.save()
            cache.set(key, pickle.dumps(r, protocol=4), 3600)
        else:
            r = pickle.loads(r, encoding="utf8")
        self.polis_types_id_list = r["polis_types_id_list"]
        self.local_types = r["local_types"]
        self.local_reverse_types = r["reverse_types"]
        self.patient_client = self.main_client.get_client("path_patient_patients", "patients-ws/patient?wsdl").service
        self.smart_client = self.main_client.get_client("path_smart_patients", "patients-smart-ws/patient?wsdl").service
        self.appointment_client = self.main_client.get_client("path_appointment", "appointment-ws/appointment?wsdl").service

    @staticmethod
    def get_fake_reserves():
        r = []
        from random import randint

        cards = clients_models.Card.objects.filter(base__is_rmis=True, is_archive=False)
        for i in range(10):
            rn = randint(0, cards.count())
            c: clients_models.Card = cards[rn]
            r.append({'uid': c.number, 'patient': c.individual.fio(), 'slot': f'l2-test-{i + rn}', 'timeStart': f'0{i}:00', 'timeEnd': f'0{i}:59'})
        return r

    def get_reserves(self, date: datetime.date, location: Union[int, str]):
        d = self.appointment_client.getReserveFiltered(date=date, location=location)
        r = []
        for dd in d:
            s = dd["status"]
            if s in ['0', '1', '4', '7']:
                continue
            r.append(
                {
                    'uid': dd["patient"]["patientId"],
                    'patient': dd["patient"]["patientName"],
                    'slot': dd["slot"],
                    'timeStart': dd["timePeriod"]["from"].strftime('%H:%M'),
                    'timeEnd': dd["timePeriod"]["to"].strftime('%H:%M'),
                }
            )
        return sorted(r, key=lambda k: k['timeStart'])

    @staticmethod
    def get_fake_slot():
        from django.utils import timezone

        return {
            "status": "unknown",
            "datetime": timezone.now(),
        }

    def get_slot(self, pk: Union[int, str]):
        d = self.appointment_client.getSlot(pk)
        return (
            {
                "status": d["status"],
                "datetime": d["date"],
            }
            if d
            else {}
        )

    def extended_data(self, uid):
        d = self.smart_client.getPatient(uid)
        return {} if d["error"] else d["patientCard"]

    def send_patient(self, card: clients_models.Card):
        data = [
            {
                "patient": {
                    "uid": card.number,
                    "firstName": card.individual.name,
                    "middleName": card.individual.patronymic,
                    "lastName": card.individual.family,
                    "birthDate": card.individual.birthday,
                    "gender": {"ж": "2"}.get(card.individual.sex.lower(), "1"),
                },
            }
        ]
        return self.smart_client.sendPatient(patientCard=data)

    def send_new_patient(self, individual):
        data = {
            "name": individual.name,
            "patrName": individual.patronymic,
            "surname": individual.family,
            "gender": {"ж": "2"}.get(individual.sex.lower(), "1"),
            "birthDate": individual.birthday,
        }
        iuid = self.client.createIndividual(**data)

        self.patient_client.createPatient(patientId=iuid, patientData={})

        ruid = self.smart_client.sendPatient(patientCard={'patient': {'uid': iuid}, 'identifiers': {'code': iuid, 'codeType': '7', 'issueDate': strfdatetime(current_time(), "%Y-%m-%d")}})

        return iuid, ruid["patientUid"]

    def edit_patient(self, individual):
        data = {
            "individualId": individual.rmis_uid,
            "individualData": {
                "patrName": individual.patronymic,
                "surname": individual.family,
                "name": individual.name,
                "gender": {"ж": "2"}.get(individual.sex.lower(), "1"),
                "birthDate": individual.birthday,
            },
        }
        self.client.editIndividual(**data)

    def sync_card_data(self, card: clients_models.Card, out: OutputWrapper = None):
        if out:
            out.write("Синхронизация карты. Получение данных из РМИС...")
        data = self.extended_data(card.number)
        if data:
            if out:
                out.write("Данные получены")
            if 'contacts' in data:
                ps = []
                for c in data["contacts"]:
                    if c["type"] not in ['2', '3', '6']:
                        continue
                    p = c["value"]
                    card.add_phone(p)
                    ps.append(p)
                card.clear_phones(ps)
            if 'addresses' in data:
                for a in data['addresses']:
                    if a["type"] not in '43':
                        continue
                    addr = ', '.join([x['name'] for x in a['entries'] if x['type'] not in ['1', '2', '53'] and x['type']]) + ((', Дом ' + a['house']) if a['house'] else '')
                    if a['apartment']:
                        addr += ', ' + a['apartment']
                    if a["type"] == '4' and card.main_address != addr:
                        card.main_address = addr
                        card.save()
                    if a["type"] == '3' and card.fact_address != addr:
                        card.fact_address = addr
                        card.save()
                    break
            clients_models.Card.add_l2_card(card_orig=card)
        else:
            card.is_archive = True
            card.save()
            if out:
                out.write("Нет данных")

    def search_by_document(self, document: clients_models.Document = None, doc_type_id: str = "", doc_serial: str = "", doc_number: str = ""):
        if document is not None:
            if document.document_type_id in self.local_types:
                doc_type_id = str(self.local_types[document.document_type_id])
                doc_serial = document.serial
                doc_number = document.number
            else:
                return []
        search_dict = {}
        if doc_serial != "":
            search_dict["docSeries"] = doc_serial
        elif doc_type_id == "24":
            doc_type_id = "26"
        search_dict["docNumber"] = doc_number
        search_dict["docTypeId"] = doc_type_id
        if search_dict["docNumber"] == "":
            return []
        return self.client.searchIndividual(searchDocument=search_dict)

    def patient_ids_by_poils(self, polis_serial, polis_number) -> list:
        patients = []
        for polis_type_id in self.polis_types_id_list:
            patients = self.search_by_document(doc_type_id=polis_type_id, doc_serial=polis_serial, doc_number=polis_number)
            if len(patients) > 0:
                break
        return patients

    def get_data(self, uid, forced_data=None, return_none_on_empty=False):
        from_rmis = forced_data or self.client.getIndividual(uid)
        if (not from_rmis or not from_rmis['surname'] or not from_rmis["name"]) and return_none_on_empty:
            return None
        return dict(
            family=(from_rmis["surname"] or "").title().strip(),
            name=(from_rmis["name"] or "").title().strip(),
            patronymic=(from_rmis["patrName"] or "").title().strip(),
            birthday=from_rmis["birthDate"],
            sex={"1": "м", "2": "ж"}.get(from_rmis["gender"], "м"),
        )

    def sync_data(self, card: clients_models.Card, forced_data=None):
        if not card.base.is_rmis:
            return False
        q = card.number
        data = self.get_data(q, forced_data=forced_data)
        ind = card.individual

        def n(s):
            return (
                s.lower()
                .replace("ё", "е")
                .replace('%', '')
                .replace('`', '')
                .replace('~', '')
                .replace('-', '')
                .replace(',', '')
                .replace('\'', '')
                .replace('"', '')
                .replace('$', '')
                .replace('@', '')
                .replace('*', '')
                .replace('.', '')
                .replace('!', '')
                .replace('&', '')
                .strip()
            )

        def cmp(a: str, b: str):
            a = n(a)
            b = n(b)
            return a == b

        updated = []
        if not cmp(ind.family, data["family"]):
            updated.append(["family", ind.family, data["family"]])
            ind.family = data["family"]
            ind.save()
        if not card.individual.card_set.filter(base__is_rmis=False).exists():
            if ind.name != data["name"]:
                updated.append(["name", ind.name, data["name"]])
                ind.name = data["name"]
                ind.save()

            if ind.patronymic != data["patronymic"]:
                updated.append(["patronymic", ind.patronymic, data["patronymic"]])
                ind.patronymic = data["patronymic"]
                ind.save()

            if ind.birthday != data["birthday"] and data["birthday"] is not None:
                updated.append(["birthday", strdate(ind.birthday), data["birthday"].strftime("%d.%m.%Y")])
                ind.birthday = data["birthday"]
                ind.save()

            if ind.sex != data["sex"]:
                updated.append(["sex", ind.sex, data["sex"]])
                ind.sex = data["sex"]
                ind.save()
        if len(updated) > 0:
            return str(updated)
        return False

    def patient_first_id_by_poils(self, polis_serial, polis_number) -> str:
        if polis_number != "":
            patients = self.patient_ids_by_poils(polis_serial, polis_number)
            if len(patients) == 1:
                return patients[0]
        return "NONERMIS"

    @staticmethod
    def create_rmis_card(individual: clients_models.Individual, get_id: str, strict=True):
        base = clients_models.CardBase.objects.filter(is_rmis=True).first()
        if not individual.rmis_uid and individual.rmis_uid != get_id:
            individual.rmis_uid = get_id
            individual.save(update_fields=['rmis_uid'])
        if get_id:
            if not clients_models.Card.objects.filter(base=base, number=get_id, is_archive=False).exists():
                for cm in clients_models.Card.objects.filter(base=base, individual=individual):
                    cm.is_archive = True
                    cm.save()
                c = clients_models.Card(base=base, number=get_id, individual=individual, is_archive=False)
                c.save()
                return c
            elif not strict:
                return clients_models.Card.objects.filter(base=base, number=get_id, is_archive=False)[0]
        return None

    def get_rmis_id_for_individual(self, individual: clients_models.Individual):
        return_none = "NONERMIS"
        for doc in clients_models.Document.objects.filter(individual=individual, document_type__title="Полис ОМС"):
            get_id = self.patient_first_id_by_poils(doc.serial, doc.number)
            if get_id != "":
                self.create_rmis_card(individual, get_id)
                return get_id
        return return_none

    def get_l2_card_by_enp(self, enp: str):
        get_id = self.patient_first_id_by_poils("", enp)
        logger.exception(f'{enp} <-> {get_id}')
        if get_id not in ['', 'NONERMIS']:
            if clients_models.Card.objects.filter(number=get_id, base__is_rmis=True).exists():
                rmis_card = clients_models.Card.objects.filter(number=get_id, base__is_rmis=True)[0]
                logger.exception(f'{enp}:1 – {rmis_card}')
            elif clients_models.Individual.objects.filter(rmis_uid=get_id).exists():
                i = clients_models.Individual.objects.filter(rmis_uid=get_id)[0]
                rmis_card = self.create_rmis_card(i, get_id)
                logger.exception(f'{enp}:2 – {rmis_card}')
            else:
                i = self.import_individual_to_base(get_id, limit=1)
                logger.exception(f'{enp}:3 – {i}')
                if not i:
                    return None
                logger.exception(f'{enp}:4 – {i[0]}')
                rmis_card = self.create_rmis_card(i[0], get_id, strict=False)
                logger.exception(f'{enp}:5 – {rmis_card}')
            if rmis_card:
                rmis_card.individual.sync_with_rmis(None, self.main_client, True)
                if clients_models.Card.objects.filter(individual=rmis_card.individual, base__internal_type=True).exists():
                    logger.exception(f'{enp}:6')
                    return clients_models.Card.objects.filter(individual=rmis_card.individual, base__internal_type=True)[0]
                logger.exception(f'{enp}:7')
                return clients_models.Card.add_l2_card(card_orig=rmis_card)
        return None

    def import_individual_to_base(self, query, fio=False, limit=10) -> clients_models.Individual or None:
        return_rows = []
        if fio:
            if ECP_SEARCH_PATIENT.get("search"):
                patient = {
                    "family": query.get("surname").replace("%", ""),
                    "name": query.get("name").replace("%", ""),
                    "patronymic": query.get("patrName").replace("%", ""),
                    "birthday": query.get("birthDate"),
                    "snils": "",
                }
                qs = search_patient_ecp_by_fio(patient, return_first_element=False)
            else:
                qs = self.client.searchIndividual(**query)[:limit]
        else:
            qs = [query.upper()]
        polis_type = clients_models.DocumentType.objects.filter(title="Полис ОМС")[0]
        for q in qs:
            if q != "":
                individual = None
                if not ECP_SEARCH_PATIENT.get("search"):
                    individual_row = self.client.getIndividual(q)
                    if individual_row and (individual_row["surname"] or individual_row["name"] or individual_row["patrName"]) and individual_row["birthDate"] is not None:
                        qq = dict(
                            family=(individual_row["surname"] or "").title(),
                            name=(individual_row["name"] or "").title(),
                            patronymic=(individual_row["patrName"] or "").title(),
                            birthday=individual_row["birthDate"],
                            sex={"1": "м", "2": "ж"}.get(individual_row["gender"], "м"),
                        )
                        individual_set = clients_models.Individual.objects.filter(**qq)
                        if not individual_set.exists():
                            individual_set = [clients_models.Individual(**qq)]
                            individual_set[0].save()
                        individual = individual_set[0]
                        document_ids = self.client.getIndividualDocuments(q)
                        for document_id in document_ids:
                            document_object = self.client.getDocument(document_id)
                            if document_object["type"] in self.polis_types_id_list and document_object["active"]:
                                q = dict(
                                    document_type=polis_type,
                                    serial=document_object["series"] or "",
                                    number=document_object["number"] or "",
                                    individual=individual,
                                    is_active=True,
                                )
                                if clients_models.Document.objects.filter(**q).exists():
                                    if q['number'] and not q['serial']:
                                        break
                                    continue
                                doc = clients_models.Document(**q)
                                doc.save()
                                if q['number'] and not q['serial']:
                                    break
                            individual.sync_with_rmis(c=self.main_client, forced_data=individual_row)

                if ECP_SEARCH_PATIENT.get("search"):

                    individual_row = search_patient_ecp_by_person_id(q)
                    individual = clients_models.Individual.import_from_ecp(individual_row)
                return_rows.append(individual)
        return return_rows


class Services(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_services")

        org_id = client.search_organization_id()

        key = "zeep_services"
        r = cache.get(key)

        if not r:
            self.services = {}
            srv = self.client.getServices(clinic=org_id)
            for r in srv:
                if RMISServiceInactive.isInactive(r["id"]):
                    continue
                self.services[Utils.fix_nmu_code(r["code"])] = r["id"]

            cache.set(key, pickle.dumps(self.services, protocol=4), 300)
        else:
            self.services = pickle.loads(r, encoding="utf8")

        self.external_services = {
            org_id: self.services,
        }

    def get_service_data(self, pk):
        key = "get_service_d{}".format(pk)
        gav_src = cache.get(key)
        if gav_src:
            r = pickle.loads(gav_src, encoding="utf8")
        else:
            r = self.client.getService(pk)
            cache.set(key, pickle.dumps(r, protocol=4), 180)
        return r

    def get_service_id(self, s):
        s = Utils.fix_nmu_code(s)
        if s in self.services:
            return self.services[s]
        return None

    def get_service_id_for_direction(self, s, direction: Napravleniya):
        s = Utils.fix_nmu_code(s)
        org_id = self.main_client.get_org_id_for_direction(direction)
        if org_id not in self.external_services:
            self.external_services[org_id] = {}
            srv = self.client.getServices(clinic=org_id)
            for r in srv:
                if RMISServiceInactive.isInactive(r["id"]):
                    continue
                self.external_services[org_id][Utils.fix_nmu_code(r["code"])] = r["id"]
        return self.external_services.get(org_id, {}).get(s)

    def get_service_ids(self, direction: Napravleniya):
        services_tmp = []
        rmis_id_rend = []
        for iss in Issledovaniya.objects.filter(napravleniye=direction):
            if iss.research.rmis_id:
                rmis_id_rend.append(iss.research.rmis_id)
                continue
            services_tmp.append(iss.research.code)
            for f in Fractions.objects.filter(research=iss.research):
                services_tmp.append(f.code)

        return rmis_id_rend + [y for y in [self.get_service_id_for_direction(x, direction) for x in list(set(services_tmp))] if y is not None]


def ndate(d: Union[datetime.datetime, datetime.date]):
    if isinstance(d, datetime.date):
        return f"{d.year}-{d.month:02}-{d.day:02}"
    return localtime(d).strftime("%Y-%m-%d")


def get_direction_full_data_key(pk):
    return "gdfd_{}".format(pk)


def get_direction_full_data_cache(pk):
    r = None
    k = get_direction_full_data_key(pk)
    d = cache.get(k)
    if d:
        r = pickle.loads(d, encoding="utf8")
    return r


class Directions(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_directions")
        self.covid_service_codes = {
            'A26.08.044.001',
            'A26.08.027.001',
        }
        self.covid_values = {
            'undetected': {
                "результат": "РНК вируса SARS-CоV2 не обнаружена",
                "результат defining": '<code_string xml:space="preserve">at0006</code_string>',
                "диагноз value": '',
                "диагноз defining_code": '<terminology_id/>',
            },
            'detected': {
                "результат": "РНК вируса SARS-CоV2 обнаружена",
                "результат defining": '<code_string xml:space="preserve">at0005</code_string>',
                "диагноз value": '<value xml:space="preserve">U07.1  COVID-19, вирус идентифицирован</value>',
                "диагноз defining_code": '''<terminology_id>
                           <value xml:space="preserve">MD-Base-UI-Diagnosis</value>	
                        </terminology_id>
                        <code_string xml:space="preserve">404</code_string>''',
            },
        }

        # Порядок определения ключей важен
        self.allowed_covid_values = {
            'undetected': ('не обнаружен', 'отрицат'),
            'detected': ('обнаружен', 'положительн'),
        }

    def get_covid_value(self, orig_value: str):
        orig_value = orig_value.lower().strip()
        key = select_key_by_one_of_values_includes(orig_value, self.allowed_covid_values)
        return self.covid_values.get(key)

    def service_is_covid(self, code):
        code = Utils.fix_nmu_code(code)
        return code in self.covid_service_codes

    def search_directions(self, **kwargs):
        return self.client.searchReferral(**kwargs)

    def get_direction_data(self, pk):
        key = "gdd_{}".format(pk)
        gav_src = cache.get(key)
        if gav_src:
            r = pickle.loads(gav_src, encoding="utf8")
        else:
            r = self.client.getReferralById(pk)
            cache.set(key, pickle.dumps(r, protocol=4), 180)
        return r

    def get_direction_full_data(self, pk):
        raw = self.get_direction_data(pk)
        data = {}
        if raw["refServiceId"]:
            data["pk"] = pk
            data["referralOrganization"] = self.main_client.get_organization_title(pk=raw["referralOrganizationId"])
            data["referralOrganizationPk"] = raw["referralOrganizationId"]
            data["diagnosis"] = ""
            data["diagnosisName"] = ""
            if raw["diagnosisId"]:
                v = self.main_client.get_directory("md_diagnosis").get_values_by_data(search_name="ID", search_data=raw["diagnosisId"])
                if len(v) > 0:
                    v = v[0]
                    data["diagnosis"] = Utils.get_column_value(v, "CODE")
                    data["diagnosisName"] = Utils.get_column_value(v, "NAME")
            data["referralDate"] = strdate(raw["referralDate"])
            data["services"] = []
            for s in raw["refServiceId"]:
                srv_d = self.main_client.services.get_service_data(s)
                srv = {"pk": s, "title": srv_d["name"], "code": srv_d["code"]}

                ls = (
                    []
                    if srv["code"] in [None, ""]
                    else [x.pk for x in Researches.objects.filter(Q(code=srv["code"]) | Q(fractions__code=srv["code"], fractions__hide=False)).filter(hide=False).distinct()]
                )
                srv["local_services"] = ls
                srv["selected_local_service"] = -1 if len(ls) != 1 else ls[0]
                srv["exclude_direction"] = False

                data["services"].append(srv)
        cache.set(get_direction_full_data_key(pk), pickle.dumps(data, protocol=4), 600)
        return data

    def get_individual_active_directions(self, uid):
        rows = self.search_directions(receivingOrganizationId=self.main_client.search_organization_id(), refStatusId=2, patientUid=uid)
        return rows

    def delete_direction(self, user, direction: Napravleniya):
        d = False
        self.delete_services(direction, user=user)
        try:
            if direction.rmis_number not in [None, "", "NONERMIS"]:
                self.client.deleteReferral(direction.rmis_number)
            direction.rmis_number = ""
            direction.save()
            d = True
            slog.Log(key=direction.pk, type=3001, body=json.dumps({}), user=user).save()
        except Fault:
            pass
        return d

    def delete_services(self, direction: Napravleniya, user):
        deleted = [RmisServices.objects.filter(napravleniye=direction).count()]
        for row in RmisServices.objects.filter(napravleniye=direction):
            deleted.append(self.main_client.rendered_services.delete_service(row.rmis_id))
        RmisServices.objects.filter(napravleniye=direction).delete()
        attachments = self.main_client.req(self.main_client.get_addr("referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number), method="GET", ret="json")
        if len(attachments) > 1:
            attachments = [int(x) for x in attachments]
            attachment = max(attachments)
            deleted.append(self.main_client.req(self.main_client.get_addr("referral-attachments-ws/rs/referralAttachments/" + str(attachment))))
            deleted.append(attachments)
        direction.result_rmis_send = False
        direction.rmis_hosp_id = ""
        direction.rmis_case_id = ""
        direction.rmis_resend_services = True
        if direction.rmis_number == "NONERMIS":
            direction.rmis_number = ""
        direction.save()
        slog.Log(key=direction.pk, type=3000, body=json.dumps({}), user=user).save()
        return deleted

    def check_send(self, direction: Napravleniya, stdout: OutputWrapper = None):
        client_rmis = direction.client.individual.check_rmis()
        if (
            client_rmis
            and client_rmis != "NONERMIS"
            and (
                not direction.rmis_number
                or direction.rmis_number == ""
                or direction.rmis_number == "NONERMIS"
                or (direction.imported_from_rmis and not direction.imported_directions_rmis_send)
            )
        ):
            if not direction.imported_from_rmis:
                ref_data = dict(
                    patientUid=client_rmis,
                    number=str(direction.pk),
                    typeId=self.main_client.get_directory("md_referral_type").get_first("ID", search_data=direction.rmis_direction_type()),
                    referralDate=ndate(direction.data_sozdaniya_local),
                    referralOrganizationId=self.main_client.get_org_id_for_direction(direction),
                    referringDepartmentId=self.main_client.search_dep_id(q=direction.rmis_referral_title(), org_id=self.main_client.get_org_id_for_direction(direction)),
                    receivingOrganizationId=self.main_client.get_org_id_for_direction(direction),
                    receivingDepartmentId=self.main_client.search_dep_id(q=direction.rmis_department_title(), org_id=self.main_client.get_org_id_for_direction(direction)),
                    refServiceId=self.main_client.services.get_service_ids(direction),
                    fundingSourceTypeId=Utils.get_fin_src_id(direction.fin_title, self.main_client.get_fin_dict()),
                    note=f'Автоматический вывод из Информационной Системы {get_system_name()}',
                    goalId=self.main_client.get_directory("md_referral_goal").get_first("ID", search_data=Settings.get("cel_title", default="Для коррекции лечения")),
                )

                try:
                    direction.rmis_number = self.client.sendReferral(**ref_data)
                except:
                    stdout.write("Err: " + direction.rmis_referral_title())
                    return
                if direction.client.base.is_rmis and direction.rmis_case_id in ["", None] and direction.rmis_hosp_id in ["", None]:
                    case_id, h_id = self.main_client.hosp.search_last_opened_hosp_record(client_rmis)
                    direction.rmis_case_id = case_id
                    direction.rmis_hosp_id = h_id
            self.main_client.put_content(
                "Napravleniye.pdf",
                self.main_client.local_get("/directions/pdf", {"napr_id": json.dumps([direction.pk]), 'token': "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7"}),
                self.main_client.get_addr("referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number + "/Направление-" + str(direction.pk) + "/direction.pdf"),
            )
            if direction.imported_from_rmis and not direction.imported_directions_rmis_send:
                direction.imported_directions_rmis_send = True
        elif client_rmis == "NONERMIS":
            direction.rmis_number = "NONERMIS"
        self.fill_caseid_hospid(client_rmis, direction, stdout)
        direction.save()
        self.check_service(direction, stdout)
        return direction.rmis_number

    def fill_caseid_hospid(self, client_rmis, direction, stdout):
        if client_rmis != "NONERMIS" and direction.rmis_resend_services and direction.client.base.is_rmis and direction.rmis_case_id in ["", None] and direction.rmis_hosp_id in ["", None]:
            case_id, h_id = self.main_client.hosp.search_last_opened_hosp_record(client_rmis)
            if stdout is not None:
                stdout.write("Update case_id and hosp_id %s %s" % (case_id, h_id))
            direction.rmis_case_id = case_id
            direction.rmis_hosp_id = h_id

    def send_service(self, code: str, patient_uid: str, refferal_id: str, direction: Napravleniya) -> str:
        service_id = self.main_client.services.get_service_id_for_direction(code, direction)
        if service_id is None:
            return ""
        send_data = dict(
            referralId=refferal_id,
            serviceId=service_id,
            isRendered="false",
            patientUid=patient_uid,
            orgId=self.main_client.get_org_id_for_direction(direction),
            note=f'Результаты в направлении или в протоколе.\nАвтоматический вывод из МИС {get_system_name()}',
            quantity=1,
        )
        if not direction.imported_from_rmis:
            send_data["fundingSourceTypeId"] = Utils.get_fin_src_id(direction.fin_title, self.main_client.get_fin_dict())
        if direction.rmis_case_id not in [None, ""] and direction.rmis_hosp_id not in [None, ""] and SettingManager.get("rmis_fill_hosp", default='false', default_type='b'):
            send_data["medicalCaseId"] = direction.rmis_case_id
            send_data["stepId"] = direction.rmis_hosp_id
        rendered_id = None
        try:
            rendered_id = self.main_client.rendered_services.client.sendServiceRend(**send_data)
        finally:
            return rendered_id

    def check_service(self, direction: Napravleniya, stdout: OutputWrapper = None):
        if direction.rmis_number == "NONERMIS":
            return
        sended_researches = [None, ""]
        sended_ids = {}
        issledovanya = Issledovaniya.objects.filter(napravleniye=direction)
        individual_rmis_id = self.main_client.patients.get_rmis_id_for_individual(direction.client.individual)
        for row in RmisServices.objects.filter(napravleniye=direction):
            sended_researches.append(row.code)
        self.fill_caseid_hospid(individual_rmis_id, direction, stdout)
        for i in issledovanya:
            code = i.research.code
            self.send_service_if_not_in_sended(code, direction, individual_rmis_id, sended_ids, sended_researches)
            for fraction in Fractions.objects.filter(research=i.research):
                code = fraction.code
                self.send_service_if_not_in_sended(code, direction, individual_rmis_id, sended_ids, sended_researches)
        for k in sended_ids:
            if sended_ids[k] is None:
                continue
            RmisServices(napravleniye=direction, code=k, rmis_id=sended_ids[k]).save()
        direction.rmis_resend_services = False
        direction.save()

    def send_service_if_not_in_sended(self, code, direction, individual_rmis_id, sended_ids, sended_researches):
        if code not in sended_researches:
            sended_researches.append(code)
            sended_ids[code] = self.send_service(code, individual_rmis_id, direction.rmis_number, direction)

    def check_send_results(self, direction: Napravleniya, stdout: OutputWrapper = None):
        protocol_template = Settings.get("protocol_template")
        protocol_covid_template = Settings.get("protocol_covid_template") or ""
        protocol_row = Settings.get("protocol_template_row")
        case_rmis_id = None
        visit_rmis_id = None
        send_visit_data = None
        if not direction.result_rmis_send:
            if direction.rmis_number != "NONERMIS":
                try:
                    rid = self.check_send(direction)
                    if rid and rid != "":
                        rindiv = self.main_client.patients.get_rmis_id_for_individual(direction.client.individual)
                        if rindiv != "NONERMIS":
                            sended_ids = {}
                            for row in RmisServices.objects.filter(napravleniye=direction):
                                sended_ids[row.code] = row.rmis_id
                            sended_researches = []
                            sended_codes = []
                            has_covid = False

                            for x in ParaclinicResult.objects.filter(issledovaniye__napravleniye=direction):
                                code = x.field.group.research.code
                                if code in sended_codes or code.strip() == "":
                                    continue
                                service_rend_id = sended_ids.get(code, None)
                                sended_codes.append(code)
                                if (
                                    x.issledovaniye.research.is_doc_refferal
                                    and (not direction.parent or not direction.parent.research.is_hospital)
                                    and not case_rmis_id
                                    and not visit_rmis_id
                                ):
                                    send_case_data = self.gen_case_rmis(direction, rindiv, x)
                                    case_rmis_id = self.main_client.case.client.sendCase(**send_case_data)
                                    if case_rmis_id:
                                        send_visit_data = self.gen_visit_rmis(direction, rindiv, x, case_rmis_id)
                                    if send_visit_data:
                                        visit_rmis_id = self.main_client.visit.client.sendVisit(**send_visit_data)
                                send_data, ssd = self.gen_rmis_direction_data(code, direction, rid, rindiv, service_rend_id, stdout, x, case_rmis_id, visit_rmis_id)
                                if ssd is not None and x.field.group.research_id not in sended_researches:
                                    RmisServices.objects.filter(napravleniye=direction, rmis_id=service_rend_id).delete()
                                    self.main_client.rendered_services.delete_service(service_rend_id)
                                    sended_researches.append(x.field.group.research_id)
                                    if stdout:
                                        stdout.write("DATA: " + str(send_data))
                                    ss = self.main_client.rendered_services.client.sendServiceRend(**send_data)
                                    xresult = ""
                                    for g in ParaclinicInputGroups.objects.filter(research=x.field.group.research).order_by("order"):
                                        if not ParaclinicResult.objects.filter(issledovaniye__napravleniye=direction, field__group=g).exists():
                                            continue
                                        if g.show_title and g.title != "":
                                            xresult += protocol_row.replace("{{фракция}}", g.title).replace("{{значение}}", "")

                                        for y in ParaclinicResult.objects.filter(issledovaniye__napravleniye=direction, field__group=g).exclude(value="").order_by("field__order"):
                                            v = y.value.replace("\n", "<br/>")
                                            if y.field.field_type == 1:
                                                vv = v.split('-')
                                                if len(vv) == 3:
                                                    v = "{}.{}.{}".format(vv[2], vv[1], vv[0])
                                            xresult += protocol_row.replace("{{фракция}}", y.field.get_title()).replace("{{значение}}", v)
                                    xresult = xresult.replace("{{едизм}}", "").replace("<sub>", "").replace("</sub>", "").replace("<font>", "").replace("</font>", "")
                                    self.put_protocol(code, direction, protocol_template, ss, x, xresult, stdout)
                                    RmisServices(napravleniye=direction, code=code, rmis_id=ss).save()
                            for x in Result.objects.filter(issledovaniye__napravleniye=direction).distinct():
                                code = x.fraction.research.code
                                if code in sended_codes:
                                    continue

                                if code.strip() != "":
                                    service_rend_id = sended_ids.get(code, None)
                                    sended_codes.append(code)
                                    send_data, ssd = self.gen_rmis_direction_data(code, direction, rid, rindiv, service_rend_id, stdout, x)
                                    if ssd is not None and x.fraction.research_id not in sended_researches:
                                        RmisServices.objects.filter(napravleniye=direction, rmis_id=service_rend_id).delete()
                                        self.main_client.rendered_services.delete_service(service_rend_id)
                                        sended_researches.append(x.fraction.research_id)
                                        if stdout:
                                            stdout.write("DATA: " + str(send_data))
                                        ss = self.main_client.rendered_services.client.sendServiceRend(**send_data)
                                        RmisServices(napravleniye=direction, code=code, rmis_id=ss).save()

                                        if self.service_is_covid(code):
                                            has_covid = True
                                            i: Issledovaniya = x.issledovaniye
                                            tube: TubesRegistration = i.tubes.all().first()

                                            date_confirm = "" if not i.time_confirmation else localtime(i.time_confirmation).strftime("%d.%m.%Y")

                                            if tube:
                                                time_get = tube.time_get or tube.time_recive
                                                date_get = "" if not time_get else localtime(time_get).strftime("%d.%m.%Y")
                                            else:
                                                date_get = ""

                                            date_get = date_get or date_confirm

                                            protocol: str = (
                                                protocol_covid_template.replace("{{комментарий}}", i.lab_comment or "")
                                                .replace("{{дата забора}}", date_get)
                                                .replace("{{дата подтверждения}}", date_confirm)
                                                .replace("{{номер результата}}", i.napravleniye.id_in_hospital or str(i.napravleniye.pk))
                                            )
                                            for y in Result.objects.filter(issledovaniye__napravleniye=direction, fraction__research=x.fraction.research).order_by("fraction__sort_weight"):
                                                value = self.get_covid_value(y.value)
                                                if value:
                                                    protocol = replace_values_by_keys(protocol, value)
                                                    break

                                            self.put_protocol(code, direction, protocol, ss, x, "", stdout)
                                        else:
                                            xresult = ""
                                            for y in Result.objects.filter(issledovaniye__napravleniye=direction, fraction__research=x.fraction.research).order_by("fraction__sort_weight"):
                                                xresult += protocol_row.replace("{{фракция}}", y.fraction.title).replace("{{значение}}", y.value).replace("{{едизм}}", y.get_units())
                                            xresult = xresult.replace("<sub>", "").replace("</sub>", "").replace("<font>", "").replace("</font>", "")
                                            if x.issledovaniye.get_analyzer() != "":
                                                xresult += protocol_row.replace("{{фракция}}", "Анализатор").replace("{{значение}}", x.issledovaniye.get_analyzer()).replace("{{едизм}}", "")
                                            if x.issledovaniye.lab_comment and x.issledovaniye.lab_comment != "":
                                                xresult += protocol_row.replace("{{фракция}}", "Комментарий").replace("{{значение}}", x.issledovaniye.lab_comment).replace("{{едизм}}", "")
                                            self.put_protocol(code, direction, protocol_template, ss, x, xresult, stdout)
                                code = x.fraction.code
                                if code in sended_codes or code.strip() == "":
                                    continue
                                service_rend_id = sended_ids.get(code, None)
                                sended_codes.append(code)
                                send_data, ssd = self.gen_rmis_direction_data(code, direction, rid, rindiv, service_rend_id, stdout, x)
                                if ssd is not None:
                                    if stdout:
                                        stdout.write("SR2: " + str(service_rend_id))
                                    send_data["serviceId"] = ssd
                                    if service_rend_id:
                                        service_old_data = self.main_client.rendered_services.get_data_by_id(service_rend_id)
                                        if stdout:
                                            stdout.write("OLD DATA2: " + str(service_old_data))
                                        if service_old_data:
                                            self.fill_send_old_data(send_data, service_old_data)
                                            RmisServices.objects.filter(napravleniye=direction, rmis_id=service_rend_id).delete()
                                            self.main_client.rendered_services.delete_service(service_rend_id)
                                    if stdout:
                                        stdout.write("DATA2: " + json.dumps(send_data))
                                    ss = self.main_client.rendered_services.client.sendServiceRend(**send_data)
                                    if self.service_is_covid(code):
                                        has_covid = True
                                        i: Issledovaniya = x.issledovaniye
                                        tube: TubesRegistration = i.tubes.all().first()

                                        date_confirm = "" if not i.time_confirmation else localtime(i.time_confirmation).strftime("%d.%m.%Y")

                                        if tube:
                                            time_get = tube.time_get or tube.time_recive
                                            date_get = "" if not time_get else localtime(time_get).strftime("%d.%m.%Y")
                                        else:
                                            date_get = ""

                                        date_get = date_get or date_confirm

                                        protocol: str = (
                                            protocol_covid_template.replace("{{комментарий}}", i.lab_comment or "")
                                            .replace("{{дата забора}}", date_get)
                                            .replace("{{дата подтверждения}}", date_confirm)
                                            .replace("{{номер результата}}", i.napravleniye.id_in_hospital or str(i.napravleniye.pk))
                                        )
                                        for y in Result.objects.filter(issledovaniye__napravleniye=direction, fraction__research=x.fraction.research).order_by("fraction__sort_weight"):
                                            value = self.get_covid_value(y.value)
                                            if value:
                                                protocol = replace_values_by_keys(protocol, value)
                                                break

                                        self.put_protocol(code, direction, protocol, ss, x, "", stdout)
                                    else:
                                        xresult = protocol_row.replace("{{фракция}}", x.fraction.title).replace("{{значение}}", x.value).replace("{{едизм}}", x.get_units())
                                        xresult = xresult.replace("<sub>", "").replace("</sub>", "").replace("<font>", "").replace("</font>", "")
                                        if x.issledovaniye.get_analyzer() != "":
                                            xresult += protocol_row.replace("{{фракция}}", "Анализатор").replace("{{значение}}", x.issledovaniye.get_analyzer()).replace("{{едизм}}", "")
                                        self.main_client.put_content(
                                            "Protocol.otg",
                                            protocol_template.replace("{{исполнитель}}", x.issledovaniye.doc_confirmation_fio).replace("{{результат}}", xresult),
                                            self.main_client.get_addr("/medservices-ws/service-rs/renderedServiceProtocols/" + ss),
                                            method="POST",
                                        )
                                    RmisServices(napravleniye=direction, code=code, rmis_id=ss).save()

                            if not has_covid:
                                self.main_client.put_content(
                                    "Resultat.pdf",
                                    self.main_client.local_get("/results/pdf", {"pk": json.dumps([direction.pk]), "normis": '1', 'token': "8d63a9d6-c977-4c7b-a27c-64f9ba8086a7"}),
                                    self.main_client.get_addr(
                                        "referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number + "/Результат-" + str(direction.pk) + "/Resultat.pdf"
                                    ),
                                )
                except Fault as e:
                    logging.exception(e)
                    if "ата смерти пациента" in e.message:
                        direction.rmis_number = "NONERMIS"
                    else:
                        return False
            direction.result_rmis_send = True
            if case_rmis_id or visit_rmis_id:
                direction.rmis_case_id = case_rmis_id
                direction.rmis_visit_id = visit_rmis_id
            direction.save()
        return direction.result_rmis_send

    def get_protocol(self, rendered_service_id):
        return self.main_client.get_content(self.main_client.get_addr("/medservices-ws/service-rs/renderedServiceProtocols/" + rendered_service_id))

    def put_protocol(self, code, direction, protocol_template, ss, x, xresult, stdout: OutputWrapper = None):
        protocol = protocol_template.replace("{{исполнитель}}", x.issledovaniye.doc_confirmation_fio).replace("{{результат}}", xresult)
        self.main_client.put_content(
            "Protocol.otg", protocol, self.main_client.get_addr("/medservices-ws/service-rs/renderedServiceProtocols/" + ss), method="POST", filetype="text/xml", stdout=stdout
        )
        RmisServices(napravleniye=direction, code=code, rmis_id=ss).save()
        if stdout:
            stdout.write("put_protocol: {} {} {} {} {}".format(code, direction, protocol, ss, x))

    def fill_send_old_data(self, send_data, service_old_data):
        for p in [
            "medicalCaseId",
            "stepId",
            "diagnosisId",
            "referralId",
            "serviceId",
            "orgId",
            "fundingSourceTypeId",
            "dateFrom",
            "timeFrom",
            "dateTo",
            "note",
            "quantity",
            "patientUid",
            "plannedDate",
            "plannedTime",
        ]:
            send_data[p] = service_old_data.get(p, None) or send_data.get(p, None)

    def gen_case_rmis(self, direction: Napravleniya, rindiv, x):
        purpose = "1" if not x.issledovaniye.purpose else x.issledovaniye.purpose.rmis_id or "1"
        place = "1" if not x.issledovaniye.place else x.issledovaniye.place.rmis_id or "1"

        new_case_data = {
            "uid": direction.pk,
            "patientUid": rindiv,
            "caseTypeId": "1",
            "medicalOrganizationId": self.main_client.get_org_id_for_direction(direction),
            "fundingSourceTypeId": Utils.get_fin_src_id(direction.fin_title, self.main_client.get_fin_dict()),
            "careLevelId": "8",
            "paymentMethodId": "26",
            "initGoalId": purpose,
            "careRegimenId": place,
            "createdDate": ndate(x.issledovaniye.time_confirmation),
        }
        return new_case_data

    def gen_visit_rmis(self, direction: Napravleniya, rindiv, x, case_rid):
        if not case_rid:
            return None
        profile = x.issledovaniye.research.speciality
        if not profile or not profile.rmis_id:
            return None
        resource_group_id = x.issledovaniye.doc_confirmation.rmis_resource_id
        if not resource_group_id:
            return None
        diagnos = x.issledovaniye.diagnos.split(" ")[0]
        if not diagnos:
            return None
        diagnos_rmis_id = Diagnoses.objects.values_list('rmis_id', flat=True).filter(code=diagnos, hide=False)
        if not diagnos_rmis_id:
            return None

        visit_data = {
            "caseId": case_rid,
            "diagnoses": {
                "stageId": "3",
                "diagnosId": diagnos_rmis_id[0],
                "establishmentDate": f"{ndate(x.issledovaniye.time_confirmation)}+08:00",
                "main": "true",
            },
            # "visitResultId": 9,
            # "deseaseResultId": "1",
            "admissionDate": ndate(x.issledovaniye.time_confirmation),
            "admissionTime": strtime(x.issledovaniye.time_confirmation),
            "rendererDate": ndate(x.issledovaniye.time_confirmation),
            "resourceGroupId": resource_group_id,
            "goalId": "1",
            "placeId": "1",
            "profileId": profile.rmis_id,
        }
        return visit_data

    def close_case_rmis(self):
        pass

    def gen_rmis_direction_data(self, code, direction: Napravleniya, rid, rindiv, service_rend_id, stdout, x, case_rmis_id=None, visit_rmis_id=None):
        ssd = self.main_client.services.get_service_id_for_direction(code, direction)
        send_data = dict(
            referralId=rid,
            serviceId=ssd,
            isRendered="true",
            quantity="1",
            orgId=self.main_client.get_org_id_for_direction(direction),
            dateFrom=ndate(x.issledovaniye.time_confirmation),
            timeFrom=strtime(x.issledovaniye.time_confirmation),
            dateTo=ndate(x.issledovaniye.time_confirmation),
            note=f'Результаты в направлении на фирменном бланке или в протоколе.\nАвтоматический вывод из {get_system_name()}',
            patientUid=rindiv,
        )
        if not direction.imported_from_rmis:
            send_data["fundingSourceTypeId"] = Utils.get_fin_src_id(direction.fin_title, self.main_client.get_fin_dict())
        if stdout:
            stdout.write("SR: " + str(service_rend_id))
        if service_rend_id:
            service_old_data = self.main_client.rendered_services.get_data_by_id(service_rend_id)
            if stdout:
                stdout.write("OLD DATA: " + str(service_old_data))
            if service_old_data:
                self.fill_send_old_data(send_data, service_old_data)
        send_data["dateFrom"] = ndate(send_data["dateFrom"]) if send_data["dateFrom"] and not isinstance(send_data["dateFrom"], str) else send_data["dateFrom"]
        send_data["timeFrom"] = strtime(send_data["timeFrom"]) if send_data["timeFrom"] and not isinstance(send_data["timeFrom"], str) else send_data["timeFrom"]
        send_data["dateTo"] = ndate(send_data["dateTo"]) if send_data["dateTo"] and not isinstance(send_data["dateTo"], str) else send_data["dateTo"]
        if case_rmis_id:
            send_data["medicalCaseId"] = case_rmis_id
        if visit_rmis_id:
            send_data["stepId"] = visit_rmis_id

        return send_data, ssd

    def check_and_send_all(self, stdout: OutputWrapper = None, without_results=False, maxthreads=MAX_RMIS_THREADS, slice_to_upload: bool = False, slice_to_upload_count=None):
        def check_lock():
            return cache.get('upload_lock') is not None

        if not slice_to_upload:
            if check_lock():
                if stdout:
                    stdout.write("Lockfile exists. EXIT")
                return

        def update_lock():
            cache.set('upload_lock', '1', 15)
            pass

        sema = threading.BoundedSemaphore(maxthreads)
        threads = list()

        upload_after = Settings.get("upload_results_after", default="11.09.2017")
        date = datetime.date(int(upload_after.split(".")[2]), int(upload_after.split(".")[1]), int(upload_after.split(".")[0])) - datetime.timedelta(minutes=20)
        uploaded = []
        exclude_res = Researches.objects.filter(Q(is_hospital=True) | Q(is_slave_hospital=True))
        to_upload = (
            Napravleniya.objects.filter(data_sozdaniya__gte=date)
            .filter(Q(rmis_number__isnull=True) | Q(rmis_number="") | Q(imported_from_rmis=True, imported_directions_rmis_send=False))
            .exclude(issledovaniya__research__in=exclude_res)
            .distinct()
        )
        slice_to_upload_count = slice_to_upload_count or MAX_RMIS_THREADS * 2
        if slice_to_upload:
            stdout.write("Total to upload directions: {}".format(to_upload.count()))
            stdout.write("Slice to upload directions: {}".format(slice_to_upload_count))
            to_upload = to_upload[:slice_to_upload_count]
        cnt = to_upload.count()
        if stdout:
            stdout.write("Directions to upload: {}".format(cnt))
        i = 0

        def upload_dir(self, direct, out, i, s):
            s.acquire()
            update_lock()
            try:
                uploaded.append(self.check_send(direct, out))
                if out:
                    out.write("Upload direction {} ({}/{}); RMIS number={}".format(direct.pk, i, cnt, uploaded[-1]))
            finally:
                s.release()

            try:
                connections.close_all()
                if out:
                    out.write("Closed db connections")
            except Exception as e:
                if out:
                    out.write(f"Error closing connections {e}")

        def upload_services(self, direct, out, s):
            s.acquire()
            update_lock()
            try:
                self.check_service(direct, out)
                if out:
                    out.write("Check services for direction {}; RMIS number={}".format(direct.pk, direct.rmis_number))
            finally:
                s.release()

            try:
                connections.close_all()
                if out:
                    out.write("Closed db connections")
            except Exception as e:
                if out:
                    out.write(f"Error closing connection {e}")

        def upload_results(self, direct, out, i, s):
            s.acquire()
            update_lock()
            try:
                direct = Napravleniya.objects.get(pk=direct)
                uploaded_results.append(self.check_send_results(direct))
                if out:
                    out.write("Upload result for direction {} ({}/{})".format(direct.pk, i, cnt))
            finally:
                s.release()

            try:
                connections.close_all()
                if out:
                    out.write("Closed db connections")
            except Exception as e:
                if out:
                    out.write(f"Error closing connection {e}")

        for d in to_upload:
            i += 1
            thread = threading.Thread(target=upload_dir, args=(self, d, stdout, i, sema))
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

        sema = threading.BoundedSemaphore(maxthreads)

        threads = []
        to_upload = Napravleniya.objects.filter(data_sozdaniya__gte=date, rmis_resend_services=True).exclude(rmis_number='NONERMIS').distinct()
        if slice_to_upload:
            stdout.write("Total to upload resend services: {}".format(to_upload.count()))
            stdout.write("Slice to upload resend services: {}".format(slice_to_upload_count))
            to_upload = to_upload[:slice_to_upload_count]
        for d in to_upload:
            thread = threading.Thread(target=upload_services, args=(self, d, stdout, sema))
            threads.append(thread)
            thread.start()

        for t in threads:
            t.join()

        sema = threading.BoundedSemaphore(maxthreads)

        threads = []

        uploaded_results = []
        if not without_results:
            upload_lt = current_time() - datetime.timedelta(hours=Settings.get("upload_hours_interval", default="8", default_type="i"))
            direction_ids = get_confirm_direction(date, upload_lt, slice_to_upload_count if slice_to_upload else 10000)
            cnt = len(direction_ids)
            stdout.write("To upload results: {}".format(cnt))
            if slice_to_upload:
                stdout.write("Directions: {}".format(direction_ids))
            i = 0
            for d in direction_ids:
                i += 1
                thread = threading.Thread(target=upload_results, args=(self, d[0], stdout, i, sema))
                threads.append(thread)
                thread.start()
            [t.join() for t in threads]

        return {"directions": [x for x in uploaded if x != ""], "results": [x for x in uploaded_results if x != ""]}


class RenderedServices(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_medservices")

    def get_data_by_id(self, service_id):
        try:
            return helpers.serialize_object(self.client.getServiceRendById(str(service_id)))
        except Fault:
            return {}

    def delete_service(self, service_id):
        try:
            return self.client.deleteServiceRend(str(service_id))
        except Fault as e:
            return str(e)


class CaseServices(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_caseservices")


class VisitServices(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_visitservices")


class DirServices(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_dirservices")

    def get_service_id_by_code(self, code, orgid=None):
        resp = self.client.getServices(clinic=orgid or self.main_client.search_organization_id(), code=code)
        id = -1
        if len(resp) > 0:
            id = int(resp[0]["id"])
        return id

    def get_service_data(self, id, type_id=""):
        resp = self.client.getService(id)
        data = {
            'type': resp["type"] if type_id in ["", "None"] else type_id,
            'code': resp["code"],
            'name': resp["name"],
            'terms': resp["terms"],
            'independent': True,
            'multiplicity': resp["multiplicity"],
            'finType': resp["finType"],
        }
        return data

    def createService(self, data, orgid=None):
        data["clinic"] = orgid or self.main_client.search_organization_id()
        resp = self.client.createService(service=data)
        return resp


class Hosp(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_hosp")

    def search_last_opened_hosp_record(self, patient_uid, orgid=None):
        if not SettingManager.get("rmis_fill_hosp", default='false', default_type='b'):
            return None, None
        resp = self.client.searchHspRecord(medicalOrganizationId=orgid or self.main_client.search_organization_id(), patientUid=patient_uid)
        last_id = None
        last_case_id = None
        for row in reversed(resp):
            if row is None:
                continue
            try:
                d = self.get_hosp_details(row)
                t = helpers.serialize_object(d).get("outcomeDate", None)
                v = t is None or t >= datetime.datetime.now().date()
                if v:
                    last_id = row
                    last_case_id = helpers.serialize_object(d).get("caseId", None)
                    break
            except Fault:
                pass
        return last_case_id, last_id

    def get_hosp_details(self, id):
        resp = self.client.getHspRecordById(id)
        return resp


class Department(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_departments")

    def get_departments(self, orgid=None):
        resp = self.client.getDepartments(orgid or self.main_client.search_organization_id())
        return [dict(self.get_department(x), id=x) for x in resp]

    def get_department(self, department_id):
        resp = self.client.getDepartment(department_id)
        return helpers.serialize_object(resp)

    def sync_departments(self):
        toadd = toupdate = 0
        for dep in self.get_departments():
            if Podrazdeleniya.objects.filter(rmis_id=dep["id"]).exists():
                p = Podrazdeleniya.objects.filter(rmis_id=dep["id"])[0]
                p.title = dep["name"]
                p.isLab = any([x in dep["name"] for x in ["лаборатория", "КДЛ", "Лаборатория"]])
                p.save()
                toupdate += 1
            else:
                p = Podrazdeleniya(title=dep["name"], isLab=any([x in dep["name"] for x in ["лаборатория", "КДЛ", "Лаборатория"]]), rmis_id=dep["id"])
                p.save()
                toadd += 1
        return toadd, toupdate

import datetime
import hashlib
import threading
import urllib.parse

import requests
from django.core.cache import cache
from django.core.management.base import OutputWrapper
from django.db.models import Q
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder
from simplejson import JSONDecodeError
from zeep import Client as zeepClient, helpers
from zeep.exceptions import Fault
from zeep.transports import Transport

import clients.models as clients_models
from appconf.manager import SettingManager
from directions.models import Napravleniya, Result, Issledovaniya, RmisServices
from directory.models import Fractions
from podrazdeleniya.models import Podrazdeleniya


class Utils:
    @staticmethod
    def get_column_value(row, column):
        try:
            for col in row["column"]:
                if col["name"] == column:
                    return col["data"]
        except Exception:
            return ""

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
        str = str.replace("₀", "0")
        str = str.replace("₁", "1")
        str = str.replace("₂", "2")
        str = str.replace("₃", "3")
        str = str.replace("₄", "4")
        str = str.replace("₅", "5")
        str = str.replace("₆", "6")
        str = str.replace("₇", "7")
        str = str.replace("₈", "8")
        str = str.replace("₉", "9")
        return str


class Settings:
    @staticmethod
    def get(key, default=None, default_type='s'):
        return SettingManager.get("rmis_" + key, default=default, default_type=default_type)


def get_md5(s):
    m = hashlib.md5()
    m.update(s.encode())
    return m.hexdigest()


from django.test import Client as TC


class Client(object):
    def __init__(self, login=Settings.get("login"), password=Settings.get("password")):
        self.base_address = Settings.get("address")
        self.session = Session()
        self.session.auth = HTTPBasicAuth(login, password)
        self.clients = {}
        self.directories = {}
        self.load_directories(titles=["pim_organization",
                                      "pim_department",
                                      "pc_doc_type",
                                      "md_referral_type",
                                      "md_referral_goal",
                                      "fer_se_service_type",
                                      "fin_funding_source_type"])
        self.patients = Patients(self)
        self.services = Services(self)
        self.directions = Directions(self)
        self.rendered_services = RenderedServices(self)
        self.dirservices = DirServices(self)
        self.hosp = Hosp(self)
        self.department = Department(self)
        self.localclient = TC(enforce_csrf_checks=False)
        cstatus = self.localclient.login(username=Settings.get("local_user", default="rmis"),
                                         password=Settings.get("local_password",
                                                               default="clientDirections.service.sendReferral"))
        if not cstatus:
            raise Exception("Не могу войти в L2")

    def get_addr(self, address):
        return urllib.parse.urljoin(self.base_address, address)

    def get_client(self, address_key: str) -> zeepClient:
        address = Settings.get(address_key)
        if address not in self.clients:
            self.clients[address] = zeepClient(self.get_addr(address),
                                               transport=Transport(session=self.session))
        return self.clients[address]

    def load_directories(self, titles: list):
        for title in titles:
            self.directories[title] = Directory(self, title)

    def get_directory(self, title: str):
        if title not in self.directories:
            self.load_directories([title])
        return self.directories[title]

    def search_organization_id(self, q=None, check=False):
        query = q or Settings.get("orgname")
        key = 'rmis_organization_id_' + get_md5(query)
        id = cache.get(key)
        if check and id is not None:
            cache.delete(key)
        if id is None:
            id = self.get_directory("pim_organization").get_first("ID", "FULL_NAME", query)
            cache.set(key, id, 24 * 60 * 60)
        return id

    def search_dep_id(self, q=None, check=False):
        def_q = Settings.get("depname")
        query = q or def_q
        try:
            key = 'rmis_dep_id_' + get_md5(query)
            id = cache.get(key)
            if check and id is not None:
                cache.delete(key)
            if id is None:
                id = self.get_directory("pim_department").get_first("ID", "NAME", query)
                cache.set(key, id, 24 * 60 * 60)
        except IndexError:
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

    def put_content(self, filename, content, path, filetype='application/pdf', method="PUT"):
        multipart_data = MultipartEncoder(
            fields={'file': (filename, content, filetype)},
        )
        resip = requests.request(method, path,
                                 data=multipart_data,
                                 headers={'Content-Type': "multipart/form-data"}, auth=self.session.auth)
        return str(resip.status_code) == "200"

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
    def __init__(self, client: Client, client_path: str):
        self.main_client = client
        self.client = self.main_client.get_client(client_path).service


class Directory(BaseRequester):
    def __init__(self, client: Client, title: str):
        super().__init__(client, "path_directory")
        self.title = title
        refbook_list = self.main_client.get_client("path_directory").service.getRefbookList()
        self.refbook_list = refbook_list
        for refbook in self.refbook_list:
            if Utils.get_column_value(refbook, "TABLE_NAME") == self.title:
                self.code = Utils.get_column_value(refbook, "CODE")
                break

    def get_values_by_data(self, search_name="NAME", search_data=""):
        return self.client.getRefbookRowData(refbookCode=self.code, version="CURRENT",
                                             column={"name": search_name, "data": search_data})

    def get_all_values(self):
        return self.client.getRefbook(refbookCode=self.code, version="CURRENT")

    def get_with_filter(self, value_column, filter_column, filter_data, search_name="NAME", search_data=""):
        rows = self.get_values_by_data(search_name=search_name, search_data=search_data)
        for row in rows:
            if Utils.get_column_value(row, filter_column) == filter_data:
                return Utils.get_column_value(row, value_column)

    def get_first(self, column, search_name="NAME", search_data=""):
        values = self.get_values_by_data(search_name, search_data)
        if len(values) > 0:
            return Utils.get_column_value(values[0], column)
        return None


class Patients(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_patients")
        self.document_types_directory = client.get_directory("pc_doc_type")
        self.polis_types_id_list = [Utils.get_column_value(x, "ID") for x in
                                    self.document_types_directory.get_values_by_data(search_data="Полис")]
        self.local_types = {}
        for t in clients_models.DocumentType.objects.all():
            tmp = [Utils.get_column_value(x, "ID") for x in
                   self.document_types_directory.get_values_by_data(search_data=t.title)]
            if len(tmp) > 0:
                self.local_types[t.pk] = tmp[0]
            elif t.title == "СНИЛС":
                self.local_types[t.pk] = "19"

    def search_by_document(self, document: clients_models.Document = None, doc_type_id: str = "", doc_serial: str = "",
                           doc_number: str = ""):
        if document is not None:
            if document.document_type.pk in self.local_types:
                doc_type_id = str(self.local_types[document.document_type.pk])
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
            patients = self.search_by_document(doc_type_id=polis_type_id, doc_serial=polis_serial,
                                               doc_number=polis_number)
            if len(patients) > 0:
                break
        return patients

    def get_data(self, uid):
        from_rmis = self.client.getIndividual(uid)
        return dict(family=(from_rmis["surname"] or "").title().strip(),
                    name=(from_rmis["name"] or "").title().strip(),
                    patronymic=(from_rmis["patrName"] or "").title().strip(),
                    birthday=from_rmis["birthDate"],
                    sex={"1": "м", "2": "ж"}.get(from_rmis["gender"], "м"))

    def sync_data(self, card: clients_models.Card):
        if not card.base.is_rmis:
            return False
        q = card.number
        data = self.get_data(q)
        ind = card.individual

        def n(s):
            return s.lower().replace("ё", "е").replace('%', '').replace('`', '').replace('~', '').replace('-',
                                                                                                          '').replace(
                ',', '').replace('\'', '').replace('"', '').replace('$', '').replace('@', '').replace('*', '').replace(
                '.', '').replace('!', '').replace('&', '').strip()

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
                updated.append(["birthday", ind.birthday.strftime("%d.%m.%Y"), data["birthday"].strftime("%d.%m.%Y")])
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
    def create_rmis_card(individual: clients_models.Individual, get_id: str):
        base = clients_models.CardBase.objects.filter(is_rmis=True, hide=False).first()
        if not clients_models.Card.objects.filter(base=base, number=get_id, is_archive=False).exists():
            clients_models.Card.objects.filter(base=base, individual=individual).update(is_archive=True)
            c = clients_models.Card(base=base, number=get_id, individual=individual, is_archive=False).save()
            return c
        return None

    def get_rmis_id_for_individual(self, individual: clients_models.Individual):
        return_none = "NONERMIS"
        for doc in clients_models.Document.objects.filter(individual=individual, document_type__title="Полис ОМС"):
            get_id = self.patient_first_id_by_poils(doc.serial, doc.number)
            if get_id != "":
                self.create_rmis_card(individual, get_id)
                return get_id
        return return_none

    def import_individual_to_base(self, query, fio=False, limit=10) -> clients_models.Individual or None:
        return_rows = []
        if fio:
            qs = self.client.searchIndividual(**query)[:limit]
        else:
            qs = [query.upper()]
        for q in qs:
            individual_row = None
            if q != "":
                individual_row = self.client.getIndividual(q)
            if individual_row and (
                    (individual_row["surname"] is not None or individual_row["name"] is not None or individual_row[
                        "patrName"] is not None) and individual_row["birthDate"] is not None):
                qq = dict(family=(individual_row["surname"] or "").title(),
                          name=(individual_row["name"] or "").title(),
                          patronymic=(individual_row["patrName"] or "").title(),
                          birthday=individual_row["birthDate"],
                          sex={"1": "м", "2": "ж"}.get(individual_row["gender"], "м"))
                individual_set = clients_models.Individual.objects.filter(**qq)
                if not individual_set.exists():
                    individual_set = [clients_models.Individual(**qq)]
                    individual_set[0].save()
                individual = individual_set[0]
                document_ids = self.client.getIndividualDocuments(q)
                for document_id in document_ids:
                    document_object = self.client.getDocument(document_id)
                    if document_object["type"] in self.polis_types_id_list and document_object["active"]:
                        doc = clients_models.Document(
                            document_type=clients_models.DocumentType.objects.filter(title="Полис ОМС")[0],
                            serial=document_object["series"] or "",
                            number=document_object["number"] or "",
                            individual=individual,
                            is_active=True)
                        doc.save()
                individual.sync_with_rmis(c=self.main_client)
                return_rows.append(individual)
        return return_rows


class Services(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_services")
        self.services = {}
        srv = self.client.getServices(clinic=client.search_organization_id())
        for r in srv:
            self.services[r["code"]] = r["id"]

    def get_service_id(self, s):
        s = s.replace("А", "A").replace("В", "B")
        if s in self.services:
            return self.services[s]
        return None

    def get_service_ids(self, direction: Napravleniya):
        services_tmp = []
        for iss in Issledovaniya.objects.filter(napravleniye=direction):
            services_tmp.append(iss.research.code)
            for f in Fractions.objects.filter(research=iss.research):
                services_tmp.append(f.code)
        return [y for y in [self.get_service_id(x) for x in list(set(services_tmp))] if y is not None]


def ndate(d: datetime.datetime):
    return d.strftime("%Y-%m-%d")


import simplejson as json
from django.utils import timezone
import slog.models as slog


class Directions(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_directions")

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
        attachments = self.main_client.req(
            self.main_client.get_addr("referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number),
            method="GET", ret="json")
        if len(attachments) > 1:
            attachments = [int(x) for x in attachments]
            attachment = max(attachments)
            deleted.append(self.main_client.req(
                self.main_client.get_addr("referral-attachments-ws/rs/referralAttachments/" + str(attachment))))
            deleted.append(attachments)
        direction.result_rmis_send = False
        direction.rmis_hosp_id = ""
        direction.rmis_case_id = ""
        direction.rmis_resend_services = True
        direction.save()
        slog.Log(key=direction.pk, type=3000, body=json.dumps({}), user=user).save()
        return deleted

    def check_send(self, direction: Napravleniya, stdout: OutputWrapper = None):
        client_rmis = direction.client.individual.check_rmis()
        if client_rmis and client_rmis != "NONERMIS" and (
                not direction.rmis_number or direction.rmis_number == "" or direction.rmis_number == "NONERMIS"):
            ref_data = dict(patientUid=client_rmis,
                            number=str(direction.pk),
                            typeId=self.main_client.get_directory(
                                "md_referral_type").get_first("ID",
                                                              search_data=direction.rmis_direction_type()),
                            referralDate=ndate(direction.data_sozdaniya),
                            referralOrganizationId=self.main_client.search_organization_id(),
                            referringDepartmentId=self.main_client.search_dep_id(q=direction.rmis_referral_title()),
                            receivingOrganizationId=self.main_client.search_organization_id(),
                            receivingDepartmentId=self.main_client.search_dep_id(q=direction.rmis_department_title()),
                            refServiceId=self.main_client.services.get_service_ids(direction),
                            fundingSourceTypeId=Utils.get_fin_src_id(
                                direction.istochnik_f.title,
                                self.main_client.get_fin_dict()),
                            note='Автоматический вывод из Лабораторной Информационной Системы L2',
                            goalId=self.main_client.get_directory(
                                "md_referral_goal").get_first("ID",
                                                              search_data=Settings.get(
                                                                  "cel_title",
                                                                  default="Для коррекции лечения")))

            try:
                direction.rmis_number = self.client.sendReferral(**ref_data)
            except:
                stdout.write("Err: " + direction.rmis_referral_title())
                return
            if direction.client.base.is_rmis and direction.rmis_case_id in ["", None] and direction.rmis_hosp_id in ["",
                                                                                                                     None]:
                case_id, h_id = self.main_client.hosp.search_last_opened_hosp_record(client_rmis)
                direction.rmis_case_id = case_id
                direction.rmis_hosp_id = h_id
            self.main_client.put_content("Napravleniye.pdf",
                                         self.main_client.local_get("/directions/pdf",
                                                                    {"napr_id": json.dumps([direction.pk])}),
                                         self.main_client.get_addr(
                                             "referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number + "/Направление/direction.pdf"))
        elif client_rmis == "NONERMIS":
            direction.rmis_number = "NONERMIS"
        if client_rmis != "NONERMIS" and direction.rmis_resend_services and direction.client.base.is_rmis and direction.rmis_case_id in [
            "", None] and direction.rmis_hosp_id in ["", None]:
            case_id, h_id = self.main_client.hosp.search_last_opened_hosp_record(client_rmis)
            if stdout is not None:
                stdout.write("Update case_id and hosp_id %s %s" % (case_id, h_id))
            direction.rmis_case_id = case_id
            direction.rmis_hosp_id = h_id
        direction.save()
        self.check_service(direction, stdout)
        return direction.rmis_number

    def send_service(self, code: str, patient_uid: str, refferal_id: str, direction: Napravleniya) -> str:
        service_id = self.main_client.services.get_service_id(code)
        if service_id is None:
            return ""
        send_data = dict(referralId=refferal_id, serviceId=service_id, isRendered="false", patientUid=patient_uid,
                         orgId=self.main_client.search_organization_id(),
                         note='Результаты в направлении или в протоколе.\nАвтоматический вывод из ЛИС L2',
                         fundingSourceTypeId=Utils.get_fin_src_id(direction.istochnik_f.title,
                                                                  self.main_client.get_fin_dict()),
                         quantity=1)
        if direction.rmis_case_id not in [None, ""] and direction.rmis_hosp_id not in [None, ""]:
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
        if individual_rmis_id != "NONERMIS" and direction.rmis_resend_services and direction.client.base.is_rmis and direction.rmis_case_id in [
            "", None] and direction.rmis_hosp_id in ["", None]:
            case_id, h_id = self.main_client.hosp.search_last_opened_hosp_record(individual_rmis_id)
            if stdout is not None:
                stdout.write("Update case_id and hosp_id %s %s" % (case_id, h_id))
            direction.rmis_case_id = case_id
            direction.rmis_hosp_id = h_id
        for i in issledovanya:
            code = i.research.code
            if code not in sended_researches:
                sended_researches.append(code)
                sended_ids[code] = self.send_service(code, individual_rmis_id, direction.rmis_number, direction)
            for fraction in Fractions.objects.filter(research=i.research):
                code = fraction.code
                if code not in sended_researches:
                    sended_researches.append(code)
                    sended_ids[code] = self.send_service(code, individual_rmis_id, direction.rmis_number, direction)
        for k in sended_ids:
            if sended_ids[k] is None:
                continue
            RmisServices(napravleniye=direction, code=k, rmis_id=sended_ids[k]).save()
        direction.rmis_resend_services = False
        direction.save()

    def check_send_results(self, direction: Napravleniya, stdout: OutputWrapper = None):
        protocol_template = Settings.get("protocol_template")
        protocol_row = Settings.get("protocol_template_row")
        if not direction.result_rmis_send:
            direction.result_rmis_send = True
            direction.save()
            if direction.rmis_number != "NONERMIS":
                rid = self.check_send(direction)
                if rid and rid != "":
                    rindiv = self.main_client.patients.get_rmis_id_for_individual(direction.client.individual)
                    if rindiv != "NONERMIS":
                        sended_ids = {}
                        for row in RmisServices.objects.filter(napravleniye=direction):
                            sended_ids[row.code] = row.rmis_id
                        sended_researches = []
                        sended_codes = []
                        for x in Result.objects.filter(issledovaniye__napravleniye=direction):
                            code = x.fraction.research.code
                            service_rend_id = sended_ids.get(code, None)
                            if code in sended_codes:
                                continue
                            sended_codes.append(code)
                            ssd = self.main_client.services.get_service_id(code)
                            send_data = dict(referralId=rid,
                                             serviceId=ssd,
                                             isRendered="true",
                                             quantity="1",
                                             orgId=self.main_client.search_organization_id(),
                                             dateFrom=direction.data_sozdaniya.strftime("%Y-%m-%d"),
                                             timeFrom=timezone.localtime(direction.data_sozdaniya).strftime("%X"),
                                             dateTo=x.issledovaniye.time_confirmation.strftime("%Y-%m-%d"),
                                             note='Результаты в направлении или в протоколе.\nАвтоматический вывод из ЛИС L2',
                                             fundingSourceTypeId=Utils.get_fin_src_id(direction.istochnik_f.title,
                                                                                      self.main_client.get_fin_dict()),
                                             patientUid=rindiv)
                            if stdout:
                                stdout.write("SR: " + str(service_rend_id))
                            if service_rend_id:
                                service_old_data = self.main_client.rendered_services.get_data_by_id(service_rend_id)
                                if stdout:
                                    stdout.write("OLD DATA: " + str(service_old_data))
                                if service_old_data:
                                    send_data["medicalCaseId"] = service_old_data.get("medicalCaseId",
                                                                                      None) or send_data.get(
                                        "medicalCaseId", None)
                                    send_data["stepId"] = service_old_data.get("stepId", None) or send_data.get(
                                        "stepId", None)
                                    send_data["diagnosisId"] = service_old_data.get("diagnosisId",
                                                                                    None) or send_data.get(
                                        "diagnosisId", None)
                                    send_data["referralId"] = service_old_data.get("referralId", None) or send_data.get(
                                        "referralId", None)
                                    send_data["serviceId"] = service_old_data.get("serviceId", None) or send_data.get(
                                        "serviceId", None)
                                    send_data["orgId"] = service_old_data.get("orgId", None) or send_data.get("orgId",
                                                                                                              None)
                                    send_data["fundingSourceTypeId"] = service_old_data.get("fundingSourceTypeId",
                                                                                            None) or send_data.get(
                                        "fundingSourceTypeId", None)
                                    send_data["dateFrom"] = service_old_data.get("dateFrom", None) or send_data.get(
                                        "dateFrom", None)
                                    send_data["timeFrom"] = service_old_data.get("timeFrom", None) or send_data.get(
                                        "timeFrom", None)
                                    send_data["dateTo"] = service_old_data.get("dateTo", None) or send_data.get(
                                        "dateTo", None)
                                    send_data["note"] = service_old_data.get("note", None) or send_data.get("note",
                                                                                                            None)
                                    send_data["quantity"] = service_old_data.get("quantity", None) or send_data.get(
                                        "quantity", None)
                                    send_data["patientUid"] = service_old_data.get("patientUid", None) or send_data.get(
                                        "patientUid", None)
                                    send_data["plannedDate"] = service_old_data.get("plannedDate",
                                                                                    None) or send_data.get(
                                        "plannedDate", None)
                                    send_data["plannedTime"] = service_old_data.get("plannedTime",
                                                                                    None) or send_data.get(
                                        "plannedTime", None)
                            if ssd is not None and x.fraction.research.pk not in sended_researches:
                                RmisServices.objects.filter(napravleniye=direction, rmis_id=service_rend_id).delete()
                                self.main_client.rendered_services.delete_service(service_rend_id)
                                sended_researches.append(x.fraction.research.pk)
                                if stdout:
                                    stdout.write("DATA: " + json.dumps(send_data))
                                ss = self.main_client.rendered_services.client.sendServiceRend(**send_data)
                                xresult = ""
                                for y in Result.objects.filter(issledovaniye__napravleniye=direction,
                                                               fraction__research=x.fraction.research).order_by(
                                        "fraction__sort_weight"):
                                    xresult += protocol_row.replace("{{фракция}}", y.fraction.title).replace(
                                        "{{значение}}", y.value).replace("{{едизм}}", y.fraction.units)
                                xresult = xresult.replace("<sub>", "").replace("</sub>", "").replace("<font>",
                                                                                                     "").replace(
                                    "</font>", "")
                                if x.issledovaniye.get_analyzer() != "":
                                    xresult += protocol_row.replace("{{фракция}}", "Анализатор").replace("{{значение}}",
                                                                                                         x.issledovaniye.get_analyzer()).replace(
                                        "{{едизм}}", "")
                                if x.issledovaniye.lab_comment and x.issledovaniye.lab_comment != "":
                                    xresult += protocol_row.replace("{{фракция}}", "Комментарий").replace(
                                        "{{значение}}",
                                        x.issledovaniye.lab_comment).replace(
                                        "{{едизм}}", "")
                                sd = self.main_client.put_content("Protocol.otg",
                                                                  protocol_template.replace("{{исполнитель}}",
                                                                                            x.issledovaniye.doc_confirmation.get_fio()).replace(
                                                                      "{{результат}}", xresult),
                                                                  self.main_client.get_addr(
                                                                      "/medservices-ws/service-rs/renderedServiceProtocols/" + ss),
                                                                  method="POST",
                                                                  filetype="text/xml")
                                RmisServices(napravleniye=direction, code=code, rmis_id=ss).save()
                            code = x.fraction.code
                            if code in sended_codes:
                                continue
                            service_rend_id = sended_ids.get(code, None)
                            sended_codes.append(code)
                            ssd = self.main_client.services.get_service_id(code)
                            if ssd is not None:
                                if stdout:
                                    stdout.write("SR2: " + str(service_rend_id))
                                send_data["serviceId"] = ssd
                                if service_rend_id:
                                    service_old_data = self.main_client.rendered_services.get_data_by_id(
                                        service_rend_id)
                                    if stdout:
                                        stdout.write("OLD DATA2: " + str(service_old_data))
                                    if service_old_data:
                                        send_data["medicalCaseId"] = service_old_data.get("medicalCaseId",
                                                                                          None) or send_data.get(
                                            "medicalCaseId", None)
                                        send_data["stepId"] = service_old_data.get("stepId", None) or send_data.get(
                                            "stepId", None)
                                        send_data["diagnosisId"] = service_old_data.get("diagnosisId",
                                                                                        None) or send_data.get(
                                            "diagnosisId", None)
                                        send_data["referralId"] = service_old_data.get("referralId",
                                                                                       None) or send_data.get(
                                            "referralId", None)
                                        send_data["serviceId"] = service_old_data.get("serviceId",
                                                                                      None) or send_data.get(
                                            "serviceId", None)
                                        send_data["orgId"] = service_old_data.get("orgId", None) or send_data.get(
                                            "orgId", None)
                                        send_data["fundingSourceTypeId"] = service_old_data.get("fundingSourceTypeId",
                                                                                                None) or send_data.get(
                                            "fundingSourceTypeId", None)
                                        send_data["dateFrom"] = service_old_data.get("dateFrom", None) or send_data.get(
                                            "dateFrom", None)
                                        send_data["timeFrom"] = service_old_data.get("timeFrom", None) or send_data.get(
                                            "timeFrom", None)
                                        send_data["dateTo"] = service_old_data.get("dateTo", None) or send_data.get(
                                            "dateTo", None)
                                        send_data["note"] = service_old_data.get("note", None) or send_data.get("note",
                                                                                                                None)
                                        send_data["quantity"] = service_old_data.get("quantity", None) or send_data.get(
                                            "quantity", None)
                                        send_data["patientUid"] = service_old_data.get("patientUid",
                                                                                       None) or send_data.get(
                                            "patientUid", None)
                                        send_data["plannedDate"] = service_old_data.get("plannedDate",
                                                                                        None) or send_data.get(
                                            "plannedDate", None)
                                        send_data["plannedTime"] = service_old_data.get("plannedTime",
                                                                                        None) or send_data.get(
                                            "plannedTime", None)
                                        RmisServices.objects.filter(napravleniye=direction,
                                                                    rmis_id=service_rend_id).delete()
                                        self.main_client.rendered_services.delete_service(service_rend_id)
                                if stdout:
                                    stdout.write("DATA2: " + json.dumps(send_data))
                                ss = self.main_client.rendered_services.client.sendServiceRend(**send_data)
                                xresult = protocol_row.replace("{{фракция}}", x.fraction.title).replace("{{значение}}",
                                                                                                        x.value).replace(
                                    "{{едизм}}", x.fraction.units)
                                xresult = xresult.replace("<sub>", "").replace("</sub>", "").replace("<font>",
                                                                                                     "").replace(
                                    "</font>", "")
                                if x.issledovaniye.get_analyzer() != "":
                                    xresult += protocol_row.replace("{{фракция}}", "Анализатор").replace("{{значение}}",
                                                                                                         x.issledovaniye.get_analyzer()).replace(
                                        "{{едизм}}", "")
                                self.main_client.put_content("Protocol.otg",
                                                             protocol_template.replace("{{исполнитель}}",
                                                                                       x.issledovaniye.doc_confirmation.get_fio()).replace(
                                                                 "{{результат}}", xresult), self.main_client.get_addr(
                                        "/medservices-ws/service-rs/renderedServiceProtocols/" + ss), method="POST")
                                RmisServices(napravleniye=direction, code=code, rmis_id=ss).save()
                        self.main_client.put_content("Resultat.pdf",
                                                     self.main_client.local_get("/results/pdf",
                                                                                {"pk": json.dumps([direction.pk]),
                                                                                 "normis": '1'}),
                                                     self.main_client.get_addr(
                                                         "referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number + "/Результат/Resultat.pdf"))
        return direction.result_rmis_send

    def check_and_send_all(self, stdout: OutputWrapper = None, without_results=False, maxthreads=10):
        def check_lock():
            return cache.get('upload_lock') is not None

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
        date = datetime.date(int(upload_after.split(".")[2]), int(upload_after.split(".")[1]),
                             int(upload_after.split(".")[0])) - datetime.timedelta(minutes=20)
        uploaded = []
        to_upload = Napravleniya.objects.filter(data_sozdaniya__gte=date).filter(
            Q(rmis_number__isnull=True) | Q(rmis_number="")).distinct()
        cnt = to_upload.count()
        if stdout:
            stdout.write("Directions to upload: {}".format(cnt))
        i = 0

        def upload_dir(self, direct, out, i):
            sema.acquire()
            update_lock()
            try:
                uploaded.append(self.check_send(direct, out))
                if out:
                    out.write("Upload direction {} ({}/{}); RMIS number={}".format(direct.pk, i, cnt, uploaded[-1]))
            finally:
                sema.release()

        def upload_services(self, direct, out):
            sema.acquire()
            update_lock()
            try:
                self.check_service(direct, out)
                if out:
                    out.write("Check services for direction {}; RMIS number={}".format(direct.pk, direct.rmis_number))
            finally:
                sema.release()

        def upload_results(self, direct, out, i):
            sema.acquire()
            update_lock()
            try:
                if direct.is_all_confirm():
                    uploaded_results.append(self.check_send_results(direct))
                    if out:
                        out.write("Upload result for direction {} ({}/{})".format(direct.pk, i, cnt))
            finally:
                sema.release()

        for d in to_upload:
            i += 1
            thread = threading.Thread(target=upload_dir, args=(self, d, stdout, i))
            threads.append(thread)
            thread.start()
        [t.join() for t in threads]
        threads = []
        to_upload = Napravleniya.objects.filter(data_sozdaniya__gte=date, rmis_resend_services=True).exclude(
            rmis_number='NONERMIS').distinct()
        for d in to_upload:
            thread = threading.Thread(target=upload_services, args=(self, d, stdout))
            threads.append(thread)
            thread.start()
        [t.join() for t in threads]
        threads = []

        uploaded_results = []
        if not without_results:
            to_upload = Napravleniya.objects.filter(data_sozdaniya__gte=date,
                                                    issledovaniya__time_confirmation__isnull=False,
                                                    rmis_number__isnull=False,
                                                    result_rmis_send=False) \
                .exclude(rmis_number="NONERMIS") \
                .exclude(rmis_number="") \
                .distinct()
            cnt = to_upload.count()
            i = 0
            for d in to_upload:
                i += 1
                thread = threading.Thread(target=upload_results, args=(self, d, stdout, i))
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
        resp = self.client.searchHspRecord(medicalOrganizationId=orgid or self.main_client.search_organization_id(),
                                           patientUid=patient_uid)
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
                p = Podrazdeleniya(title=dep["name"],
                                   isLab=any([x in dep["name"] for x in ["лаборатория", "КДЛ", "Лаборатория"]]),
                                   rmis_id=dep["id"])
                p.save()
                toadd += 1
        return toadd, toupdate

import datetime
import hashlib
import urllib.parse

import requests
from django.core.management.base import OutputWrapper
from django.db.models import Q
from requests_toolbelt import MultipartEncoder

from appconf.manager import SettingManager
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client as zeepClient
from zeep.transports import Transport
import clients.models as clients_models
from django.core.cache import cache

from directions.models import Napravleniya, Result, Issledovaniya
from directory.models import Fractions


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
    def __init__(self):
        self.base_address = Settings.get("address")
        self.session = Session()
        self.session.auth = HTTPBasicAuth(Settings.get("login"), Settings.get("password"))
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
        self.localclient = TC(enforce_csrf_checks=False)
        cstatus = self.localclient.login(username=Settings.get("local_user", default="rmis"),
                                         password=Settings.get("local_password",
                                                               default="clientDirections.service.sendReferral"))
        if not cstatus:
            raise Exception("Не могу войти в ЛИС")

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
        query = q or Settings.get("depname")
        key = 'rmis_dep_id_' + get_md5(query)
        id = cache.get(key)
        if check and id is not None:
            cache.delete(key)
        if id is None:
            id = self.get_directory("pim_department").get_first("ID", "NAME", query)
            cache.set(key, id, 24 * 60 * 60)
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

    def put_content(self, filename, content, path, filetype='application/pdf', type="PUT"):
        multipart_data = MultipartEncoder(
            fields={'file': (filename, content, filetype)},
        )
        resip = requests.request(type, path,
                                 data=multipart_data,
                                 headers={'Content-Type': "multipart/form-data"}, auth=self.session.auth)
        return str(resip.status_code) == "200"

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
        return Utils.get_column_value(self.get_values_by_data(search_name, search_data)[0], column)


class Patients(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_patients")
        self.document_types_directory = client.get_directory("pc_doc_type")
        self.polis_types_id_list = [Utils.get_column_value(x, "ID") for x in
                                    self.document_types_directory.get_values_by_data(search_data="Полис")]

    def search_by_polis(self, doc_type_id: str, polis_serial: str, polis_number: str):
        search_dict = {"docTypeId": doc_type_id}
        if polis_serial != "":
            search_dict["docSeries"] = polis_serial
        if polis_number != "":
            search_dict["docNumber"] = polis_number
        return self.client.searchIndividual(searchDocument=search_dict)

    def patient_ids_by_poils(self, polis_serial, polis_number) -> list:
        patients = []
        for polis_type_id in self.polis_types_id_list:
            patients = self.search_by_polis(polis_type_id, polis_serial, polis_number)
            if len(patients) > 0:
                break
        return patients

    def patient_first_id_by_poils(self, polis_serial, polis_number) -> str:
        if polis_number != "":
            patients = self.patient_ids_by_poils(polis_serial, polis_number)
            if len(patients) == 1:
                return patients[0]
        return "NONERMIS"

    def create_rmis_card(self, individual: clients_models.Individual, get_id: str):
        base = clients_models.CardBase.objects.filter(is_rmis=True, hide=False).first()
        if not clients_models.Card.objects.filter(base=base, number=get_id, is_archive=False).exists():
            clients_models.Card.objects.filter(base=base, individual=individual).update(is_archive=True)
            c = clients_models.Card(base=base, number=get_id, individual=individual, is_archive=False).save()
            return c
        return None

    def get_rmis_id_for_individual(self, individual: clients_models.Individual, update_rmis=False):
        return_none = "NONERMIS"
        for doc in clients_models.Document.objects.filter(individual=individual, document_type__title="Полис ОМС"):
            get_id = self.patient_first_id_by_poils(doc.serial, doc.number)
            if get_id != "":
                self.create_rmis_card(individual, get_id)
                return get_id
        return return_none

    def import_individual_to_base(self, query, fio=False, limit=10) -> clients_models.Individual or None:
        qs = []
        return_rows = []
        if fio:
            qs = self.client.searchIndividual(**query)[:limit]
        else:
            q = [query.upper()]
        for q in qs:
            individual_row = None
            if q != "":
                individual_row = self.client.getIndividual(q)
            if individual_row and (
                        (individual_row["surname"] is not None or individual_row["name"] is not None or individual_row[
                            "patrName"] is not None) and individual_row["birthDate"] is not None):
                individual = clients_models.Individual(family=individual_row["surname"].title() or "",
                                                       name=individual_row["name"].title() or "",
                                                       patronymic=individual_row["patrName"].title() or "",
                                                       birthday=individual_row["birthDate"],
                                                       sex={"1": "м", "2": "ж"}.get(individual_row["gender"], "м"))
                individual.save()
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
                self.create_rmis_card(individual, q)
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


class Directions(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_directions")
        self.baseclient = client

    def check_send(self, direction: Napravleniya):
        client_rmis = direction.client.individual.check_rmis()
        if client_rmis and client_rmis != "NONERMIS" and (not direction.rmis_number or direction.rmis_number == "" or direction.rmis_number == "NONERMIS"):
            direction.rmis_number = self.client.sendReferral(patientUid=client_rmis,
                                                             number=str(direction.pk),
                                                             typeId=self.baseclient.get_directory(
                                                                 "md_referral_type").get_first("ID",
                                                                                               search_data=Settings.get(
                                                                                                   "direction_type_title",
                                                                                                   default="Направление в лабораторию")),
                                                             referralDate=ndate(direction.data_sozdaniya),
                                                             referralOrganizationId=self.baseclient.search_organization_id(),
                                                             referringDepartmentId=self.baseclient.search_dep_id(),
                                                             receivingOrganizationId=self.baseclient.search_organization_id(),
                                                             receivingDepartmentId=self.baseclient.search_dep_id(),
                                                             refServiceId=self.baseclient.services.get_service_ids(
                                                                 direction),
                                                             fundingSourceTypeId=Utils.get_fin_src_id(
                                                                 direction.istochnik_f.tilie,
                                                                 self.baseclient.get_fin_dict()),
                                                             note='Автоматический вывод из Лабораторной Информационной Системы L2',
                                                             goalId=self.baseclient.get_directory(
                                                                 "md_referral_goal").get_first("ID",
                                                                                               search_data=Settings.get(
                                                                                                   "cel_title",
                                                                                                   default="Для коррекции лечения")))
            direction.save()
            self.baseclient.put_content("Napravleniye.pdf",
                                        self.baseclient.local_get("/directions/pdf",
                                                                  {"napr_id": json.dumps([direction.pk])}),
                                        self.baseclient.get_addr(
                                            "referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number + "/Направление/direction.pdf"))
        elif client_rmis == "NONERMIS":
            direction.rmis_number = "NONERMIS"
            direction.save()
        return direction.rmis_number

    def check_send_results(self, direction: Napravleniya):
        protocol_template = Settings.get("protocol_template")
        if not direction.result_rmis_send and direction.rmis_number != "NONERMIS":
            rid = self.check_send(direction)
            if rid and rid != "":
                rindiv = self.baseclient.patients.get_rmis_id_for_individual(direction.client.individual)
                sended_researches = []
                for x in Result.objects.filter(issledovaniye__napravleniye=direction):
                    ssd = self.baseclient.services.get_service_id(x.fraction.research.code)
                    ss = None

                    if ssd is not None and x.fraction.research.pk not in sended_researches:
                        sended_researches.append(x.fraction.research.pk)
                        robj = ["{}: {} {}".format(y.fraction.title, y.value, y.fraction.units) for y in
                                Result.objects.filter(issledovaniye__napravleniye=direction,
                                                      fraction__research=x.fraction.research)][16:21]
                        ss = self.baseclient.rendered_services.client.sendServiceRend(referralId=rid,
                                                                                      serviceId=ssd,
                                                                                      isRendered="true",
                                                                                      patientUid=rindiv,
                                                                                      orgId=self.baseclient.search_organization_id(),
                                                                                      dateFrom=x.issledovaniye.time_confirmation.strftime("%Y-%m-%d"),
                                                                                      dateTo=x.issledovaniye.time_confirmation.strftime("%Y-%m-%d"),
                                                                                      note='Результаты в направлении или в протоколе.\nАвтоматический вывод из ЛИС L2')
                        xresult = ""
                        for y in Result.objects.filter(issledovaniye__napravleniye=direction, fraction__research=x.fraction.research):
                            xresult += "<br/><b>{}</b>: {} {}".format(y.fraction.title, y.value, y.fraction.units).strip()
                        xresult = xresult.replace("<sub>", "").replace("</sub>", "").replace("<font>", "").replace("</font>", "")
                        xresult = Utils.escape("<br/>" + xresult + "<br/>")
                        sd = self.baseclient.put_content("Protocol.otg", protocol_template.replace("{{исполнитель}}", x.issledovaniye.doc_confirmation.get_fio()).replace("{{результат}}", xresult), self.baseclient.get_addr("/medservices-ws/service-rs/renderedServiceProtocols/"+ss), type="POST")
                    if x.fraction.research.pk in sended_researches:
                        continue
                    ssd = self.baseclient.services.get_service_id(x.fraction.code)
                    if ssd is not None:
                        ss = self.baseclient.rendered_services.client.sendServiceRend(referralId=rid,
                                                                                      serviceId=ssd,
                                                                                      isRendered="true",
                                                                                      patientUid=rindiv,
                                                                                      orgId=self.baseclient.search_organization_id(),
                                                                                      dateFrom=x.issledovaniye.time_confirmation.strftime("%Y-%m-%d"),
                                                                                      dateTo=x.issledovaniye.time_confirmation.strftime("%Y-%m-%d"),
                                                                                      note='Результаты в направлении или в протоколе.\nАвтоматический вывод из ЛИС L2')
                        xresult = "<br/><b>{}</b>: {} {}".format(x.fraction.title, x.value, x.fraction.units).strip()
                        xresult = xresult.replace("<sub>", "").replace("</sub>", "").replace("<font>", "").replace("</font>", "")
                        xresult = Utils.escape("<br/>" + xresult + "<br/>")
                        sd = self.baseclient.put_content("Protocol.otg", protocol_template.replace("{{исполнитель}}",
                                                                                              x.issledovaniye.doc_confirmation.get_fio()).replace(
                            "{{результат}}", xresult), self.baseclient.get_addr(
                            "/medservices-ws/service-rs/renderedServiceProtocols/" + ss), type="POST")
                self.baseclient.put_content("Resultat.pdf",
                                            self.baseclient.local_get("/results/pdf",
                                                                      {"pk": json.dumps([direction.pk]),
                                                                       "normis": '1'}),
                                            self.baseclient.get_addr(
                                                "referral-attachments-ws/rs/referralAttachments/" + direction.rmis_number + "/Результат/Resultat.pdf"))
            direction.result_rmis_send = True
            direction.save()
        return direction.result_rmis_send

    def check_and_send_all(self, stdout: OutputWrapper=None):
        upload_after = Settings.get("upload_results_after", default="11.09.2017")
        date = datetime.date(int(upload_after.split(".")[2]), int(upload_after.split(".")[1]),
                             int(upload_after.split(".")[0])) - datetime.timedelta(minutes=20)
        uploaded = []
        for d in Napravleniya.objects.filter(data_sozdaniya__gte=date).filter(
                        Q(rmis_number__isnull=True) | Q(rmis_number="")).distinct():
            uploaded.append(self.check_send(d))
            if stdout:
                stdout.write("Upload direction for direction {}; RMIS number={}".format(d.pk, uploaded[-1]))

        uploaded_results = []

        for d in Napravleniya.objects.filter(data_sozdaniya__gte=date, issledovaniya__time_confirmation__isnull=False,
                                             rmis_number__isnull=False, result_rmis_send=False).exclude(rmis_number="NONERMIS").exclude(rmis_number="").distinct():
            if d.is_all_confirm():
                uploaded_results.append(self.check_send_results(d))
                if stdout:
                    stdout.write("Upload result for direction {}; RMIS number={}".format(d.pk, uploaded_results[-1]))

        return {"directions": [x for x in uploaded if x != ""], "results": [x for x in uploaded_results if x != ""]}


class RenderedServices(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "path_medservices")

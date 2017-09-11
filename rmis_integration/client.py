import datetime
import hashlib
import urllib.parse
from appconf.manager import SettingManager
from requests import Session
from requests.auth import HTTPBasicAuth
from zeep import Client as zeepClient
from zeep.transports import Transport
import clients.models as clients_models
from django.core.cache import cache


class Utils:
    @staticmethod
    def get_column_value(row, column):
        for col in row["column"]:
            if col["name"] == column:
                return col["data"]

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


class Settings:
    @staticmethod
    def get(key):
        return SettingManager.get("rmis_" + key)


def get_md5(s):
    m = hashlib.md5()
    m.update(s.encode())
    return m.hexdigest()


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

    def get_client(self, address_key: str) -> zeepClient:
        address = Settings.get(address_key)
        if address not in self.clients:
            self.clients[address] = zeepClient(urllib.parse.urljoin(self.base_address, address),
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
        return "NONB_RMIS"

    def create_rmis_card(self, individual: clients_models.Individual, get_id: str):
        base = clients_models.CardBase.objects.filter(is_rmis=True, hide=False).first()
        if not clients_models.Card.objects.filter(base=base, number=get_id, is_archive=False).exists():
            clients_models.Card.objects.filter(base=base, individual=individual).update(is_archive=True)
            c = clients_models.Card(base=base, number=get_id, individual=individual, is_archive=False).save()
            return c
        return None

    def get_rmis_id_for_individual(self, individual: clients_models.Individual, update_rmis=False):
        return_none = "NONB_RMIS"
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
        super().__init__(client, "rmis_path_services")
        self.services = {}
        srv = self.client.getServices(clinic=client.search_organization_id())
        for r in srv:
            self.services[r["code"]] = r["id"]

    def get_service_id(self, s):
        if s in self.services:
            return self.services[s]
        return None


class Directions(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "rmis_path_directions")


class RenderedServices(BaseRequester):
    def __init__(self, client: Client):
        super().__init__(client, "rmis_path_medservices")
import ftplib
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from urllib.parse import urlparse
import time

from django.db import transaction
from hl7apy import VALIDATION_LEVEL, core
from hl7apy.parser import parse_message

from clients.models import Individual
from directions.models import Napravleniya, RegisteredOrders
from hospitals.models import Hospitals
from directory.models import Researches
from users.models import DoctorProfile


class ServiceNotFoundException(Exception):
    pass


class FailedCreatingDirectionsException(Exception):
    pass


class FTPConnection:
    def __init__(self, url, hospital: Hospitals):
        parsed_url = urlparse(url)
        self.hospital = hospital
        self.url = url
        self.hostname = parsed_url.hostname
        self.username = parsed_url.username
        self.password = parsed_url.password
        self.directory = parsed_url.path

        self.ftp = None
        self.connected = False
        self.encoding = 'utf-8'

    @property
    def name(self):
        return self.hospital.safe_short_title

    def log(self, *msg, color=None, level='INFO '):
        message = ""
        if color:
            message = f"\033[{color}m{message}"

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        message += f"[{level}] {current_time}: {self.name} {self.url} {' '.join([str(x) for x in (msg if isinstance(msg, Iterable) else [msg])])}"

        if color:
            message += "\033[0m"

        print(message)

    def error(self, *msg):
        self.log(*msg, color='91', level='ERROR')

    def connect(self, forced=False, encoding='utf-8'):
        if forced:
            self.disconnect()
        if not self.connected:
            self.ftp = ftplib.FTP(self.hostname, encoding=encoding)
            self.ftp.login(self.username, self.password)
            self.ftp.cwd(self.directory)
            self.connected = True
            self.encoding = encoding
            self.log("Connected with encoding", self.encoding)

    def disconnect(self):
        if self.connected:
            try:
                self.ftp.quit()
            except ftplib.all_errors:
                pass
            finally:
                self.ftp = None
                self.connected = False

    def get_file_list(self, is_retry=False):
        try:
            file_list = self.ftp.nlst()
        except ftplib.error_perm as resp:
            if str(resp).startswith('550'):
                file_list = []
            else:
                raise resp
        except UnicodeDecodeError as e:
            self.error(f"UnicodeDecodeError: {e}")
            if not is_retry:
                self.log(f"Retrying connection with encoding cp1251")
                self.connect(forced=True, encoding='cp1251')
                return self.get_file_list(is_retry=True)
            else:
                raise e
        return file_list

    def delete_file(self, file):
        try:
            self.ftp.delete(file)
            self.log(f"Deleted file {file}")
        except Exception as e:
            self.error(f"Error deleting file {file}: {e}")

    def read_file_as_text(self, file):
        self.log(f"Reading file {file}")
        with tempfile.NamedTemporaryFile() as f:
            self.connect()
            self.ftp.retrbinary(f"RETR {file}", f.write)
            f.seek(0)
            content = f.read()
            try:
                return content.decode('utf-8-sig')
            except UnicodeDecodeError as e:
                self.error(f"UnicodeDecodeError: {e}")
                self.log('Trying again with encoding cp1251')
                return content.decode('cp1251')

    def read_file_as_hl7(self, file):
        content = self.read_file_as_text(file)
        self.log(f"{file}\n{content}")
        hl7_result = parse_message(content.replace("\n", "\r"), validation_level=VALIDATION_LEVEL.QUIET)

        return hl7_result

    def pull_order(self, file: str):
        if not file.endswith('.ord'):
            self.error(f"Skipping file {file} because it does not end with '.ord'")
            return
        if RegisteredOrders.objects.filter(file_name=file).exists():
            self.error(f"Skipping file {file} because it already exists")
            return

        hl7_result = self.read_file_as_hl7(file)
        self.log(f"HL7 parsed")
        patient = hl7_result.ORM_O01_PATIENT[0]
        pid = patient.PID[0]
        orders = hl7_result.ORM_O01_ORDER[0].children[0]

        fio = pid.PID_5
        family = fio.PID_5_1.value
        name = fio.PID_5_2.value
        patronymic = fio.PID_5_3.value if hasattr(fio, 'PID_5_3') else ''

        birthday = pid.PID_7.value
        if len(birthday) == 8:
            birthday = f"{birthday[:4]}-{birthday[4:6]}-{birthday[6:]}"

        sex = {'m': 'м', 'f': 'ж'}.get(pid.PID_8.value.lower(), 'ж')

        orders_by_numbers = defaultdict(list)

        for order in orders.children:
            obr = order.children[0]
            orders_by_numbers[obr.OBR_3.value].append(obr.OBR_4.OBR_4_4.value)

        orders_by_numbers = dict(orders_by_numbers)

        self.log(family, name, patronymic, birthday, sex)
        self.log(orders_by_numbers)

        try:
            card = Individual.import_from_simple_data(
                {
                    "family": family,
                    "name": name,
                    "patronymic": patronymic,
                    "sex": sex,
                    "birthday": birthday,
                },
                self.hospital,
            )
            self.log("Card", card)
            with transaction.atomic():
                services_by_order_number = {}
                for order_number, services_codes in orders_by_numbers.items():
                    for service_code in services_codes:
                        service = Researches.objects.filter(hide=False, internal_code=service_code).first()
                        if not service:
                            raise ServiceNotFoundException(f"Service {service_code} not found")
                        if order_number not in services_by_order_number:
                            services_by_order_number[order_number] = []
                        services_by_order_number[order_number].append(service.pk)

                for order_number, services in services_by_order_number.items():
                    external_order = RegisteredOrders.objects.create(
                        order_number=order_number,
                        organization=self.hospital,
                        services=orders_by_numbers[order_number],
                        patient_card=card,
                        file_name=file,
                    )
                    result = Napravleniya.gen_napravleniya_by_issledovaniya(
                        card.pk,
                        "",
                        None,
                        "",
                        None,
                        DoctorProfile.get_system_profile(),
                        {-1: services},
                        {},
                        False,
                        {},
                        vich_code="",
                        count=1,
                        discount=0,
                        rmis_slot=None,
                        external_order=external_order,
                        hospital_override=self.hospital.pk,
                    )

                    if not result['r']:
                        raise FailedCreatingDirectionsException(result.get('message') or "Failed creating directions")

                    self.log("Created local directions:", result['list_id'])

                    for direction in Napravleniya.objects.filter(pk__in=result['list_id'], need_order_redirection=True):
                        self.log("Direction", direction.pk, "marked as redirection to", direction.external_executor_hospital)

            self.delete_file(file)
        except Exception as e:
            self.error(f"Exception: {e}")

    def push_order(self, direction: Napravleniya):
        hl7 = core.Message("ORM_O01")
        hl7.msh.msh_3 = "L2"
        hl7.msh.msh_4 = "ORDER"
        hl7.msh.msh_5 = "qLIS"
        hl7.msh.msh_6 = "LukaLab"
        hl7.msh.msh_9 = "ORM^O01"
        hl7.msh.msh_10 = "1"
        hl7.msh.msh_11 = "P"

        individual = direction.client.individual
        hl7.add_group("ORM_O01_PATIENT")
        hl7.ORM_O01_PATIENT.pid.pid_2 = str(direction.client.pk)
        hl7.ORM_O01_PATIENT.pid.pid_5 = f"{individual.family}^{individual.name}^{individual.patronymic}"
        hl7.ORM_O01_PATIENT.pid.pid_7 = individual.birthday.strftime("%Y%m%d")
        hl7.ORM_O01_PATIENT.pid.pid_8 = individual.sex.upper()

        self.log(hl7.to_mllp().replace("\r", "\r\n"))


MAX_LOOP_TIME = 600


def get_hospitals_pull_orders():
    hospitals = Hospitals.objects.filter(orders_pull_by_numbers__isnull=False, hide=False)
    return hospitals


def process_pull_orders():
    processed_files_by_url = defaultdict(set)

    hospitals = get_hospitals_pull_orders()

    print('Getting ftp links')
    ftp_links = {x.orders_pull_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        print(f'Iterating over {len(ftp_links)} servers')
        for ftp_url, ftp_connection in ftp_connections.items():
            processed_files_new = set()
            try:
                ftp_connection.connect()
                file_list = ftp_connection.get_file_list()

                for file in file_list:
                    processed_files_new.add(file)

                    if file not in processed_files_by_url[ftp_url]:
                        ftp_connection.pull_order(file)

            except ftplib.all_errors as e:
                processed_files_new.update(processed_files_by_url[ftp_url])
                ftp_connection.error(f"error: {e}")
                ftp_connection.log("Disconnecting...")
                ftp_connection.disconnect()

            processed_files_by_url[ftp_url] = processed_files_new

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_pull_start_orders():
    print('Starting pull_orders process')
    while True:
        process_pull_orders()
        time.sleep(1)


def get_hospitals_push_orders():
    hospitals = Hospitals.objects.filter(orders_push_by_numbers__isnull=False, is_external_performing_organization=True, hide=False)
    return hospitals


def process_push_orders():
    hospitals = get_hospitals_push_orders()

    print('Getting ftp links')
    ftp_links = {x.orders_push_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        print(f'Iterating over {len(ftp_links)} servers')
        for ftp_url, ftp_connection in ftp_connections.items():
            directions_to_sync = []

            for direction in Napravleniya.objects.filter(external_executor_hospital=ftp_connection.hospital, need_order_redirection=True)[:10]:
                directions_to_sync.append(direction)

            ftp_connection.log(f"Directions to sync: {[d.pk for d in directions_to_sync]}")

            if directions_to_sync:
                try:
                    ftp_connection.connect()
                    for direction in directions_to_sync:
                        ftp_connection.push_order(direction)

                except ftplib.all_errors as e:
                    ftp_connection.error(f"error: {e}")
                    ftp_connection.log("Disconnecting...")
                    ftp_connection.disconnect()

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_push_orders_start():
    print('Starting push_orders process')
    while True:
        process_push_orders()
        time.sleep(1)

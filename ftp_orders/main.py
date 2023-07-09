import ftplib
import tempfile
from collections import defaultdict
from urllib.parse import urlparse
import time

from hl7apy import VALIDATION_LEVEL
from hl7apy.parser import parse_message

from hospitals.models import Hospitals


class FTPConnection:
    def __init__(self, url, name):
        parsed_url = urlparse(url)
        self.name = name
        self.url = url
        self.hostname = parsed_url.hostname
        self.username = parsed_url.username
        self.password = parsed_url.password
        self.directory = parsed_url.path

        self.ftp = None
        self.connected = False

    def log(self, *msg):
        print(f"{self.name} {self.url}", *msg)

    def connect(self):
        if not self.connected:
            self.ftp = ftplib.FTP(self.hostname)
            self.ftp.login(self.username, self.password)
            self.ftp.cwd(self.directory)
            self.connected = True
            self.log("Connected")

    def disconnect(self):
        if self.connected:
            try:
                self.ftp.quit()
            except ftplib.all_errors:
                pass
            finally:
                self.ftp = None
                self.connected = False

    def get_file_list(self):
        try:
            file_list = self.ftp.nlst()
        except ftplib.error_perm as resp:
            if str(resp).startswith('550'):
                file_list = []
            else:
                raise
        return file_list

    def read_file_as_text(self, file):
        self.log(f"Reading file {file}")
        with tempfile.NamedTemporaryFile() as f:
            self.connect()
            self.ftp.retrbinary(f"RETR {file}", f.write)
            f.seek(0)
            content = f.read()
            return content.decode('utf-8-sig')

    def read_file_as_hl7(self, file):
        content = self.read_file_as_text(file)
        self.log(f"{file}\n{content}")
        hl7_result = parse_message(content.replace("\n", "\r"), validation_level=VALIDATION_LEVEL.QUIET)

        return hl7_result

    def perform_file(self, file):
        hl7_result = self.read_file_as_hl7(file)
        self.log(f"HL7 parsed")
        patient = hl7_result.ORM_O01_PATIENT[0]
        pid = patient.PID[0]
        piv = patient.PV1
        orders = hl7_result.ORM_O01_ORDER[0].children[0]

        fio = pid.PID_5
        family = fio.PID_5_1.value
        name = fio.PID_5_2.value
        patronymic = fio.PID_5_3.value if hasattr(fio, 'PID_5_3') else ''

        birthday = pid.PID_7.value
        if len(birthday) == 8:
            birthday = f"{birthday[:4]}-{birthday[4:6]}-{birthday[6:]}"

        sex = {'m': 'м', 'f': 'ж'}.get(pid.PID_8.value.lower(), 'ж')

        orders_by_tubes = defaultdict(list)

        for order in orders.children:
            obr = order.children[0]
            orders_by_tubes[obr.OBR_3.value].append(obr.OBR_4.OBR_4_4.value)

        orders_by_tubes = dict(orders_by_tubes)

        self.log(family, name, patronymic, birthday, sex)
        self.log(orders_by_tubes)
        return hl7_result


def get_hospitals():
    hospitals = Hospitals.objects.filter(orders_ftp_server_url__isnull=False, hide=False)
    return hospitals


def process():
    processed_files_by_url = defaultdict(set)

    hospitals = get_hospitals()

    print('Getting ftp links')
    ftp_links = {x.orders_ftp_server_url: x.safe_short_title for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, name=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < 600:
        print(f'Iterating over {len(ftp_links)} servers')
        for ftp_url, ftp_connection in ftp_connections.items():
            processed_files_new = set()
            try:
                ftp_connection.connect()
                file_list = ftp_connection.get_file_list()

                for file in file_list:
                    processed_files_new.add(file)

                    if file not in processed_files_by_url[ftp_url]:
                        ftp_connection.perform_file(file)

            except ftplib.all_errors as e:
                processed_files_new.update(processed_files_by_url[ftp_url])
                ftp_connection.log(f"error: {e}")
                ftp_connection.log("Disconnecting...")
                ftp_connection.disconnect()

            processed_files_by_url[ftp_url] = processed_files_new

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_ftp_links():
    print('Starting process')
    while True:
        process()
        time.sleep(1)

import base64
import datetime
import ftplib
import json
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from io import BytesIO
from sys import stdout
from urllib.parse import urlparse
import time

from django.db import transaction
from hl7apy import VALIDATION_LEVEL, core
from hl7apy.parser import parse_message

from appconf.manager import SettingManager
from clients.models import Individual, CardBase
from contracts.models import PriceName
from directions.models import Napravleniya, RegisteredOrders, NumberGenerator, TubesRegistration, IstochnikiFinansirovaniya, NapravleniyaHL7LinkFiles, Issledovaniya, Result
from ftp_orders.sql_func import get_tubesregistration_id_by_iss
from hospitals.models import Hospitals
from directory.models import Researches, Fractions
from laboratory.settings import BASE_DIR, NEED_RECIEVE_TUBE_TO_PUSH_ORDER, FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES, OWN_SETUP_TO_SEND_FTP_EXECUTOR
from laboratory.utils import current_time
from slog.models import Log
from users.models import DoctorProfile
from hl7apy.core import Message, Segment, Group
from ftplib import FTP


class ServiceNotFoundException(Exception):
    pass


class InvalidOrderNumberException(Exception):
    pass


class FailedCreatingDirectionsException(Exception):
    pass


class NoValidNumberGeneratorException(Exception):
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
        self.encoding = "utf-8"

    @property
    def name(self):
        return self.hospital.safe_short_title

    def log(self, *msg, color=None, level="INFO "):
        message = ""
        if color:
            message = f"\033[{color}m{message}"

        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        message += f"[{level}] {current_time}: {self.name} {self.url} {' '.join([str(x) for x in (msg if isinstance(msg, Iterable) else [msg])])}"

        if color:
            message += "\033[0m"

        stdout.write(message)

    def error(self, *msg):
        self.log(*msg, color="91", level="ERROR")

    def connect(self, forced=False, encoding="utf-8"):
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
            if str(resp).startswith("550"):
                file_list = []
            else:
                raise resp
        except UnicodeDecodeError as e:
            self.error(f"UnicodeDecodeError: {e}")
            if not is_retry:
                self.log("Retrying connection with encoding cp1251")
                self.connect(forced=True, encoding="cp1251")
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

    def copy_file(self, file_name: str, path: str):
        with tempfile.NamedTemporaryFile() as file:
            self.ftp.retrbinary(f"RETR {file_name}", file.write)
            file.seek(0)
            self.ftp.storbinary(f"STOR {path}{file_name}", file)
            self.log(f"File {file_name} copied")

    def read_file_as_text(self, file):
        self.log(f"Reading file {file}")
        with tempfile.NamedTemporaryFile() as f:
            self.connect()
            self.ftp.retrbinary(f"RETR {file}", f.write)
            f.seek(0)
            content = f.read()
            try:
                return content.decode("utf-8-sig")
            except UnicodeDecodeError as e:
                self.error(f"UnicodeDecodeError: {e}")
                self.log("Trying again with encoding cp1251")
                return content.decode("cp1251")

    def write_file_as_text(self, file, content):
        self.log(f"Writing file {file}")
        self.connect()
        self.ftp.storbinary(f"STOR {file}", BytesIO(content.encode("utf-8")))
        self.log(f"Wrote file {file}")

    def read_file_as_hl7(self, file):
        content = self.read_file_as_text(file).strip("\x0b").strip("\x0c")
        self.log(f"{file}\n{content}")
        content = content.replace("\n", "\r")
        try:
            hl7_result = parse_message(content, validation_level=VALIDATION_LEVEL.QUIET)

            return hl7_result, content
        except Exception as e:
            self.error(f"Error parsing file {file}: {e}")
            return None, None

    def pull_order(self, file: str):
        if not file.endswith(".ord"):
            self.error(f"Skipping file {file} because it does not end with '.ord'")
            return
        if RegisteredOrders.objects.filter(file_name=file).exists():
            self.error(f"Skipping file {file} because it already exists")
            return
        hl7_result, hl7_content = self.read_file_as_hl7(file)

        if not hl7_content or not hl7_result:
            self.error(f"Skipping file {file} because it could not be parsed")
            return

        self.log(f"HL7 parsed")
        patient = hl7_result.ORM_O01_PATIENT[0]
        pid = patient.PID[0]

        pv1 = hl7_result.ORM_O01_PATIENT.ORM_O01_PATIENT_VISIT.PV1.PV1_20.value.split("^")
        if len(pv1) > 1:
            price_symbol_code = pv1[-1]
        else:
            price_symbol_code = pv1[0]
        base = CardBase.objects.filter(internal_type=True).first()
        if pv1[0].lower() in ["наличные", "платно", "средства граждан"]:
            finsource = IstochnikiFinansirovaniya.objects.filter(base=base, title="Платно", hide=False).first()
        else:
            finsource = IstochnikiFinansirovaniya.objects.filter(base=base, title__in=["Договор"], hide=False).first()

        price_name = PriceName.objects.filter(symbol_code=price_symbol_code).first()

        orders = hl7_result.ORM_O01_ORDER[0].children[0]
        patient_id_company = pid.PID_2.value

        fio = pid.PID_5
        family = fio.PID_5_1.value
        name = fio.PID_5_2.value
        patronymic = fio.PID_5_3.value if hasattr(fio, "PID_5_3") else ""

        birthday = pid.PID_7.value
        if len(birthday) == 8:
            birthday = f"{birthday[:4]}-{birthday[4:6]}-{birthday[6:]}"

        sex = {"m": "м", "f": "ж"}.get(pid.PID_8.value.lower(), "ж")

        snils = pid.PID_19.value
        snils = snils.replace("-", "").replace(" ", "")
        enp = ""
        if len(pid.PID_18.value) > 1:
            document_data = pid.PID_18.value.split("^")
            if document_data[2] == "Полис":
                enp = document_data[4]
        adds_data = pid.to_er7().split("|")[13].split("~")

        phone = adds_data[0] if adds_data[0] else ""
        email_base64_str = adds_data[3] if adds_data[3] else ""
        if email_base64_str:
            email_byte = email_base64_str.encode("utf-8")
            email_base64 = base64.b64decode(email_byte)
            email = email_base64.decode("utf-8")
        else:
            email = ""

        orders_by_numbers = defaultdict(list)
        additional_order_number_by_service = defaultdict(list)

        for order in orders.children:
            obr = order.children[0]
            orders_by_numbers[obr.OBR_3.value].append(obr.OBR_4.OBR_4_4.value)
            additional_order_number_by_service[obr.OBR_4.OBR_4_4.value] = obr.OBR_2.OBR_2_1.value
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
                    "snils": snils,
                    "enp": enp,
                },
                self.hospital,
                patient_id_company,
                email,
                phone,
            )
            self.log("Card", card)

            directions = {}
            order_numbers = []

            with transaction.atomic():
                doc = DoctorProfile.get_system_profile()
                services_by_order_number = {}
                services_by_additional_order_num = {}
                for order_number, services_codes in orders_by_numbers.items():
                    for service_code in services_codes:
                        service = Researches.objects.filter(hide=False, internal_code=service_code).first()
                        if not service:
                            raise ServiceNotFoundException(f"Service {service_code} not found")
                        if order_number not in services_by_order_number:
                            services_by_order_number[order_number] = []
                        services_by_order_number[order_number].append(service.pk)
                        services_by_additional_order_num[service.pk] = additional_order_number_by_service.get(service_code, "")

                for order_number_str, services in services_by_order_number.items():
                    order_numbers.append(order_number_str)

                    if not order_number_str.isdigit():
                        raise InvalidOrderNumberException(f"Number {order_number} is not digit")
                    order_number = int(order_number_str)
                    if order_number <= 0:
                        raise InvalidOrderNumberException(f"Number {order_number} need to be greater than 0")
                    if not NumberGenerator.check_value_for_organization(self.hospital, order_number):
                        raise InvalidOrderNumberException(f"Number {order_number} not valid. May be NumberGenerator is over or order number exists")

                    external_order = RegisteredOrders.objects.create(
                        order_number=order_number,
                        organization=self.hospital,
                        services=orders_by_numbers[order_number_str],
                        patient_card=card,
                        file_name=file,
                    )
                    result = Napravleniya.gen_napravleniya_by_issledovaniya(
                        card.pk,
                        "",
                        finsource.pk,
                        "",
                        None,
                        doc,
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
                        services_by_additional_order_num=services_by_additional_order_num,
                        price_name=price_name.pk,
                    )

                    if not result["r"]:
                        raise FailedCreatingDirectionsException(result.get("message") or "Failed creating directions")

                    self.log("Created local directions:", result["list_id"])
                    for direction in result["list_id"]:
                        directions[direction] = orders_by_numbers[order_number_str]

                    for direction in Napravleniya.objects.filter(pk__in=result["list_id"], need_order_redirection=True):
                        self.log("Direction", direction.pk, "marked as redirection to", direction.external_executor_hospital)
                        with tempfile.NamedTemporaryFile() as f:
                            self.connect()
                            self.ftp.retrbinary(f"RETR {file}", f.write)
                            f.seek(0)
                            path_file = NapravleniyaHL7LinkFiles.create_hl7_file_path(direction.pk, file)
                            with open(path_file, "wb") as fnew:
                                fnew.write(f.read())
                        NapravleniyaHL7LinkFiles.objects.create(
                            napravleniye_id=direction.pk,
                            upload_file=path_file,
                            file_type="HL7_ORIG_ORDER",
                        )

            self.delete_file(file)

            Log.log(
                json.dumps(order_numbers),
                190000,
                None,
                {
                    "org": self.hospital.safe_short_title,
                    "content": hl7_content,
                    "directions": directions,
                    "card": card.number_with_type(),
                },
            )
        except Exception as e:
            self.error(f"Exception: {e}")

    def pull_result(self, file: str):
        if not file.endswith(".res"):
            self.error(f"Skipping file {file} because it does not end with '.res'")
            return

        hl7_result, hl7_content = self.read_file_as_hl7(file)

        if not hl7_content or not hl7_result:
            self.error(f"Skipping file {file} because it could not be parsed")
            return

        self.log("HL7 parsed")
        obr = hl7_result.ORU_R01_RESPONSE.ORU_R01_ORDER_OBSERVATION.OBR
        external_add_order, iss_id = None, None
        is_confirm = False
        if "L2" not in obr.OBR_2.OBR_2_1.value:
            external_add_order = obr.OBR_2.OBR_2_1.value
        else:
            iss_id = (obr.OBR_2.OBR_2_1.value).split("_")[1]
        doctor_family_confirm = obr.OBR_32.OBR_32_2.value
        doctor_name_confirm = obr.OBR_32.OBR_32_3.value
        doctor_patronymic_confirm = obr.OBR_32.OBR_32_4.value
        doctor_fio = f"{doctor_family_confirm} {doctor_name_confirm} {doctor_patronymic_confirm}"
        date_time_confirm = obr.OBR_8.value
        if obr.OBR_25.value == "F":
            is_confirm = True
        elif obr.OBR_25.value == "D":
            is_confirm = False

        obxes = hl7_result.ORU_R01_RESPONSE.ORU_R01_ORDER_OBSERVATION.ORU_R01_OBSERVATION
        fractions = {"fsli": "", "title_fraction": "", "value": "", "refs": "", "units": "", "jpeg": "", "html": "", "doc_confirm": "", "date_confirm": "", "note_data": ""}
        result = []
        for obx in obxes:
            tmp_fractions = fractions.copy()
            if (obx.OBX.obx_3.obx_3_1.value).lower == "pdf":
                continue
            elif (obx.OBX.obx_3.obx_3_1.value).lower() == "jpg":
                tmp_fractions["jpg"] = obx.OBX.obx_5.obx_5_5.value
                result.append(tmp_fractions.copy())
                continue
            elif (obx.OBX.obx_3.obx_3_1.value).lower() == "image":
                tmp_fractions["html"] = obx.OBX.obx_5.obx_5_1.value
                result.append(tmp_fractions.copy())
                continue
            tmp_fractions["fsli"] = obx.OBX.obx_3.obx_3_1.value
            tmp_fractions["title_fraction"] = obx.OBX.obx_3.obx_3_2.value
            tmp_fractions["value"] = obx.OBX.obx_5.obx_5_1.value
            tmp_fractions["units"] = obx.OBX.obx_6.obx_6_1.value
            tmp_fractions["refs"] = obx.OBX.obx_7.obx_7_1.value
            result.append(tmp_fractions.copy())

        if external_add_order:
            iss = Issledovaniya.objects.filter(external_add_order__external_add_order=external_add_order).first()
        else:
            iss = Issledovaniya.objects.filter(id=iss_id).first()

        if is_confirm:
            iss.lab_comment = ""
            iss.time_confirmation = datetime.datetime.strptime(date_time_confirm, "%Y%m%d%H%M%S")
            iss.time_save = current_time()
            iss.doc_confirmation_string = doctor_fio
            iss.save()

            for res in result:
                fraction = Fractions.objects.filter(fsli=res["fsli"]).first()
                if not fraction:
                    continue
                value = res["value"]
                units = res["units"]
                ref_str = res["refs"]
                if ref_str:
                    ref_str = ref_str.replace('"', "'")
                    ref_str = f'{{"Все": "{ref_str}"}}'
                Result(
                    issledovaniye=iss,
                    fraction=fraction,
                    value=value,
                    units=units,
                    ref_f=ref_str,
                    ref_m=ref_str,
                ).save()
        else:
            iss.lab_comment = ("",)
            iss.time_confirmation = (None,)
            iss.time_save = current_time()
            iss.doc_confirmation_string = ""
            iss.save()

    def push_order(self, direction: Napravleniya):
        hl7 = core.Message("ORM_O01", validation_level=VALIDATION_LEVEL.QUIET)

        hl7.msh.msh_3 = direction.hospital.hl7_sender_application if direction.hospital.hl7_sender_application else "L2"
        hl7.msh.msh_4 = direction.hospital.hl7_sender_org if direction.hospital.hl7_sender_org else "ORDER"
        hl7.msh.msh_5 = "qLIS"
        hl7.msh.msh_6 = "LukaLab"
        hl7.msh.msh_9 = "ORM^O01"
        hl7.msh.msh_10 = "1"
        hl7.msh.msh_11 = "P"

        individual = direction.client.individual
        data_indivdual = direction.client.get_data_individual()
        patient = hl7.add_group("ORM_O01_PATIENT")
        patient.pid.pid_2 = str(direction.client.pk)
        patient.pid.pid_5 = f"{individual.family}^{individual.name}^{individual.patronymic}"
        patient.pid.pid_7 = individual.birthday.strftime("%Y%m%d")
        if individual.sex.upper() == "Ж":
            sex = "F"
        else:
            sex = "M"
        patient.pid.pid_8 = sex
        byte_email = direction.client.email.encode("utf-8")
        field_13 = f"{direction.client.phone.replace(' ', '').replace('-', '')}@@@{base64.b64encode(byte_email).decode('UTF-8')}"
        patient.pid.pid_13.value = field_13
        patient.pid.pid_18 = f"^^Полис^^{data_indivdual['enp']}"
        patient.pid.pid_19 = data_indivdual["snils"]

        pv = hl7.add_group("ORM_O01_PATIENT_VISIT")
        pv.PV1.PV1_2.value = "O"

        l2_price_code = SettingManager.get("l2_price_code", default='ТЛ0000001', default_type='s')
        if OWN_SETUP_TO_SEND_FTP_EXECUTOR:
            prices = PriceName.get_hospital_extrenal_price_by_date(direction.external_executor_hospital, direction.data_sozdaniya, direction.data_sozdaniya)
            for price in prices:
                if l2_price_code:
                    price_code_value = l2_price_code
                else:
                    price_code_value = price.symbol_code
                if direction.istochnik_f.title.lower() == "омс" and "омс" in price.title.lower():
                    pv.PV1.PV1_20.value = f"Договор^^{price.contract_number}^{price_code_value}"
                    pv.PV1.PV1_7.value = f"{price_code_value}"
                if direction.istochnik_f.title.lower() == "договор" and "договор" in price.title.lower():
                    pv.PV1.PV1_20.value = f"Договор^^{price.contract_number}^{price_code_value}"
                    pv.PV1.PV1_7.value = f"{price_code_value}"
        else:
            if direction.istochnik_f.title.lower() == "договор":
                if l2_price_code:
                    price_code_value = l2_price_code
                else:
                    price_code_value = direction.price_name.symbol_code
                pv.PV1.PV1_20.value = f"Договор^^{direction.price_name.title}^{price_code_value}"
                pv.PV1.PV1_7.value = f"{price_code_value}"
            else:
                pv.PV1.PV1_20.value = "Наличные"
        pv.PV1.PV1_44.value = direction.data_sozdaniya.strftime("%Y%m%d")
        pv.PV1.PV1_46.value = ""

        created_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        hl7.ORM_O01_ORDER.orc.orc_1 = "1"

        ordd = hl7.ORM_O01_ORDER.add_group("ORM_O01_ORDER_DETAIL")

        with transaction.atomic():
            direction.need_order_redirection = False
            direction.time_send_hl7 = current_time()
            direction.save(update_fields=["time_send_hl7", "need_order_redirection"])
            n = 0
            for iss in direction.issledovaniya_set.all():
                n += 1
                obr = ordd.add_segment("OBR")
                obr.obr_1 = str(n)
                obr.obr_2 = f"L2_{iss.pk}^{direction.hospital.hl7_sender_application}"
                tube_data = [i.tube_number for i in get_tubesregistration_id_by_iss(iss.pk)]
                obr.obr_3.value = str(tube_data[0])
                obr.obr_4.obr_4_4.value = iss.research.internal_code
                obr.obr_4.obr_4_5.value = iss.research.title.replace(" ", "_")
                obr.obr_7.value = created_at
                obr.obr_27.value = "^^^^^"
                obr.obr_34.value = ""

            content = hl7.value.replace("\r", "\n").replace("ORC|1\n", "")
            content = content.replace("@", "~")
            filename = f"form1c_orm_{direction.pk}_{created_at}.ord"

            self.log("Writing file", filename, "\n", content)
            self.write_file_as_text(filename, content)

            Log.log(
                direction.pk,
                190001,
                None,
                {
                    "org": self.hospital.safe_short_title,
                    "content": content,
                },
            )

    def push_tranfer_file_order(self, direction: Napravleniya, registered_orders_ids, directions_to_sync):
        created_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        directons_external_order_group = Napravleniya.objects.filter(external_order_id__in=registered_orders_ids)
        with transaction.atomic():
            for i in directons_external_order_group:
                i.need_order_redirection = False
                i.time_send_hl7 = current_time()
                i.save(update_fields=["time_send_hl7", "need_order_redirection", "need_order_redirection"])
            hl7_file = NapravleniyaHL7LinkFiles.objects.filter(napravleniye=direction).first()

            hl7_rule_file = os.path.join(BASE_DIR, "ftp_orders", "hl7_rule", direction.hospital.hl7_rule_file)
            if hl7_rule_file:
                with open(hl7_rule_file) as json_file:
                    data = json.load(json_file)
                    data = data["order"]
                    need_replace_field = data["needReplaceField"]
                mod_lines = []
                with open(f"{hl7_file.upload_file.name}", "r") as fp:
                    for n, line in enumerate(fp, 1):
                        line = line.rstrip("\n")
                        line_new = line.split("|")
                        if line_new[0] in need_replace_field.keys():
                            field_replace = need_replace_field[line_new[0]]
                            line_new = check_replace_fields(field_replace, line_new, direction)
                        mod_lines.append("|".join(line_new))
            path_file = NapravleniyaHL7LinkFiles.create_hl7_file_path(direction.pk, f"{hl7_file.upload_file.name}_mod")

            with open(path_file, "w") as file:
                for line in mod_lines:
                    file.write(line + "\n")
            file.close()
            with open(path_file, "r") as file:
                content = file.read()

            self.log("Writing file", path_file, "\n", content)
            filename = f"form1c_orm_{direction.pk}_{created_at}.ord"
            self.write_file_as_text(filename, content)
            for k in directons_external_order_group:
                if k in directions_to_sync:
                    directions_to_sync.remove(k)

            Log.log(
                direction.pk,
                190001,
                None,
                {
                    "org": self.hospital.safe_short_title,
                    "content": content,
                },
            )


MAX_LOOP_TIME = 600


def check_replace_fields(field_replace, line_new, direction):
    for fr in field_replace:
        if fr == "2" and line_new[0] == "MSH":
            line_new[int(fr)] = direction.external_executor_hospital.hl7_sender_application
        elif fr == "3" and line_new[0] == "MSH":
            line_new[int(fr)] = direction.external_executor_hospital.short_title
        elif fr == "2-2" and line_new[0] == "OBR":
            positions = fr.split("-")
            data = line_new[int(positions[0])]
            data_pos = data.split("^")
            data_pos[int(positions[1]) - 1] = direction.external_executor_hospital.hl7_sender_application
            data = "^".join(data_pos)
            line_new[int(positions[0])] = data
    return line_new


def get_hospitals_pull_orders():
    hospitals = Hospitals.objects.filter(orders_pull_by_numbers__isnull=False, hide=False)
    return hospitals


def process_pull_orders():
    processed_files_by_url = defaultdict(set)

    hospitals = get_hospitals_pull_orders()
    stdout.write("Getting ftp links")
    ftp_links = {x.orders_pull_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        stdout.write(f"Iterating over {len(ftp_links)} servers")
        for ftp_url, ftp_connection in ftp_connections.items():
            processed_files_new = set()
            path_to_copy = None
            path_to_push = ftp_connection.hospital.orders_push_by_numbers
            if len(path_to_push) > 0:
                path_to_copy = urlparse(path_to_push).path
            try:
                ftp_connection.connect()
                file_list = ftp_connection.get_file_list()

                for file in file_list:
                    processed_files_new.add(file)

                    if file not in processed_files_by_url[ftp_url]:
                        if path_to_copy:
                            ftp_connection.copy_file(file, path_to_copy)
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
    stdout.write("Starting pull_orders process")
    while True:
        process_pull_orders()
        time.sleep(1)


def get_hospitals_push_orders():
    hospitals = Hospitals.objects.filter(orders_push_by_numbers__isnull=False, is_external_performing_organization=True, hide=False)
    return hospitals


def process_push_orders():
    hospitals = get_hospitals_push_orders()

    stdout.write("Getting ftp links")
    ftp_links = {x.orders_push_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        stdout.write(f"Iterating over {len(ftp_links)} servers")
        for ftp_url, ftp_connection in ftp_connections.items():
            directions_to_sync = []
            directions = []
            directions_external_executor = []
            if ftp_connection.hospital.is_auto_transfer_hl7_file:
                directions = Napravleniya.objects.filter(hospital=ftp_connection.hospital, need_order_redirection=True)[:50]
            else:
                directions_external_executor = Napravleniya.objects.filter(external_executor_hospital=ftp_connection.hospital, need_order_redirection=True)[:50]
            for dir_external in directions_external_executor:
                if dir_external not in directions:
                    tube_data = []
                    for iss in dir_external.issledovaniya_set.all():
                        tube_data = [i.tube_number for i in get_tubesregistration_id_by_iss(iss.pk)]
                    if len(tube_data) > 0:
                        directions.append(dir_external)

            if NEED_RECIEVE_TUBE_TO_PUSH_ORDER:
                for direction in directions:
                    is_recieve = False
                    for tube in TubesRegistration.objects.filter(issledovaniya__napravleniye=direction).distinct():
                        is_recieve = True
                        if tube.time_recive is None:
                            is_recieve = False
                    if is_recieve:
                        directions_to_sync.append(direction)
            else:
                directions_to_sync.extend(directions)

            ftp_connection.log(f"Directions to sync: {[d.pk for d in directions_to_sync]}")

            if directions_to_sync:
                try:
                    ftp_connection.connect()
                    for direction in directions_to_sync:
                        if direction.external_order and direction.need_order_redirection:
                            registered_orders_ids = direction.external_order.get_registered_orders_by_file_name()
                            ftp_connection.push_tranfer_file_order(direction, registered_orders_ids, directions_to_sync)
                        else:
                            ftp_connection.push_order(direction)

                except ftplib.all_errors as e:
                    ftp_connection.error(f"error: {e}")
                    ftp_connection.log("Disconnecting...")
                    ftp_connection.disconnect()

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_push_orders_start():
    stdout.write("Starting push_orders process")
    while True:
        process_push_orders()
        time.sleep(1)


def get_hospitals_pull_results():
    hospitals = Hospitals.objects.filter(result_pull_by_numbers__isnull=False, hide=False)
    return hospitals


def process_pull_results():
    processed_files_by_url = defaultdict(set)

    hospitals = get_hospitals_pull_results()

    ftp_links = {x.result_pull_by_numbers: x for x in hospitals}

    ftp_connections = {}

    for ftp_url in ftp_links:
        ftp_connection = FTPConnection(ftp_url, hospital=ftp_links[ftp_url])
        ftp_connections[ftp_url] = ftp_connection

    time_start = time.time()

    while time.time() - time_start < MAX_LOOP_TIME:
        for ftp_url, ftp_connection in ftp_connections.items():
            processed_files_new = set()
            try:
                ftp_connection.connect()
                file_list = ftp_connection.get_file_list()

                for file in file_list:
                    processed_files_new.add(file)

                    if file not in processed_files_by_url[ftp_url]:
                        ftp_connection.pull_result(file)

            except ftplib.all_errors as e:
                processed_files_new.update(processed_files_by_url[ftp_url])
                ftp_connection.error(f"error: {e}")
                ftp_connection.log("Disconnecting...")
                ftp_connection.disconnect()

            processed_files_by_url[ftp_url] = processed_files_new

        time.sleep(5)

    for _, ftp_connection in ftp_connections.items():
        ftp_connection.disconnect()


def process_pull_start_results():
    while True:
        process_pull_results()
        time.sleep(1)


def push_result(iss: Issledovaniya):
    hl7 = Message()
    meta_data = FTP_SETUP_TO_SEND_HL7_BY_RESEARCHES
    msh_meta = meta_data.get("msh")
    app_sender = msh_meta.get("app_sender")
    organization_sender = msh_meta.get("organization_sender")
    app_receiver = msh_meta.get("app_receiver")
    organization_receiver = msh_meta.get("organization_receiver")

    obr_meta = meta_data.get("obr")
    obr_executor = obr_meta.get("executer_code")

    service = iss.research.title
    if not iss.time_confirmation or not iss.napravleniye.external_order:
        return False

    if not iss.napravleniye.external_order.hl7:
        return False

    hl7_bs64 = iss.napravleniye.external_order.hl7
    hl7_source = base64.b64decode(hl7_bs64, altchars=None, validate=False).decode("utf-8").split("\n")

    confirm_datetime_service = datetime.datetime.strftime(iss.time_confirmation, "%Y%m%d%H%M%S")
    confirm_date_service = datetime.datetime.strftime(iss.time_confirmation, "%Y%m%d")
    tube = iss.tubes.all().first()
    tube_number = tube.number
    internal_id = iss.research.internal_code
    pv1_date = confirm_date_service

    results = Result.objects.filter(issledovaniye=iss)
    hl7.msh = f"MSH|^~\&|{app_sender}|{organization_sender}|{app_receiver}|{organization_receiver}|{confirm_datetime_service}||ORU^R01|{tube_number}|P|2.3|||AL|NE|22.2.19"
    hl7.pid = hl7_source[1]
    hl7.PV1 = f"PV1||O||||||||||||||||||||||||||||||||||||||||||{pv1_date}|{pv1_date}|"
    obr_val = (
        f"OBR|1|{tube_number}^{app_receiver}|{tube_number}^{app_sender}|^^^{internal_id}^{service}|||{confirm_datetime_service}|{confirm_datetime_service}"
        f"|||||^||||||||^^^||||F||^^^^^R|||||{obr_executor}||"
    )
    hl7.ORU_R01_PATIENT_RESULT.ORU_R01_ORDER_OBSERVATION.OBR.value = obr_val

    obs_name = "ORU_R01_OBSERVATION"

    step = 0
    for result in results:
        step += 1
        obx_group = Group(obs_name)
        obx = Segment("OBX")
        obx.value = f"OBX|{step}|NM|{result.fraction.fsli}^{result.fraction.title})||{result.value}|{result.fraction.unit.title}|-|||||||{confirm_date_service}"
        obx_group.add(obx)
        hl7.ORU_R01_PATIENT_RESULT.ORU_R01_ORDER_OBSERVATION.add(obx_group)

    content = hl7.value.replace("\r", "\n").replace("ORC|1\n", "")
    created_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S-%f")
    if iss.external_add_order:
        external_add_order = iss.external_add_order.external_add_order
    else:
        external_add_order = "-ext-add-ord"
    filename = f"ORU_ord-{external_add_order}_tube-{tube_number}_{created_at}.res"

    ftp_settings = msh_meta.get("ftp_settings")

    with FTP(ftp_settings["address"], ftp_settings["user"], ftp_settings["password"]) as ftp:
        ftp.cwd(ftp_settings["path"])
        ftp.storbinary(f"STOR {filename}", BytesIO(content.encode("cp1251")))

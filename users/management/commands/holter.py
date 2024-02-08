import os
import pathlib
import re
import sys
from datetime import datetime
from shutil import copytree, rmtree

import pdfkit
from dateutil.relativedelta import relativedelta
from django.core.management import BaseCommand
from django.utils import timezone
import pytz_deprecation_shim as pytz
from pyvirtualdisplay import Display

from appconf.manager import SettingManager
from directions.models import Issledovaniya, Napravleniya
from integration_framework.models import TempData
from laboratory.settings import TIME_ZONE, AFTER_DATE_HOLTER
from users.models import DoctorProfile


##################################################
# в каталогах созданных -20 дней назад
# найти файлы *.html дата изменния к-рые больше заданной(из базы)
# Если такой ф-л найден и размер > 30кБайт:
# то попытаться найти в нем последовательность цифр направления из Адрес: <b>5555555557778978978</b>
# если найдена, то проверить, что такое направление существует в L2 и оно не подтверждено, или
# подтверждено, но разница от даты подтверждения и текущей не более 48 часов
# если условия, удовлетворены, то:
# проверить путь на наличие директории ../год/месяц/число (дата из св-ва ф-ла модификации)
# если нет каталога, то создать директорию:
# потом сгенерировать с помощью pdfkit ф-л с названием: номер направления и ФИО-пациента (4600000121Иванов) и
# сохранить в каталог путь ../год/месяц/число/4600000121Иванов.pdf
# записать ссылку на ф-л на результат в спец поле в L2
# если найдена последовательность Врач: Фамилия
# подтвердить результат от имени врача
# Если нет, то от имени зав.отд.


class Command(BaseCommand):
    help = "Обработка холтера"

    def handle(self, *args, **options):
        dst_dir = SettingManager.get("root_dir")
        src_dir = SettingManager.get("src_holter")
        p = pathlib.Path(src_dir)
        temp_dir = SettingManager.get("temp_dir")

        # в каих каталогах искать "-" дней
        back_days = SettingManager.get("holter_back_days")
        d_start = datetime.now().date() - relativedelta(days=back_days)
        today_dir = datetime.now().strftime('%Y/%m/%d')
        # Ищем последовательность
        pattern = re.compile('(Направление: <b>\d+</b>;)|(Адрес: <b>\d+</b>;)')
        pattern_doc = re.compile('Врач')

        # услуга относящаяся к подразделению
        podrazdeleniye_pk = SettingManager.get("ofd")
        podrazdeleniye_users = DoctorProfile.objects.values_list('pk', 'fio').filter(podrazdeleniye=podrazdeleniye_pk)
        podrazdeleniye_manager_pk = SettingManager.get("manager_ofd")
        pk_research = SettingManager.get("holter_pk_research")

        user_timezone = pytz.timezone(TIME_ZONE)
        datetime_object = datetime.strptime(AFTER_DATE_HOLTER, '%Y-%m-%d %H:%M:%S').astimezone(user_timezone)
        holter_obj, created = TempData.objects.get_or_create(key='holter', defaults={"holter_protocol_date": datetime_object})

        if created:
            date_proto = TempData.objects.values_list('holter_protocol_date').get(key='holter')
            date_proto = date_proto[0].astimezone(user_timezone)
        else:
            date_proto = holter_obj.holter_protocol_date
            date_proto = date_proto.astimezone(user_timezone)

        doctors = {}
        for i in podrazdeleniye_users:
            k = i[1].split()
            temp_dict = {k[0]: i[0]}
            doctors.update(temp_dict)

        for f in p.iterdir():
            stat_info = f.stat()
            if datetime.fromtimestamp(stat_info.st_ctime) > datetime.combine(d_start, datetime.min.time()):
                for h in f.glob('*.html'):
                    find = False

                    stat_info = h.stat()
                    file_modify = datetime.fromtimestamp(stat_info.st_mtime).astimezone(user_timezone)
                    holter_path_result = h.as_posix()
                    file_name = holter_path_result.split('/')[-1]

                    if stat_info.st_size > 30000 and file_modify > date_proto:
                        with open(holter_path_result, 'r', encoding="cp1251") as file:
                            for line in file:
                                result = pattern.match(line)
                                if result:
                                    obj_num_dir = re.search(r'\d+', result.group(0))
                                    num_dir = int(obj_num_dir.group(0))
                                    if num_dir >= 4600000000000:
                                        num_dir -= 4600000000000
                                        num_dir //= 10
                                    obj_iss = Issledovaniya.objects.filter(napravleniye=num_dir, research=pk_research).first()
                                    if obj_iss:
                                        time_confirm = obj_iss.time_confirmation
                                        file_modify = datetime.fromtimestamp(stat_info.st_mtime).astimezone(user_timezone)
                                        if obj_iss.time_confirmation:
                                            delta_confirm = file_modify - time_confirm
                                            if delta_confirm.seconds // 60 > SettingManager.get("holter_reset_confirm"):
                                                break
                                        patient = Napravleniya.objects.filter(pk=num_dir).first()
                                        fio = patient.client.get_fio_w_card()
                                        if not os.path.exists(dst_dir + today_dir):
                                            new_dir = dst_dir + today_dir
                                            os.makedirs(new_dir)
                                        find = True
                                        current_dir = os.path.dirname(holter_path_result)

                                        TempData.objects.filter(key='holter').update(holter_protocol_date=file_modify)

                                        if os.path.exists(temp_dir):
                                            rmtree(temp_dir)
                                        copytree(current_dir, temp_dir)

                        if find:
                            with open(temp_dir + file_name, 'r', encoding="cp1251") as f:
                                old_data = f.read()
                            new_data = old_data.replace('Адрес:', fio + '<br><u>Направление:</u>')

                            with open(temp_dir + file_name, 'w', encoding="cp1251") as f:
                                f.write(new_data)

                            with open(temp_dir + file_name, 'r', encoding="cp1251") as f:
                                find_doc = False
                                break_line = False
                                pk_doc = None
                                for line in f:
                                    result = pattern_doc.search(line)
                                    if result:
                                        find_doc = True
                                    if find_doc:
                                        for doc in doctors.keys():
                                            doc_fio_find = re.search(doc, line)
                                            if doc_fio_find:
                                                pk_doc = doctors.get(doc_fio_find.group(0))
                                                break_line = True
                                                break
                                        if break_line:
                                            break

                            list_fio = fio.split()
                            link = today_dir + f'/{str(num_dir) + "_" + list_fio[2]}.pdf'
                            if sys.platform != 'win32':
                                try:
                                    display = Display(visible=0, size=(800, 600))
                                    display.start()
                                    pdfkit.from_file(temp_dir + file_name, dst_dir + link)
                                finally:
                                    display.stop()
                            else:
                                pdfkit.from_file(temp_dir + file_name, dst_dir + link)
                            if pk_doc:
                                doc_profile = DoctorProfile.objects.filter(pk=pk_doc).first()
                            else:
                                doc_profile = DoctorProfile.objects.filter(pk=podrazdeleniye_manager_pk).first()

                            t = timezone.now()
                            obj_iss.doc_confirmation = doc_profile
                            if obj_iss.napravleniye:
                                obj_iss.napravleniye.qr_check_token = None
                                obj_iss.napravleniye.save(update_fields=['qr_check_token'])
                            obj_iss.link_file = f'{today_dir}/{num_dir}_{list_fio[2]}.pdf'
                            obj_iss.time_confirmation = t
                            obj_iss.time_save = t
                            obj_iss.save(update_fields=['doc_confirmation', 'time_save', 'time_confirmation', 'link_file'])
                            obj_iss.napravleniye.sync_confirmed_fields()
                            rmtree(temp_dir)

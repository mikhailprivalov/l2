import os

import openpyxl

from appconf.manager import SettingManager
import datetime


def save_file_disk(wb):
    dir_param = SettingManager.get("dir_param", default='/tmp', default_type='s')
    today = datetime.datetime.now()
    date_now1 = datetime.datetime.strftime(today, "%y%m%d%H%M%S%f")[:-3]
    date_now_str = "offer" + str(date_now1)
    file_dir = os.path.join(dir_param, date_now_str + '.xlsx')
    wb.save(filename=file_dir)
    return file_dir


def initial_work_book(name_sheets):
    wb = openpyxl.Workbook()
    wb.remove(wb.get_sheet_by_name('Sheet'))
    ws = wb.create_sheet(name_sheets)
    return wb, ws

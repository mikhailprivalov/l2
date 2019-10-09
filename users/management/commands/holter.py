from django.core.management import BaseCommand



import pdfkit
import os, datetime
# pdfkit.from_file('c:\\my\\node_project\\holter\\ME1747190927113306.001\\ME1747190927113306.html', 'c:/tmp/holter24.pdf')
# path = 'c:\\my\\node_project\\holter\\ME1747190927113306.001\\ME1747190927113306.html'
# a = os.path.getmtime(path)
#2019-09-30 22:11:51.790084
# print(datetime.datetime.fromtimestamp(a))

import  pathlib, sys, time
# p = pathlib.Path('c:\\my\\node_project\\holter\\ME1747190927113306.001\\ME1747190927113306.html')
# p = pathlib.Path('c:\\my\\node_project\\holter\\ME1747190927113306.001\\')
# stat_info = p.stat()
# print(f'{p}')
# print(f"Size: {stat_info.st_size}")
# print(f"created: {time.ctime(stat_info.st_ctime)}")
# print(f"modify: {time.ctime(stat_info.st_mtime)}")
# print(f"acces: {time.ctime(stat_info.st_atime)}")
# print(f"acces: {time.ctime(stat_info.st_atime)}")

##################################################
# в каталогах созданных -20 дней назад
# найти файлы *.html дата изменния к-рые больше заданной(из базы)
# Если такой ф-л найден и размер > 30кБайт:
  # то попытаться найти в нем последовательность цифр направления из Адрес: <b>5555555557778978978</b>
    #если найдена, то проверить, что такое направление существует в L2 и оно не подтверждено, или
                   #подтверждено, но разница от дата подтверждения и текущей не более 48 часов
      #если условия, удовлетворены, то:
        #проверить путь на наличие директории ../год/месяц/число (дата из св-ва ф-ла модификации)
        #если нет каталога, то создать директорию:
          #потом сгенерировать с помощью pdfkit ф-л с названием: номер направления и ФИО-пациента (4600000121Иванов) и
          #сохранить в каталог путь ../год/месяц/число/4600000121Иванов.pdf
          #записать ссылку на ф-л на результат в спец поле в L2
          #если найдена последовательность Врач: Фамилия
              #подтвердить результат от имени врача
          #Если нет, то от имени зав.отд.
import pathlib, re
from datetime import datetime
from dateutil.relativedelta import *

class Command(BaseCommand):
    help = "Обработка холтера"

    def handle(self, *args, **options):
        d_start = datetime.now().date() - relativedelta(days=+10)
        pattern = re.compile('(Направление: <b>\d+</b>;)|(Адрес: <b>\d+</b>;)')
        p = pathlib.Path('d:/holter/')
        for f in p.iterdir():
            stat_info = f.stat()
            if datetime.fromtimestamp(stat_info.st_ctime) > datetime.combine(d_start, datetime.min.time()):
                for h in f.glob('*.html'):
                    find = False
                    stat_info = h.stat()
                    if stat_info.st_size > 30000:
                        with open(h) as file:
                            for line in file:
                                result = pattern.match(line)
                                if result:
                                    obj_num_dir = re.search(r'\d+', result.group(0))
                                    num_dir = obj_num_dir.group(0)
                                    print(num_dir)
                                    find = True
                                    break
                        if find:
                            with open(h, 'r') as f:
                                old_data = f.read()
                            new_data = old_data.replace('Адрес:', 'Направление:')
                            with open(h, 'w') as f:
                                f.write(new_data)
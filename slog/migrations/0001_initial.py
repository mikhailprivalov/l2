# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_auto_20150609_0350'),
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
                ('type', models.IntegerField(
                    choices=[(0, 'Другое'), (1, 'Справочник: добавлена пробирка'), (2, 'Справочник: изменена пробирка'),
                             (3, 'Справочник: добавлен анализ'), (4, 'Справочник: изменен анализ'),
                             (5, 'Справочник: добавлена группа направления'),
                             (6, 'Справочник: изменена группа направления'), (7, 'Направления: создано направление'),
                             (8, 'Взятие материала: открыто направление'), (9, 'Взятие материала: пробирка взята'),
                             (10, 'Взятие материала: напечатан акт приема-передачи'),
                             (11, 'Прием материала: материал принят'), (12, 'Прием материала: материал не принят'),
                             (13, 'Ввод результатов: результат сохранен'),
                             (14, 'Ввод результатов: результат подтвержден'),
                             (15, 'Ввод результатов: результаты для направления напечатаны'),
                             (16, 'Администрирование: создан пользователь'),
                             (17, 'Администрирование: создано подразделение'),
                             (18, 'Пользователи: вход пользователя')])),
                ('body', models.CharField(max_length=1023)),
                ('time', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(to='users.DoctorProfile')),
            ],
        ),
    ]

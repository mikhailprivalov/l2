# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-07 05:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0022_auto_20160817_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='can_lab_result_comment',
            field=models.BooleanField(default=False, help_text='Возможность оставить комментарий лабораторией'),
        ),
    ]

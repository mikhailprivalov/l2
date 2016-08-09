# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0018_researches_comment_template'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResearchGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('title', models.CharField(max_length=63)),
            ],
        ),
        migrations.AddField(
            model_name='researches',
            name='groups',
            field=models.ManyToManyField(to='directory.ResearchGroup'),
        ),
    ]

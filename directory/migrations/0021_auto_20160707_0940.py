# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):
    dependencies = [
        ('directory', '0020_researchgroup_lab'),
    ]

    operations = [
        migrations.AddField(
            model_name='researches',
            name='onlywith',
            field=models.ForeignKey(blank=True, help_text='Без выбранного анализа не можеть быть назначено', null=True,
                                    to='directory.Researches'),
        ),
        migrations.AlterField(
            model_name='absorption',
            name='flower',
            field=models.ForeignKey(help_text='Какая фракция поглащяется главной', to='directory.Fractions',
                                    related_name='flower'),
        ),
        migrations.AlterField(
            model_name='absorption',
            name='fupper',
            field=models.ForeignKey(help_text='Какая фракция главнее', to='directory.Fractions', related_name='fupper'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='hide',
            field=models.BooleanField(default=False, help_text='Скрытие фракции'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='max_iterations',
            field=models.IntegerField(default=1, help_text='Максимальное число итераций'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='options',
            field=models.CharField(blank=True, default='', max_length=511,
                                   help_text='Варианты для динамического числа полей'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='ref_f',
            field=jsonfield.fields.JSONField(help_text='Референсы (Ж)'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='ref_m',
            field=jsonfield.fields.JSONField(help_text='Референсы (М)'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='relation',
            field=models.ForeignKey(to='directory.ReleationsFT', help_text='Пробирка (пробирки)'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='render_type',
            field=models.IntegerField(default=0, blank=True,
                                      help_text='Тип рендеринга (базовый тип (0) или динамическое число полей (1)'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='research',
            field=models.ForeignKey(to='directory.Researches', help_text='Исследование, к которому относится фракция'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='sort_weight',
            field=models.IntegerField(null=True, default=0, blank=True, help_text='Вес соритировки'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='title',
            field=models.CharField(max_length=255, help_text='Название фракции'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='type',
            field=models.IntegerField(null=True, default=-1, blank=True, help_text='Варианты подсказок результатов'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='uet_doc',
            field=models.FloatField(default=0, help_text='УЕТы для врача'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='uet_lab',
            field=models.FloatField(default=0, help_text='УЕТы для лаборанта'),
        ),
        migrations.AlterField(
            model_name='fractions',
            name='units',
            field=models.CharField(max_length=255, help_text='Еденицы измерения'),
        ),
        migrations.AlterField(
            model_name='releationsft',
            name='tube',
            field=models.ForeignKey(to='researches.Tubes', help_text='Пробирка'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='comment_template',
            field=models.IntegerField(null=True, default=-1, blank=True, help_text='Варианты комментариев к материалу'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='direction',
            field=models.ForeignKey(blank=True, help_text='Группа направления', null=True,
                                    to='directory.DirectionsGroup'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='edit_mode',
            field=models.IntegerField(default=0,
                                      help_text='0 - Лаборант может сохранять и подтверждать. 1 - Лаборант сохраняет, врач должен подтвердить'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='groups',
            field=models.ManyToManyField(to='directory.ResearchGroup', help_text='Группа исследований в лаборатории'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='hide',
            field=models.BooleanField(default=False, help_text='Скрытие исследования'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='no_attach',
            field=models.IntegerField(null=True, default=0, blank=True,
                                      help_text='Группа исследований, которые не могут быть назначены вместе'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='preparation',
            field=models.CharField(default='', max_length=2047, help_text='Подготовка к исследованию'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='quota_oms',
            field=models.IntegerField(default=-1, help_text='Квота по ОМС'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='sort_weight',
            field=models.IntegerField(null=True, default=0, blank=True, help_text='Вес сортировки'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='subgroup',
            field=models.ForeignKey(help_text='Подгруппа в лаборатории', to='podrazdeleniya.Subgroups',
                                    related_name='subgroup'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='template',
            field=models.IntegerField(default=0, blank=True, help_text='Шаблон формы'),
        ),
        migrations.AlterField(
            model_name='researches',
            name='title',
            field=models.CharField(default='', max_length=255, help_text='Название исследования'),
        ),
        migrations.AlterField(
            model_name='researchgroup',
            name='lab',
            field=models.ForeignKey(blank=True, help_text='Лаборатория', null=True, to='podrazdeleniya.Podrazdeleniya'),
        ),
        migrations.AlterField(
            model_name='researchgroup',
            name='title',
            field=models.CharField(max_length=63, help_text='Название группы'),
        ),
    ]

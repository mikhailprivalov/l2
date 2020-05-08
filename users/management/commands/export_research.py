from django.core.management.base import BaseCommand
from directory.models import Researches, ParaclinicInputGroups, ParaclinicInputField
import json
from appconf.manager import SettingManager


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('research_pk', type=str)

    def handle(self, *args, **kwargs):
        research = kwargs["research_pk"]
        research_pk = int(research)
        obj_research = {}
        r = Researches.objects.get(pk=research_pk)
        obj_research['title'] = r.title
        obj_research['code'] = r.code
        obj_research['short_title'] = r.short_title
        groups = ParaclinicInputGroups.objects.filter(research=r)
        t_group = []
        for i in groups:
            fieds = ParaclinicInputField.objects.filter(group=i, hide=False)
            t_field = []
            order = str(i.order)
            for f in fieds:
                field_data = {'title': f.title, 'order': f.order, 'default_value': f.default_value, 'lines': f.lines, 'field_type': f.field_type,
                              'for_extract_card': f.for_extract_card, 'for_talon': f.for_talon, 'helper': f.helper, 'input_templates': f.input_templates,
                              'required': f.required, 'hide': f.hide}
                t_field.append(field_data)
            t_group.append({'title': i.title, 'show_title': i.show_title, 'order': order, 'hide': i.hide, 'ParaclinicInputField': t_field.copy()})
        obj_research['ParaclinicInputGroups'] = t_group
        dir_tmp = SettingManager.get("dir_param")
        with open(f'{dir_tmp}/{research}.json', 'w') as fp:
            json.dump(obj_research, fp)

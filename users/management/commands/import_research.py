from django.core.management.base import BaseCommand
from directory.models import Researches, ParaclinicInputGroups, ParaclinicInputField
import json
from laboratory import utils


class Command(BaseCommand):
    def add_arguments(self, parser):
        """
        :param path - файл
        """
        parser.add_argument('path', type=str)

    def handle(self, *args, **kwargs):
        fp = kwargs["path"]

        self.stdout.write("Path: " + fp)
        with open(fp) as json_file:
            data = json.load(json_file)
            dt = utils.current_time()
            d = utils.strdatetime(dt)
            title = f"{d}-{data['title']}"
            r = Researches(title=title, code=data['code'], short_title=data['short_title'])
            r.save()
            for group in data['paraclinic_input_groups']:
                group_current = ParaclinicInputGroups(research=r, title=group["title"], show_title=group["show_title"], order=group["order"], hide=group["hide"])
                group_current.save()
                for f in group['paraclinic_input_field']:
                    field = ParaclinicInputField(group=group_current, title=f['title'], order=f['order'], default_value=f['default_value'], lines=f['lines'], field_type=f['field_type'],
                                                 for_extract_card=f['for_extract_card'], for_talon=f['for_talon'], helper=f['helper'], input_templates=f['input_templates'],
                                                 required=f['required'], hide=f['hide'])
                    field.save()

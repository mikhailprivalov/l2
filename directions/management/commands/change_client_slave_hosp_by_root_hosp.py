from django.core.management.base import BaseCommand
from directions.models import Napravleniya, Issledovaniya


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('history_id', type=str)

    def handle(self, *args, **kwargs):
        """
        :param history_id - Номер направления на историю болезни
        Смена карты у всех подчиненных направлений в т.ч историй болезни, вывод историй у которых могут быть свои подчиненные услуги.
        Необходимо прогнать все истории которые будут выведены
        """

        history_id = kwargs['history_id']
        need_change_history_ids = set()
        direction: Napravleniya = Napravleniya.objects.filter(pk=history_id).first()
        if not direction:
            self.stdout.write('Такого направления нет')
            return None
        issledovanie: Issledovaniya = Issledovaniya.objects.filter(napravleniye_id=direction.pk).select_related('research').first()
        if not issledovanie.research.is_hospital:
            self.stdout.write('Данное направление не является историей болезни')
            return None
        slave_hospital_directions: issledovanie = Napravleniya.objects.filter(parent_id=issledovanie.pk)
        for slave_direction in slave_hospital_directions:
            slave_direction.client_id = direction.client_id
            slave_direction.save()
            self.stdout.write(f'У направления {slave_direction.pk} изменена карта на {direction.client_id}')
            slave_direction_issledovanie: Issledovaniya = Issledovaniya.objects.filter(napravleniye_id=slave_direction.pk).select_related('research').first()
            if slave_direction_issledovanie.research.is_hospital:
                need_change_history_ids.add(slave_direction.pk)
        self.stdout.write(f'Следующие направления - истории болезни (при необходимости повторите скрипт с этими направлениями) \n' f'{need_change_history_ids}')

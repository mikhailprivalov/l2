from django.core.management.base import BaseCommand
from directory.models import Researches
import users.models as users


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('research_pk', type=int)

    def handle(self, *args, **kwargs):
        research_pk = kwargs["research_pk"]
        r = Researches.objects.get(pk=research_pk)
        us = users.DoctorProfile.objects.all()

        for doc in us:
            doc.restricted_to_direct.add(r)
            doc.save()

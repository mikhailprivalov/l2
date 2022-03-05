from django.db.models.signals import post_save, post_delete

import clients.models as clients
import directions.models as directions
import directory.models as directory
import podrazdeleniya.models as podrazdeleniya
import researches.models as researches
import users.models as users
from laboratory.settings import DEPRECATED_RMQ_ENABLED
from mq.publisher import mq_send


def post_save_l2(sender, instance, created, **kwargs):
    if not DEPRECATED_RMQ_ENABLED:
        return
    s_name = str(sender).split("'")
    s_name = s_name[1]
    mq_send("created" if created else "updated", s_name, instance.pk)


def post_delete_l2(sender, instance, **kwargs):
    if not DEPRECATED_RMQ_ENABLED:
        return
    s_name = str(sender).split("'")
    s_name = s_name[1]
    mq_send("deleted", s_name, instance.pk)


for s in [
    directions.RMISOrgs,
    directions.Napravleniya,
    directions.Issledovaniya,
    directions.TubesRegistration,
    directions.Result,
    directions.ParaclinicResult,
    clients.CardBase,
    directions.IstochnikiFinansirovaniya,
    clients.Individual,
    clients.Card,
    podrazdeleniya.Podrazdeleniya,
    users.DoctorProfile,
    researches.Tubes,
    directory.Researches,
    directory.Fractions,
    directory.ParaclinicInputGroups,
    directory.ParaclinicInputField,
]:
    post_save.connect(post_save_l2, sender=s)
    post_delete.connect(post_delete_l2, sender=s)

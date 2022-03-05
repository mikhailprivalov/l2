from directory.models import Researches
from doctor_schedule.models import ScheduleResource, UserResourceModifyRights
from users.models import DoctorProfile


def can_access_user_to_modify_resource(user: DoctorProfile, resource_param: ScheduleResource = None, resource_pk: int = None):
    if resource_param:
        resource: ScheduleResource = resource_param
    else:
        resource: ScheduleResource = ScheduleResource.objects.filter(pk=resource_pk).first()

    if not resource:
        return False

    rights: UserResourceModifyRights = UserResourceModifyRights.objects.filter(user=user).first()
    if not rights:
        return False

    if resource in rights.resources.all():
        return True

    executor: DoctorProfile = resource.executor
    if executor and executor.podrazdeleniye and executor.podrazdeleniye in rights.departments.all():
        return True

    services = rights.services.all()
    service: Researches
    for service in resource.service.all():
        if service in services:
            return True

    return False

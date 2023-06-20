from appconf.manager import SettingManager
from directions.models import Issledovaniya
from integration_framework.views import get_json_protocol_data
from utils.tree_directions import expertise_tree_direction


def get_expertise(pk, with_check_available=False):
    expertise_data = {
        'canCreateExpertise': False,
        'serviceId': None,
        'serviceTitle': None,
        'status': 'empty',
        'directions': [],
    }

    if SettingManager.l2('expertise'):
        iss_pk = Issledovaniya.objects.filter(napravleniye_id=pk).values_list('pk').first()
        expertise_from_sql = expertise_tree_direction(iss_pk) if iss_pk else []

        if with_check_available:
            iss: Issledovaniya = Issledovaniya.objects.filter(napravleniye_id=pk).first()
            if iss.research and iss.research.expertise_params_id and iss.time_confirmation:
                expertise_data['serviceId'] = iss.research.expertise_params_id
                expertise_data['serviceTitle'] = iss.research.expertise_params.get_title()
                expertise_data['status'] = 'available'
                expertise_data['canCreateExpertise'] = True

        for i in expertise_from_sql:
            if i.level == 2 and i.is_expertise:
                without_remarks = False
                if i.date_confirm:
                    result_protocol = get_json_protocol_data(i.napravleniye_id)
                    content = result_protocol["content"]
                    if content and content.get("Наличие замечаний"):
                        if content.get("Наличие замечаний", "").lower() == "нет":
                            without_remarks = True
                expertise_data['directions'].append(
                    {
                        "pk": i.napravleniye_id,
                        "confirmedAt": f"{i.date_confirm} {i.time_confirm}" if i.date_confirm else None,
                        "withoutRemarks": without_remarks,
                        "serviceTitle": i.title,
                    }
                )
                if i.date_confirm:
                    expertise_data['status'] = 'ok' if without_remarks else 'error'
    return expertise_data

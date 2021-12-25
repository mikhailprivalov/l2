from appconf.manager import SettingManager
from directions.models import Issledovaniya
from integration_framework.views import get_json_protocol_data
from utils.tree_directions import expertise_tree_direction


def get_expertise(pk):
    expertise_data = []
    if SettingManager.l2('expertise'):
        iss_pk = Issledovaniya.objects.filter(napravleniye_id=pk).values_list('pk').first()
        expertise_from_sql = expertise_tree_direction(iss_pk) if iss_pk else []
        for i in expertise_from_sql:
            if i.level == 2 and i.is_expertise:
                not_remarks = False
                if i.date_confirm:
                    result_protocol = get_json_protocol_data(i.napravleniye_id)
                    content = result_protocol["content"]
                    if content and content.get("Наличие замечаний"):
                        if content["Наличие замечаний"].lower() == "нет":
                            not_remarks = True
                expertise_data.append({"direction": i.napravleniye_id, "confirm": i.date_confirm, "not_remarks": not_remarks})
    return expertise_data

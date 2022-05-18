from directory.models import (
    Researches as DResearches,
    ParaclinicInputGroups,
    ParaclinicInputField,
)
import simplejson as json


def get_researches_details(pk):
    response = {"pk": -1, "department": -1, "title": '', "short_title": '', "code": '', "info": '', "hide": False, "groups": []}
    direction_params_all = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": x.title} for x in DResearches.objects.filter(is_direction_params=True).order_by("title")]]
    response["direction_params_all"] = direction_params_all
    direction_expertise_all = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": x.title} for x in DResearches.objects.filter(is_expertise=True).order_by("title")]]
    response["direction_expertise_all"] = direction_expertise_all
    if DResearches.objects.filter(pk=pk).exists():
        res: DResearches = DResearches.objects.get(pk=pk)
        response["pk"] = res.pk
        response["department"] = res.podrazdeleniye_id or (-2 if not res.is_hospital else -1)
        response["title"] = res.title
        response["short_title"] = res.short_title
        response["schedule_title"] = res.schedule_title
        response["code"] = res.code
        response["info"] = res.paraclinic_info or ""
        response["hide"] = res.hide
        response["tube"] = res.microbiology_tube_id or -1
        response["site_type"] = res.site_type_id
        response["internal_code"] = res.internal_code
        response["direction_current_form"] = res.direction_form
        response["show_more_services"] = res.show_more_services
        response["result_current_form"] = res.result_form
        response["conclusionTpl"] = res.bac_conclusion_templates
        response["cultureTpl"] = res.bac_culture_comments_templates
        response["speciality"] = res.speciality_id or -1
        response["direction_current_params"] = res.direction_params_id or -1
        response["direction_current_expertise"] = res.expertise_params_id or -1
        response["is_global_direction_params"] = res.is_global_direction_params
        response["is_paraclinic"] = res.is_paraclinic
        response["type_period"] = res.type_period
        response["assigned_to_params"] = []
        if res.is_direction_params:
            response["assigned_to_params"] = [f'{x.pk} – {x.get_full_short_title()}' for x in DResearches.objects.filter(direction_params=res)]

        for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
            g = {"pk": group.pk, "order": group.order, "title": group.title, "show_title": group.show_title, "hide": group.hide, "fields": [], "visibility": group.visibility}
            for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
                g["fields"].append(
                    {
                        "pk": field.pk,
                        "order": field.order,
                        "lines": field.lines,
                        "for_extract_card": field.for_extract_card,
                        "sign_organization": field.sign_organization,
                        "title": field.title,
                        "default": field.default_value,
                        "visibility": field.visibility,
                        "hide": field.hide,
                        "values_to_input": json.loads(field.input_templates),
                        "field_type": field.field_type,
                        "required": field.required,
                        "not_edit": field.not_edit,
                        "for_talon": field.for_talon,
                        "for_med_certificate": field.for_med_certificate,
                        "helper": field.helper,
                        "new_value": "",
                        "attached": field.attached,
                        "controlParam": field.control_param,
                    }
                )
            response["groups"].append(g)
    return response


def get_can_created_patient():
    researches = DResearches.objects.filter(can_created_patient=True, hide=False)
    result = [{"pk": i.pk, "title": i.get_title(), "isRequest": i.convert_to_doc_call} for i in researches]
    return result

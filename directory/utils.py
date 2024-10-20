from api.directions.sql_func import get_template_field_by_department
from directory.models import (
    Researches as DResearches,
    ParaclinicInputGroups,
    ParaclinicInputField,
    PatientControlParam, PatternParam,
)
import simplejson as json

from external_system.models import InstrumentalResearchRefbook, CdaFields
from external_system.sql_func import get_unique_method_instrumental_diagnostic


def get_researches_details(pk, templates_department_pk=None):
    response = {"pk": -1, "department": -1, "title": '', "short_title": '', "code": '', "info": '', "hide": False, "groups": []}
    direction_params_all = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": x.title} for x in DResearches.objects.filter(is_direction_params=True).order_by("title")]]
    response["direction_params_all"] = direction_params_all
    response["patient_control_param_all"] = PatientControlParam.get_patient_control_params()
    research = DResearches.objects.filter(pk=pk).first()
    response["cda_options"] = CdaFields.get_cda_params(research.is_doc_refferal, research.is_treatment, research.is_form, research.is_extract)
    response["patternParams"] = PatternParam.get_pattern_params()
    direction_expertise_all = [{"id": -1, "label": "Пусто"}, *[{"id": x.pk, "label": x.title} for x in DResearches.objects.filter(is_expertise=True).order_by("title")]]
    response["direction_expertise_all"] = direction_expertise_all
    if DResearches.objects.filter(pk=pk).exists():
        res: DResearches = DResearches.objects.get(pk=pk)
        response["collectMethods"] = [{"id": -1, "label": "Пусто"}]
        response["collectNsiResearchCode"] = [{"id": -1, "label": "Пусто"}]
        if res.is_paraclinic:
            methods = get_unique_method_instrumental_diagnostic()
            result_method = [{"id": i.method, "label": i.method} for i in methods]
            response["currentNsiResearchCode"] = res.nsi_id
            response["collectMethods"].extend(result_method)
        else:
            response["currenttMethod"] = -1
        response["pk"] = res.pk
        response["currentNsiResearchCode"] = res.nsi_id if res.nsi_id else -1
        if response["currentNsiResearchCode"] and str(response["currentNsiResearchCode"]) != "-1":
            nsi_res = InstrumentalResearchRefbook.objects.filter(code_nsi=int(response["currentNsiResearchCode"])).first()
            response["collectNsiResearchCode"] = [{"id": nsi_res.code_nsi, "label": f"{nsi_res.code_nsi}-{nsi_res.title}; область--{nsi_res.area}; локализация--{nsi_res.localization}"}]

        response["department"] = res.podrazdeleniye_id or (-2 if not res.is_hospital else -1)
        response["title"] = res.title
        response["short_title"] = res.short_title
        response["autoRegisterRmisLocation"] = res.auto_register_on_rmis_location
        response["schedule_title"] = res.schedule_title
        response["code"] = res.code
        response["info"] = res.paraclinic_info or ""
        response["hide"] = res.hide
        response["templatesByDepartment"] = res.templates_by_department
        response["tube"] = res.microbiology_tube_id or -1
        response["site_type"] = res.site_type_id
        response["internal_code"] = res.internal_code
        response["uet_refferal_co_executor_1"] = res.uet_refferal_co_executor_1
        response["uet_refferal_doc"] = res.uet_refferal_doc
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

        templates_fields_data = {}
        if res.templates_by_department and templates_department_pk:
            templates_fields = get_template_field_by_department(res.pk, templates_department_pk)
            templates_fields_data = {template.field_id: template.value for template in templates_fields}
        for group in ParaclinicInputGroups.objects.filter(research__pk=pk).order_by("order"):
            g = {
                "pk": group.pk,
                "order": group.order,
                "title": group.title,
                "show_title": group.show_title,
                "hide": group.hide,
                "fields": [],
                "visibility": group.visibility,
                "fieldsInline": group.fields_inline,
                "cdaOption": group.cda_option_id if group.cda_option else -1,
            }

            for field in ParaclinicInputField.objects.filter(group=group).order_by("order"):
                g["fields"].append(
                    {
                        "pk": field.pk,
                        "order": field.order,
                        "lines": field.lines,
                        "for_extract_card": field.for_extract_card,
                        "sign_organization": field.sign_organization,
                        "title": field.title,
                        "short_title": field.short_title,
                        "default": field.default_value,
                        "visibility": field.visibility,
                        "hide": field.hide,
                        "values_to_input": json.loads(field.input_templates) if not templates_department_pk else json.loads(templates_fields_data.get(field.pk, '[]')),
                        "field_type": field.field_type,
                        "can_edit": field.can_edit_computed,
                        "required": field.required,
                        "not_edit": field.not_edit,
                        "operator_enter_param": field.operator_enter_param,
                        "for_talon": field.for_talon,
                        "for_med_certificate": field.for_med_certificate,
                        "helper": field.helper,
                        "new_value": "",
                        "attached": field.attached,
                        "controlParam": field.control_param,
                        "patientControlParam": field.patient_control_param_id if field.patient_control_param else -1,
                        "cdaOption": field.cda_option_id if field.cda_option else -1,
                        "patternParam": field.statistic_pattern_param_id if field.statistic_pattern_param else -1,
                    }
                )
            response["groups"].append(g)
    return response


def get_can_created_patient():
    researches = DResearches.objects.filter(can_created_patient=True, hide=False)
    result = [{"pk": i.pk, "title": i.get_title(), "isRequest": i.convert_to_doc_call} for i in researches]
    return result

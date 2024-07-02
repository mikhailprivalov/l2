import hashlib
from typing import Optional

import simplejson
from django.core.cache import cache
from django.db.models.signals import post_save

import laboratory
import appconf.models as appconf


class SettingManager:
    VERSION = f"{laboratory.VERSION}-14"
    WARMUP_TEST_KEY = f'SettingManager:test-warmup:v{VERSION}'
    FULL_CACHE_L2_KEY = f'SettingManager:l2:v{VERSION}'
    FULL_CACHE_EN_KEY = f'SettingManager:en:v{VERSION}'

    @staticmethod
    def warmup():
        cache.set(SettingManager.WARMUP_TEST_KEY, True, 1)

        if not cache.get(SettingManager.WARMUP_TEST_KEY):
            print('SettingManager: cache is disabled')  # noqa: T001
            return

        cache.delete(SettingManager.FULL_CACHE_L2_KEY)
        cache.delete(SettingManager.FULL_CACHE_EN_KEY)

        post_save.disconnect(save_setting, sender=appconf.Setting)
        print('SettingManager: warming up')  # noqa: T001

        s: appconf.Setting
        for s in appconf.Setting.objects.all():
            SettingManager.get(s.name, rebuild=True)

        post_save.connect(save_setting, sender=appconf.Setting)

    @staticmethod
    def get(key, default: Optional[str] = None, default_type: str = 's', rebuild=False):
        no_cache = '#no-cache#' in key
        k = f'setting_manager:v{SettingManager.VERSION}:{key}'
        cv = cache.get(k) if not no_cache and not rebuild else None
        if cv:
            return simplejson.loads(cv)
        row = appconf.Setting.objects.filter(name=key).first()
        if not row:
            row = appconf.Setting.objects.create(name=key, value=key if default is None else default, value_type=default_type)
        value = row.get_value()
        if not no_cache:
            cache.set(k, simplejson.dumps(value), 60 * 60 * 24)
        return value

    @staticmethod
    def set_value(key, value, default_type='s'):
        row = appconf.Setting.objects.filter(name=key).first()
        if not row:
            SettingManager.get(key, value, default_type=default_type)
        else:
            row.value = value or ''
            row.save()

    @staticmethod
    def l2(key, default='false'):
        return SettingManager.get('l2_{}'.format(key), default=default, default_type='b')

    @staticmethod
    def forms_url():
        link_review = ''
        if SettingManager.get("show_review", default='true', default_type='b'):
            link_review = 'https://forms.yandex.ru/u/6327b35ab4d9a1750ea721f2/'
        return link_review

    @staticmethod
    def get_eds_base_url():
        return SettingManager.get("eds_base_url", default='http://empty', default_type='s')

    @staticmethod
    def get_cda_base_url():
        return SettingManager.get("cda_base_url", default='empty', default_type='s')

    @staticmethod
    def get_api_ecp_base_url():
        return SettingManager.get("api_ecp_base_url", default='empty', default_type='s')

    @staticmethod
    def get_l2vi_base_url():
        return SettingManager.get("l2vi_base_url", default='empty', default_type='s')

    @staticmethod
    def get_medbook_auto_start():
        return SettingManager.get("medbook_auto_start", default='100000', default_type='i')

    @staticmethod
    def qr_check_result():
        return SettingManager.get("qr_check_result", default='false', default_type='b')

    @staticmethod
    def qr_check_url():
        return SettingManager.get("qr_check_url", default='', default_type='s')

    @staticmethod
    def instance_id():
        return SettingManager.get("instance_id", default='', default_type='s')

    @staticmethod
    def get_dynamic_directory_version():
        return SettingManager.get("dynamic_directory_version", default='0', default_type='i')

    @staticmethod
    def inc_dynamic_directory_version():
        current_version = SettingManager.get_dynamic_directory_version()
        SettingManager.set_value("dynamic_directory_version", str(current_version + 1), default_type='i')

    @staticmethod
    def l2_modules() -> dict:
        k = SettingManager.FULL_CACHE_L2_KEY
        cv = cache.get(k)
        if cv:
            return simplejson.loads(cv)
        result = {
            **{
                'l2_{}'.format(x): SettingManager.l2(x)
                for x in [
                    "cards_module",
                    "fast_templates",
                    "stat_btn",
                    "treatment",
                    "stom",
                    "hosp",
                    "rmis_queue",
                    "benefit",
                    "harmful_factor",
                    "company_statistic_async_search",
                    "microbiology",
                    "citology",
                    "gistology",
                    "amd",
                    "direction_purpose",
                    "external_organizations",
                    "vaccine",
                    "tfoms",
                    "doc_call",
                    "list_wait",
                    "is_core",
                    "tfoms_as_l2",
                    "force_rmis_search",
                    "load_file",
                    "send_doc_calls",
                    "only_doc_call",
                    "forms",
                    "applications",
                    "eds",
                    "profcenter",
                    "extra_notifications",
                    "monitorings",
                    "schedule",
                    "expertise",
                    "l2vi",
                    "morfology_additional",
                    "some_links",
                    "without_lab_and_paraclinic",
                    "statistics",
                    "price_with_categories",
                    "decriptive_coexecutor",
                    "decriptive_additional_number",
                    "employee_job",
                    "send_orgs_email_results",
                    "send_patients_email_results",
                    "docx_aggregate_laboratory_results",
                    "need_order_redirection",
                    "chats",
                    "csv_load_file",
                    "transfer_card",
                    "disable_death_cert",
                    "price_customer",
                    "price_externel_performer",
                    "ftp",
                    "case",
                    "hide_show_count_param",
                    "fraction_comment",
                    "required_choose_case",
                    "calculate_researches",
                    "schedule_in_protocol",
                    "feed",
                    "equipment_load_file",
                    "show_button_barcode",
                    "show_button_set_document",
                    "show_button_summ",
                    "show_button_without_print",
                    "research_select_col",
                    "code_price",
                    "all_service",
                    "show_barcode_button_in_direction_history",
                ]
            },
            "consults_module": SettingManager.get("consults_module", default='false', default_type='b'),
            "directions_params": SettingManager.get("directions_params", default='false', default_type='b'),
            "morfology": SettingManager.is_morfology_enabled(SettingManager.en()),
            "paraclinic_module": SettingManager.get("paraclinic_module", default='false', default_type='b'),
            "eds_base_url": SettingManager.get_eds_base_url(),
            "medbook_auto_start": SettingManager.get_medbook_auto_start(),
            "descriptive_rich_text": SettingManager.get("descriptive_rich_text", default='false', default_type='b'),
            "number_generator_field": SettingManager.get("number_generator_field", default='false', default_type='b'),
            "tfoms_attachment_field": SettingManager.get("tfoms_attachment_field", default='false', default_type='b'),
            "auto_clinical_examination_direct": SettingManager.get("auto_clinical_examination_direct", default='false', default_type='b'),
            "legal_authenticator": SettingManager.get("legal_authenticator", default='false', default_type='b'),
            "change_password": SettingManager.get("change_password", default='false', default_type='b'),
            "limit_age_patient_registration": SettingManager.get("limit_age_patient_registration", default='false', default_type='b'),
            "days_subtract": SettingManager.get("days_subtract", default='90', default_type='i'),
            "forms_url": SettingManager.forms_url(),
        }
        cache.set(k, simplejson.dumps(result), 60 * 60 * 8)
        return result

    @staticmethod
    def l2_modules_md5_of_values():
        return hashlib.md5(simplejson.dumps(SettingManager.l2_modules()).encode('utf-8')).hexdigest()

    @staticmethod
    def en():
        k = SettingManager.FULL_CACHE_EN_KEY

        cv = cache.get(k)
        if cv:
            result = simplejson.loads(cv)
        else:
            result = {
                3: SettingManager.get("paraclinic_module", default='false', default_type='b'),
                4: SettingManager.get("consults_module", default='false', default_type='b'),
                5: SettingManager.l2('treatment'),
                6: SettingManager.l2('stom'),
                7: SettingManager.l2('hosp'),
                8: SettingManager.l2('microbiology'),
                9: SettingManager.l2('citology'),
                10: SettingManager.l2('gistology'),
                11: SettingManager.l2('forms'),
                12: SettingManager.get("directions_params", default='false', default_type='b'),
                13: SettingManager.l2("applications"),
                14: SettingManager.l2("monitorings"),
                16: SettingManager.l2("case"),
                18: SettingManager.l2("complex"),
            }

            cache.set(k, simplejson.dumps(result), 60 * 60 * 8)

        return {int(x): result[x] for x in result}

    @staticmethod
    def is_morfology_enabled(en: dict):
        return bool(en.get(8)) or bool(en.get(9)) or bool(en.get(10))


def save_setting(sender, instance, **kwargs):
    SettingManager.warmup()


post_save.connect(save_setting, sender=appconf.Setting)

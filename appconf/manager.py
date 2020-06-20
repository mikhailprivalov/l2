import simplejson
from django.core.cache import cache

import appconf.models as appconf


class SettingManager:

    @staticmethod
    def get(key, default=None, default_type='s'):
        k = 'setting_manager_' + key
        cv = cache.get(k)
        if cv:
            return simplejson.loads(cv)
        row = appconf.Setting.objects.filter(name=key).first()
        if not row:
            row = appconf.Setting.objects.create(name=key, value=key if default is None else default,
                                                 value_type=default_type)
        value = row.get_value()
        cache.set(k, simplejson.dumps(value), 20)
        return value

    @staticmethod
    def l2(key):
        return SettingManager.get('l2_{}'.format(key), default='false', default_type='b')

    @staticmethod
    def l2_modules():
        return {
            **{'l2_{}'.format(x): SettingManager.l2(x) for x in [
                "cards_module",
                "fast_templates",
                "stat_btn",
                "treatment",
                "stom",
                "hosp",
                "rmis_queue",
                "benefit",
                "microbiology",
                "citology",
                "gistology",
                "amd",
                "direction_purpose",
                "external_organizations",
                "vaccine",
            ]},
            "consults_module": SettingManager.get("consults_module", default='false', default_type='b'),
            "morfology": SettingManager.is_morfology_enabled(SettingManager.en())
        }

    @staticmethod
    def en():
        return {
            3: SettingManager.get("paraclinic_module", default='false', default_type='b'),
            4: SettingManager.get("consults_module", default='false', default_type='b'),
            5: SettingManager.l2('treatment'),
            6: SettingManager.l2('stom'),
            7: SettingManager.l2('hosp'),
            8: SettingManager.l2('microbiology'),
            9: SettingManager.l2('citology'),
            10: SettingManager.l2('gistology'),
        }

    @staticmethod
    def is_morfology_enabled(en: dict):
        return bool(en.get(8)) or bool(en.get(9)) or bool(en.get(10))

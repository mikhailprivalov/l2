import simplejson
from django.core.cache import cache
from django.db.models.signals import post_save

import appconf.models as appconf


class SettingManager:
    WARMUP_TEST_KEY = 'SettingManager:test-warmup'
    LOC_MEM_CACHE = {}

    @staticmethod
    def warmup(place_in_locmem=False):
        cache.set(SettingManager.WARMUP_TEST_KEY, True, 1)

        if not cache.get(SettingManager.WARMUP_TEST_KEY):
            print('SettingManager: cache is disabled')  # noqa: T001

        post_save.disconnect(save_setting, sender=appconf.Setting)
        print('SettingManager: warming up')  # noqa: T001

        s: appconf.Setting
        for s in appconf.Setting.objects.all():
            SettingManager.get(s.name, rebuild=True, place_in_locmem=place_in_locmem)

        post_save.connect(save_setting, sender=appconf.Setting)

    @staticmethod
    def get(key, default=None, default_type='s', rebuild=False, place_in_locmem=False):
        no_cache = '#no-cache#' in key
        k = 'setting_manager_' + key
        if k in SettingManager.LOC_MEM_CACHE:
            return SettingManager.LOC_MEM_CACHE[k]
        cv = cache.get(k) if not no_cache and not rebuild else None
        if cv:
            SettingManager.LOC_MEM_CACHE[k] = simplejson.loads(cv)
            return SettingManager.LOC_MEM_CACHE[k]
        row = appconf.Setting.objects.filter(name=key).first()
        if not row:
            row = appconf.Setting.objects.create(name=key, value=key if default is None else default, value_type=default_type)
        value = row.get_value()
        if not no_cache:
            SettingManager.LOC_MEM_CACHE[k] = value
            cache.set(k, simplejson.dumps(value), 60 * 60 * 24)
        return value

    @staticmethod
    def l2(key):
        return SettingManager.get('l2_{}'.format(key), default='false', default_type='b')

    @staticmethod
    def l2_modules():
        return {
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
                ]
            },
            "consults_module": SettingManager.get("consults_module", default='false', default_type='b'),
            "directions_params": SettingManager.get("directions_params", default='false', default_type='b'),
            "morfology": SettingManager.is_morfology_enabled(SettingManager.en()),
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
            11: SettingManager.l2('forms'),
            12: SettingManager.get("directions_params", default='false', default_type='b'),
        }

    @staticmethod
    def is_morfology_enabled(en: dict):
        return bool(en.get(8)) or bool(en.get(9)) or bool(en.get(10))


def save_setting(sender, instance, **kwargs):
    SettingManager.warmup()


post_save.connect(save_setting, sender=appconf.Setting)

import appconf.models as appconf


class SettingManager:

    @staticmethod
    def get(key, default=None, default_type='s'):
        row = appconf.Setting.objects.filter(name=key).first()
        if not row:
            row = appconf.Setting.objects.create(name=key, value=key if default is None else default,
                                                 value_type=default_type)
        value = row.get_value()
        return value

    @staticmethod
    def l2(key):
        return SettingManager.get('l2_{}'.format(key), default='false', default_type='b')

    @staticmethod
    def l2_modules():
        return {'l2_{}'.format(x): SettingManager.l2(x) for x in [
            "cards_module",
            "fast_templates",
            "treatment",
            "stom",
            "hosp",
            "stat_btn",
        ]}

import appconf.models as appconf


class SettingManager:

    @staticmethod
    def get(key, default=None, default_type='s'):
        if appconf.Setting.objects.filter(name=key).exists():
            row = appconf.Setting.objects.get(name=key)
        else:
            row = appconf.Setting(name=key, value=key if default is None else default, value_type=default_type)
            row.save()
        value = row.get_value()
        return value

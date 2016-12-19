from debug_panel.cache import cache

import appconf.models as appconf


class SettingManager:

    @staticmethod
    def get(key):
        value = key
        #if not cache.get(key):
        if appconf.Setting.objects.filter(name=key).exists():
            row = appconf.Setting.objects.get(name=key)
            value = row.nval()
            #cache.set(key, value, 60*60*8)
        #else:
        #    value = cache.get(key)
        return value

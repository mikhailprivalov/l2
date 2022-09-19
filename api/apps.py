from django.apps import AppConfig
import posthog


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        from appconf.manager import SettingManager

        try:
            posthog_key = SettingManager.get('posthog_key')
            if posthog_key and posthog_key != 'posthog_key':
                posthog.api_key = posthog_key
        except:
            # ignore
            pass

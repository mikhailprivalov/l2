from django.apps import AppConfig

from laboratory.settings import DEPRECATED_RMQ_ENABLED


class MqConfig(AppConfig):
    name = 'mq'

    def ready(self):
        if DEPRECATED_RMQ_ENABLED:
            import mq.signals  # noqa: F401

from django.apps import AppConfig

from laboratory.settings import RMQ_ENABLED


class MqConfig(AppConfig):
    name = 'mq'

    def ready(self):
        if RMQ_ENABLED:
            import mq.signals

import logging

from django.utils.text import Truncator


class RequestDataFilter(logging.Filter):
    def filter(self, record):
        record.method = record.request.method
        record.path = record.request.path
        record.body = Truncator(record.request.body.decode()).chars(300)
        record.data = dict(record.request.GET if record.request.method == "GET" else record.request.POST)
        record.user = record.request.user.username if record.request.user.is_authenticated else 'GUEST'
        return True

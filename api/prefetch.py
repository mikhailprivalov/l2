import logging
import threading
# import time

import simplejson
from django.db import connections
from django.http import HttpRequest
from django.utils.module_loading import import_string

from laboratory.settings import PREFETCH_ENABLED, PREFETCH_MAX_THREADS


logger = logging.getLogger(__name__)

def prefetch(request, routes):
    if not PREFETCH_ENABLED:
        return '[]'

    maxthreads = PREFETCH_MAX_THREADS
    sema = threading.BoundedSemaphore(maxthreads)
    threads = list()

    result = {}

    def get_view_data(view_name, route):
        # print(f"--- {view_name} start ---")
        # start_time = time.time()
        sema.acquire()
        try:
            if '.' in view_name:
                parts = view_name.split('.')
                view = import_string(f'api.{parts[0]}.views.{parts[1]}')
            else:
                view = import_string(f'api.views.{view_name}')
            data = route.get('data', {})
            http_obj = HttpRequest()
            http_obj._body = simplejson.dumps(data)
            http_obj.user = request.user
            result[view_name] = {
                'url': route.get('url') or view_name,
                'params': data,
                'data': view(http_obj).getvalue(),
            }
        finally:
            sema.release()
        try:
            connections.close_all()
        except Exception as e:
            logger.exception(f"Error closing connections {e}")
        # print(f"--- {view_name}: {time.time() - start_time} seconds ---")

    for view_name in routes:
        result[view_name] = {}
        route = routes[view_name]
        thread = threading.Thread(target=get_view_data, args=(view_name, route))
        try:
            thread.start()
        except RuntimeError:
            threads.remove(thread)
        threads.append(thread)

    [t.join() for t in threads]

    return simplejson.dumps(list(result.values()))

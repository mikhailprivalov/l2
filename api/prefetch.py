import logging
import threading
# import time

import simplejson
from django.db import connections
from django.http import HttpRequest
from django.utils.module_loading import import_string

from api.researches.views import get_researches
from api.views import bases, current_user_info, departments, hospitals, directive_from
from laboratory.settings import PREFETCH_ENABLED, PREFETCH_MAX_THREADS


PRE_IMPORT = {
    'bases': bases,
    'departments': departments,
    'hospitals': hospitals,
    'directive_from': directive_from,
    'current_user_info': current_user_info,
    'researches.get_researches': get_researches,
}

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
            if view_name in PRE_IMPORT:
                view = PRE_IMPORT[view_name]
            elif '.' in view_name:
                parts = view_name.split('.')
                view = import_string(f'api.{parts[0]}.views.{parts[1]}')
            else:
                view = import_string(f'api.views.{view_name}')
            data = route.get('data', {})
            http_obj = HttpRequest()
            http_obj._body = simplejson.dumps(data) if data else '{}'
            http_obj.plain_response = True
            http_obj.user = request.user
            response = view(http_obj)
            result[view_name] = {
                'url': route.get('url') or view_name,
                'params': data,
                'data': response.getvalue() if hasattr(response, 'getvalue') else response,
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

    return simplejson.dumps(list(result.values()), separators=(',', ':'))

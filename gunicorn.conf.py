import multiprocessing

bind = '127.0.0.1:8000'
workers = multiprocessing.cpu_count() * 2 + 1
user = "user"
timeout = 3600

try:
    from laboratory.local_gunicorn import *
except ImportError:
    pass
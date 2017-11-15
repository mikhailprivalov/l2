import multiprocessing

bind = '127.0.0.1:8000'
workers = multiprocessing.cpu_count() * 1.5
timeout = 3600

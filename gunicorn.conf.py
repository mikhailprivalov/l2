import multiprocessing
import os

# Server socket
bind = '127.0.0.1:8000'
backlog = 2048

# Worker processes
workers = int(multiprocessing.cpu_count() * 2) + 1
worker_class = 'gevent'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeout settings
timeout = 300  # 5 minutes
keepalive = 5
graceful_timeout = 30

# Memory management
worker_tmp_dir = '/dev/shm'  # Use RAM for temp files

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'l2_gunicorn'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None

# Security
limit_request_line = 9086
limit_request_fields = 100
limit_request_field_size = 8190


# Performance tuning
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")


def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)


def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")

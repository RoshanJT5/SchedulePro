"""
Gunicorn Configuration File
Production-ready WSGI server configuration for AI Timetable Generator
"""
import multiprocessing
import os

# Server Socket
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:5000')
backlog = 2048

# Worker Processes
# Formula: (2 * CPU cores) + 1
workers = int(os.getenv('GUNICORN_WORKERS', (multiprocessing.cpu_count() * 2) + 1))
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'gthread')  # Options: sync, gthread, gevent, eventlet
threads = int(os.getenv('GUNICORN_THREADS', 4))  # Threads per worker (for gthread)
worker_connections = 1000  # Max simultaneous clients per worker

# Worker Lifecycle
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50  # Add randomness to max_requests to avoid all workers restarting at once
timeout = 120  # Workers silent for more than this many seconds are killed and restarted
graceful_timeout = 30  # Timeout for graceful workers restart
keepalive = 5  # Seconds to wait for requests on a Keep-Alive connection

# Process Naming
proc_name = 'ai_timetable_generator'

# Server Mechanics
daemon = False  # Don't daemonize (let systemd/Docker handle this)
pidfile = None  # Let systemd/Docker handle PID
umask = 0
user = None  # Run as current user (systemd will handle user switching)
group = None
tmp_upload_dir = None

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')  # '-' means stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')  # '-' means stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')  # debug, info, warning, error, critical
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4096  # Max size of HTTP request line in bytes
limit_request_fields = 100  # Max number of HTTP headers
limit_request_field_size = 8190  # Max size of HTTP header field

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'
# ssl_version = 'TLS'
# cert_reqs = 0
# ca_certs = None
# suppress_ragged_eofs = True
# do_handshake_on_connect = False
# ciphers = None

# Server Hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"Starting Gunicorn with {workers} workers and {threads} threads per worker")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading Gunicorn workers")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Gunicorn is ready. Listening on: {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    print("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    print("Server is ready. Spawning workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker received SIGABRT signal (pid: {worker.pid})")

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug(f"{req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker exited (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    print(f"Worker exit (pid: {worker.pid})")

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    print(f"Number of workers changed from {old_value} to {new_value}")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("Shutting down Gunicorn")

# Performance Tuning Notes:
# 
# Worker Class Options:
# - 'sync': Default, simple, one request at a time per worker
# - 'gthread': Threaded workers, good for I/O bound apps (RECOMMENDED)
# - 'gevent': Async workers using greenlets (requires gevent)
# - 'eventlet': Async workers using eventlet (requires eventlet)
# - 'tornado': Async workers using tornado (requires tornado)
#
# Recommended Settings by Use Case:
# 
# 1. CPU-Bound (Heavy computation):
#    workers = cpu_count
#    worker_class = 'sync'
#    threads = 1
#
# 2. I/O-Bound (Database, API calls) - CURRENT CONFIG:
#    workers = (cpu_count * 2) + 1
#    worker_class = 'gthread'
#    threads = 4
#
# 3. High Concurrency (Many simultaneous connections):
#    workers = cpu_count
#    worker_class = 'gevent'
#    worker_connections = 1000
#
# Memory Considerations:
# - Each worker uses ~50-100MB base memory
# - Monitor with: ps aux | grep gunicorn
# - Adjust workers if memory usage is high
# - Use max_requests to prevent memory leaks

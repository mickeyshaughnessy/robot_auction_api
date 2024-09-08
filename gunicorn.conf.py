import multiprocessing
from config import API_PORT

bind = f"0.0.0.0:{API_PORT}"
workers = multiprocessing.cpu_count() * 2 + 1
raw_env = ["FLASK_ENV=production"]
worker_class = "gevent"
timeout = 300
keepalive = 5
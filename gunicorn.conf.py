import ssl, multiprocessing
from config import API_PORT

#bind = ["0.0.0.0:80", "0.0.0.0:443"]
bind = [f"0.0.0.0:{API_PORT}"]
workers = multiprocessing.cpu_count() * 2 + 1

# SSL configuration
certfile = "/etc/letsencrypt/live/robotservicesauction.com/fullchain.pem"
keyfile = "/etc/letsencrypt/live/robotservicesauction.com/privkey.pem"
ssl_version = ssl.PROTOCOL_TLS
do_handshake_on_connect = False

# Set environment variable
raw_env = ["FLASK_ENV=production"]

# Other Gunicorn settings
worker_class = "gevent"
timeout = 300
keepalive = 5

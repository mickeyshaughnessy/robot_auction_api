import ssl, multiprocessing
import config 

#bind = ["0.0.0.0:80", "0.0.0.0:443"]
bind = ["0.0.0.0:%s" % config.API_PORT]
workers = multiprocessing.cpu_count() * 2 + 1

# SSL configuration
certfile = "/home/ubuntu/robot_auction_api/cert.pem"
keyfile = "/home/ubuntu/robot_auction_api/key.pem"
ssl_version = ssl.PROTOCOL_TLS
do_handshake_on_connect = False

# Set environment variable
raw_env = ["FLASK_ENV=production"]

# Other Gunicorn settings
worker_class = "gevent"
timeout = 300
keepalive = 5

# Gunicorn production configuration for AGRIFY
bind = "0.0.0.0:5000"
workers = 2
threads = 4
timeout = 120  # Extended to 120s to prevent gateway timeouts on Render/Cloud
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"

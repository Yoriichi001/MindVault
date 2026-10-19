import os

# Render dynamically passes the port via the PORT environment variable (default 10000)
port = os.environ.get('PORT', '10000')
bind = f"0.0.0.0:{port}"

# Optimize worker concurrency for Render free/starter tiers
workers = int(os.environ.get('WEB_CONCURRENCY', '1'))
threads = 2
timeout = 120
keepalive = 5
accesslog = '-'
errorlog = '-'

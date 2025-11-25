#!/bin/bash

# Levantar Redis en segundo plano
redis-server --daemonize yes

# Arrancar Gunicorn con Flask
gunicorn -w 2 -t 120 -b 0.0.0.0:5000 app:app &

# Arrancar Celery worker
celery -A app.celery worker --loglevel=info

chmod +x start.sh

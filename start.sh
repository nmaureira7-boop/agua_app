#!/bin/bash
gunicorn -w 2 -t 120 -b 0.0.0.0:$PORT app:app --access-logfile - --error-logfile -

#!/bin/bash

# Arrancar Gunicorn con Flask (tantos workers como CPUs disponibles)
gunicorn -w $(nproc) -t 120 -b 0.0.0.0:5000 app:app &

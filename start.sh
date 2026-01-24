#!/bin/bash
# start.sh - start Django with Gunicorn on Render
gunicorn Onlinebnk.wsgi --bind 0.0.0.0:$PORT

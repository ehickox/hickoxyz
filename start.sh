#!/bin/sh
gunicorn -c gunicorn_config.py server:app

#!/bin/bash
gunicorn --bind 0.0.0.0:5000 "server:create_app()"
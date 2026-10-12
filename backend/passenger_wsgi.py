"""Passenger WSGI entry point for MihanWebHost Python hosting.

In the host panel (Python App), point the WSGI file to this path and make
sure the venv Python version is >= 3.12 (Django 6.x requirement).
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from config.wsgi import application  # noqa: E402

APP_HOME = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_HOME)
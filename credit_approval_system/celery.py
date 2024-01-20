# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'credit_approval_system.settings')

# create a Celery instance and configure it using the settings from Django
app = Celery('credit_approval_system')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Discover and configure all task modules in your Django app
app.autodiscover_tasks()

# from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Задаём переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messages.settings')

app = Celery('messages')

# Используем настройки Django для конфигурации Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в приложениях Django
app.autodiscover_tasks()

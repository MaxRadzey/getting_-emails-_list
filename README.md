# Проект: Служба обработки электронной почты

## Содержание
- [Авторы](#авторы)
- [Описание](#описание)
- [Технологии](#технологии)
- [Как запустить проект](#Как-запустить-проект)

##  Авторы

- [Maxim Radzey](https://github.com/MaxRadzey)

##  Описание
Этот проект представляет собой сервис для автоматизированного получения и обработки электронных писем из различных почтовых серверов (Yandex, Gmail, Mail.ru).
Сервис подключается к почтовым серверам через протокол IMAP, получает непрочитанные письма, извлекает текст,
HTML-контент и вложенные файлы, сохраняет их в базу данных и отправляет уведомления клиентам через WebSocket.

## Технологии
- [Python 3.8+](https://www.python.org)
- [Django](https://docs.djangoproject.com/en/stable)
- Django Channels
- Celery
- Redis
- imaplib
- cryptography
- PostrgreSQL


### Как запустить проект:

Клонировать репозиторий:

```
git clone git@github.com:MaxRadzey/getting_emails_list.git
cd getting_emails_list
```
Установить зависимости
```
pip install poetry
poetry config virtualenvs.in-project true
poetry shell
poetry install
```

Создать файл .env и указать актуальные данные

```
POSTGRES_DB=messages
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

SUPERUSER_USERNAME=admin
SUPERUSER_EMAIL=admin@admin.ru
SUPERUSER_PASSWORD=admin

DB_NAME=messages
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY="django-insecure-+=59lvk(ld6_tq=m^#"
ALLOWED_HOSTS=127.0.0.1,localhost
DEBUG_VALUE=True

EMAIL_PASSWORD_ENCRYPTION_KEY='Сгенерировать-свой-секретный-ключ'
```

Применение миграций
Для инициализации базы данных выполните миграции:

```
python manage.py migrate
```

Для обработки фоновых задач необходимо запустить Celery

```
celery -A messages worker --loglevel=info
```

Запуск сервера Django

```
daphne -p 8000 messages.asgi:application
```

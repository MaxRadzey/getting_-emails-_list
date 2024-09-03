import imaplib
from email.header import decode_header
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
import time
from typing import TYPE_CHECKING
from datetime import datetime as dt

from channels.layers import get_channel_layer
from django.db import transaction
from asgiref.sync import async_to_sync
from celery import shared_task

from .models import MessageData, Email

if TYPE_CHECKING:
    from .models import Email


def decode_and_get_title(title):
    if not title:
        return '-----'
    try:
        return decode_header(title)[0][0].decode()
    except Exception:
        return title


def decode_and_get_email(email_from):
    if not email_from:
        return '-----'
    byte_or_str_email_from = decode_header(email_from)[-1][0]
    if not isinstance(byte_or_str_email_from, str):
        return byte_or_str_email_from.decode()
    return byte_or_str_email_from


def decode_and_get_text(message):
    text_content, html_content = '', ''
    attachments = []

    for part in message.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")

        # Получение текста и его декодироваине
        if content_type == "text/plain" and "attachment" not in content_disposition:
            text_content += part.get_payload(decode=True).decode(
                part.get_content_charset() or 'utf-8'
            )

        # Получение HTML и его декодирование
        elif content_type == "text/html" and "attachment" not in content_disposition:
            html_content += part.get_payload(decode=True).decode(
                part.get_content_charset() or 'utf-8'
            )

        # Получение вложений
        elif "attachment" in content_disposition or part.get_filename():
            filename = part.get_filename()
            if filename:
                # Декодирование вложения
                filename = decode_header(part.get_filename())[0][0].decode()
                attachments.append(
                    {'filename': filename}
                )

    return text_content, html_content, attachments


def connect_to_mail_server(email_login_data: 'Email'):
    """Функция подключения к почтовому сервису."""
    try:
        imap_server_map = {
            'YANDEX': 'imap.yandex.ru',
            'GMAIL': 'imap.gmail.com',
            'MAILRU': 'imap.mail.ru'
        }
        host = imap_server_map.get(email_login_data.provider)
        if not host:
            raise ValueError(f'Неверный потчовый индекс {host}')

        # Подключение к почтновому сервису
        imap = imaplib.IMAP4_SSL(host=host)
        imap.login(email_login_data.email, email_login_data.password)
        imap.select('INBOX')
        return imap

    except Exception as err:
        print(f'Ошибка подключения к почтовому серверу: {err}')
        return None


def get_mail_list(imap):
    """Функция получения списка писем."""
    try:
        status, messages_count = imap.search(None, 'ALL')
        if status == 'OK':
            return messages_count[0].split()
        return []

    except Exception as err:
        print(f'Ошибка получения списка писем {err}')


def get_mail_data(imap, num, email_login_data):
    """Функция получения данных из письма."""
    try:
        time.sleep(2)
        # Получение данных из сообщения
        _, message_data = imap.fetch(num, '(RFC822)')

        # Проверка, что получены данные из письма
        if not message_data or not message_data[0]:
            raise ValueError('Ошибка получения данных письма')
        msg = message_data[0][1]

        message = BytesParser().parsebytes(msg)

        title = decode_and_get_title(message.get('subject'))
        sent_date = parsedate_to_datetime(message.get('date'))
        email_from = decode_and_get_email(message.get('from'))
        text, html, files = decode_and_get_text(message)
        uid = num.decode('utf-8')

        data_msg = {
            "email": email_login_data,
            'email_from': email_from,
            "title": title,
            "dispatch_date": sent_date,
            "receipt_date": dt.now(),
            "text": text if text else html,
            "msg_read": True,
            "files": files,
            "uid": uid,
        }
    except Exception as err:
        print(f'Ошибка обратотки пиьсма {err}')
    return data_msg


def save_data_in_db(data_msg):
    """Функция сохранения письма в БД через транзакцию."""
    try:
        email_message = MessageData(**data_msg)

        with transaction.atomic():
            email_message.save()
    except Exception as err:
        print(f'Ошибка сохранения пиьсма {err}')
    return email_message


async def send_email_by_websocket(email_message):
    """Отправка данных письма клиенту через WebSocket."""
    try:
        channel_layer = get_channel_layer()
        email_data = {
            'email_from': email_message.email_from,
            'title': email_message.title[:50],
            'dispatch_date': (
                email_message.dispatch_date.strftime('%Y-%m-%d %H:%M:%S')
            ),
            'receipt_date': (
                email_message.receipt_date.strftime('%Y-%m-%d %H:%M:%S')
            ),
            'text': email_message.text[:50],
            'files': email_message.files,
        }

        # Отправляем сообщение в группу вебсокет
        await channel_layer.group_send(
            'new_mail_goup',
            {
                'type': 'send_email',
                'email_data': email_data
            }
        )
    except Exception as err:
        print(f'Ошибка отправки данных клиенту: {err}')


async def progress_bar(mail_list, counter):
    try:
        channel_layer = get_channel_layer()
        message_count = len(mail_list)

        # Подсчет количества сообщений
        await channel_layer.group_send(
            'new_mail_goup',
            {
                'type': 'upadate_progress',
                'progress': {
                    'count': counter + 1,
                    'total_messages': message_count
                }
            }
        )
    except Exception as err:
        print(f'Ошибка прогресс-бара {err}')


@shared_task
def get_data_and_send_to_ws(email_id):
    i = 0
    email_account = Email.objects.get(id=email_id)
    imap = connect_to_mail_server(email_account)

    if not imap:
        return

    mail_list = get_mail_list(imap)

    for num in mail_list:
        data_msg = get_mail_data(imap, num, email_account)
        if not MessageData.objects.filter(uid=num.decode('utf-8')).exists():
            email_message = save_data_in_db(data_msg)
            async_to_sync(send_email_by_websocket)(email_message)
            async_to_sync(progress_bar)(mail_list, i)
            i = i + 1

    imap.logout()

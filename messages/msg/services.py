import imaplib
import time
from datetime import datetime as dt
from email.header import decode_header
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from typing import Optional, Dict, Any, List, Tuple

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.core.files.base import ContentFile
from django.db import transaction

from .models import Email, MessageData, MessageFile


def decode_and_get_title(
        title: Any | None
        ) -> str:
    """
    Декодирует заголовок письма, если он закодирован,
    и возвращает его в виде строки.

    Функция пытается декодировать заголовок письма,
    который может быть закодирован с использованием MIME-формата.
    Если заголовок отсутствует, возвращает строку '-----'.
    В случае возникновения ошибки при декодировании, функция
    возвращает исходный заголовок.

    Args:
        title (Any | None): Заголовок письма в виде строки. Может быть
          закодированным MIME-заголовком или обычной строкой.

    Returns:
        str: Декодированный заголовок письма, либо '-----' если заголовок
          отсутствует, либо исходный заголовок в случае ошибки.
    """
    if not title:
        return '-----'
    try:
        return decode_header(title)[0][0].decode()
    except Exception:
        return title


def decode_and_get_email(
        email_from: Any | None
        ) -> str:
    """
    Декодирует почту отправителя, если она закодирована.

    Функция принимает почту отправителя, и декодирует его, если он закодирован
    в формате MIME. Если заголовок пустой, функция возвращает строку '-----'.
    Если в виде строки, он возвращается без изменений.

    Args:
        email_from (Any | None):  Почта отправителя. Может быть
        как закодированным в формате MIME, так и обычной строкой.

    Returns:
        str: Декодированная почта отправителя, либо '-----',
        если почта отсутствует. Если почта уже представлена в виде строки,
        возвращается она без изменений.
    """
    if not email_from:
        return '-----'
    byte_or_str_email_from = decode_header(email_from)[-1][0]
    if not isinstance(byte_or_str_email_from, str):
        return byte_or_str_email_from.decode()
    return byte_or_str_email_from


def decode_and_get_text(
        message
        ) -> tuple:
    """
    Декодирование данных письма (текст, HTML-контент, файлы).

    Функция принимает экземпляр 'message', представляющий собой MIME-сообщение
    и извлекает из него текстовый и HTML-контент, а также файлы вложений.
    текст, HTML-контент, файлы в формате MIME. Для каждого текстового и
    HTML-содержимого происходит декодирование с использованием
    указанной кодировки. Вложения извлекаются и декодируются, после чего
    сохраняются в виде списка словарей.

    Args:
        message (email.message.Message): Экземпляр сообщения, из которого
        извлекаются и декодируются данные.

    Returns:
        tuple: Кортеж, содержащий:
            - text_content (str): Декодированный текстовый контент письма.
            - html_content (str): Декодированный HTML-контент письма.
            - files_list (list of dict): Список словарей, каждый из которых
              содержит информацию о файле-вложении.
            - filename (str or None): Имя последнего найденного файла-вложения
              (может быть None, если вложений нет).
            - file_data (bytes or None): Декодированные данные последнего
              найденного файла-вложения (может быть None, если вложений нет).
    """
    text_content, html_content = '', ''
    files_list = []
    filename, file_data = None, None

    for part in message.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")

        # Получение текста и его декодироваине
        if (content_type == "text/plain"
                and "attachment" not in content_disposition):
            text_content += part.get_payload(decode=True).decode(
                part.get_content_charset() or 'utf-8'
            )

        # Получение HTML и его декодирование
        elif (content_type == "text/html"
                and "attachment" not in content_disposition):
            html_content += part.get_payload(decode=True).decode(
                part.get_content_charset() or 'utf-8'
            )

        # Получение вложений
        elif "attachment" in content_disposition or part.get_filename():
            filename = part.get_filename()
            if filename:
                # Декодирование вложения
                filename = decode_header(part.get_filename())[0][0].decode()
                file_data = part.get_payload(decode=True)
                files_list.append(
                    {'filename': filename}
                )

    return text_content, html_content, files_list, filename, file_data


def connect_to_mail_server(
        email_account: 'Email'
        ) -> imaplib.IMAP4_SSL | None:
    """
    Подключается к почтовому сервису с использованием учетных данных
    пользователя.

    Функция принимает данные для входа в почтовый сервис и устанавливает
    соединение с почтовым сервером через протокол IMAP. В зависимости от
    провайдера почтового сервиса (например, Yandex, Gmail, Mail.ru)
    используется соответствующий IMAP-сервер.
    Если соединение успешно, возвращается объект IMAP-соединения. В случае
    ошибки подключения возвращается None.

    Args:
        email_account (Email): Объект, содержащий данные для входа в почтовый
        сервис, включая email, пароль и провайдера почты.

    Returns:
        imaplib.IMAP4_SSL or None: Объект IMAP-соединения в случае успешного
        подключения или None в случае ошибки.

    Raises:
        ValueError: Если провайдер почтового сервиса не поддерживается или
        указан неверно.
        Exception: Если возникает ошибка при подключении к почтовому серверу.
    """
    try:
        imap_server_map = {
            'YANDEX': 'imap.yandex.ru',
            'GMAIL': 'imap.gmail.com',
            'MAILRU': 'imap.mail.ru'
        }

        host = imap_server_map.get(email_account.provider)

        if not host:
            raise ValueError(f'Неверный потчовый индекс {host}')

        # Подключение к почтновому сервису
        imap = imaplib.IMAP4_SSL(host=host)
        decode_password = email_account.get_password()
        imap.login(email_account.email, decode_password)
        imap.select('INBOX')
        return imap

    except Exception as err:
        print(f'Ошибка подключения к почтовому серверу: {err}')
        return None


def get_mail_list(imap: imaplib.IMAP4_SSL) -> List[bytes]:

    """
    Получает список всех писем из почтового ящика.

    Функция подключается к почтовому ящику через IMAP и выполняет поиск писем,
    используя команду `search`. По умолчанию функция возвращает список всех
    непрочитанных писем в ящике. Возвращаемое значение — это список уникальных
    идентификаторов писем (UID). Если возникает ошибка при получении писем,
    функция возвращает пустой список.

    Args:
        imap (imaplib.IMAP4_SSL): Активное IMAP-соединение с почтовым ящиком.

    Returns:
        list: Список UID (уникальных идентификаторов) всех писем в почтовом
        ящике, если запрос выполнен успешно. В случае ошибки возвращается
        пустой список.

    Raises:
        Exception: Если возникает ошибка при выполнении команды поиска писем.
    """
    try:
        # status, messages_count = imap.search(None, 'ALL')
        status, messages_count = imap.search(None, 'UNSEEN')
        if status == 'OK':
            return messages_count[0].split()
    except Exception as err:
        print(f'Ошибка получения списка писем {err}')
    return []


def get_mail_data(
        imap: imaplib.IMAP4_SSL,
        num: bytes,
        email_account: 'Email'
        ) -> Tuple[Dict[str, Any], Optional[str], Optional[bytes]]:
    """
    Извлекает и обрабатывает данные из письма, подключенного через IMAP.

    Функция получает данные из указанного письма, идентифицируемого его
    уникальным номером `num`, используя активное IMAP-соединение.
    После извлечения данных из сообщения, функция декодирует заголовок,
    дату отправки, адрес отправителя, текст,
    HTML-контент и вложенные файлы. Возвращает словарь с данными письма и
    информацию о вложениях.

    Args:
        imap (imaplib.IMAP4_SSL): Активное IMAP-соединение с почтовым ящиком.
        num (bytes): Уникальный идентификатор (UID) письма,
          используемый для его извлечения.
        email_account (Email): Экземпляр модели почтового аккаунта,
          с которого получено письмо.

    Returns:
        tuple: Кортеж, содержащий:
            - data_msg (dict): Словарь с данными письма,
              включая заголовок, отправителя, дату отправки,
              текст/HTML контент, статус прочтения, список файлов и UID письма.
            - file_name (str or None): Имя последнего найденного
              файла-вложения (может быть None, если вложений нет).
            - file_data (bytes or None): Декодированные данные последнего
              найденного файла-вложения (может быть None, если вложений нет).

    Raises:
        ValueError: Если не удается получить данные из письма.
        Exception: Если возникает ошибка при обработке данных письма.
    """
    try:
        time.sleep(2)
        # Получение данных из сообщения
        num_str = num.decode('utf-8')
        _, message_data = imap.fetch(num_str, '(RFC822)')

        # Проверка, что получены данные из письма
        if not message_data or not message_data[0]:
            raise ValueError('Ошибка получения данных письма')
        msg = message_data[0][1]

        if isinstance(msg, (bytes, bytearray)):
            message = BytesParser().parsebytes(msg)

        title = decode_and_get_title(message.get('subject'))
        sent_date = parsedate_to_datetime(message.get('date'))
        email_from = decode_and_get_email(message.get('from'))
        text, html, files, file_name, file_data = decode_and_get_text(message)
        uid = num.decode('utf-8')

        data_msg = {
            "email": email_account,
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
    return data_msg, file_name, file_data


def save_data_in_db(
        data_msg: Dict[str, Any],
        file_name: Optional[str],
        file_data: Optional[bytes]
        ) -> 'MessageData':
    """
    Сохраняет данные письма и вложения в базу данных с
    использованием транзакции.

    Функция принимает данные письма, создает объект модели `MessageData`
    и сохраняет его в базе данных. Если письмо содержит вложение, оно
    сохраняется как объект `MessageFile`, связанный с письмом.
    Операции выполняются в рамках транзакции для обеспечения
    целостности данных.

    Args:
        data_msg (Dict[str, Any]): Словарь с данными письма, которые будут
          использованы для создания объекта `MessageData`.
        file_name (Optional[str]): Имя файла-вложения. Может быть `None`,
          если вложений нет.
        file_data (Optional[bytes]): Декодированные данные файла-вложения.
          Может быть `None`, если вложений нет.

    Returns:
        MessageData: Экземпляр модели `MessageData`, представляющий
          сохраненное письмо.

    Raises:
        Exception: Если возникает ошибка при сохранении данных в базу данных.
    """
    try:
        email_message = MessageData(**data_msg)

        with transaction.atomic():
            email_message.save()

        if file_data:
            email_files = MessageFile(message=email_message)
            email_files.file.save(file_name, ContentFile(file_data))
            email_files.save()

    except Exception as err:
        print(f'Ошибка сохранения пиьсма {err}')
    return email_message


async def send_email_by_websocket(
        email_message: 'MessageData'
        ) -> None:
    """
    Асинхронная отправка данных письма клиенту через WebSocket.

    Функция извлекает необходимые данные из экземпляра `MessageData`
    и отправляет их клиенту через WebSocket соединение. Данные включают
    информацию о отправителе, заголовке письма, дате отправки и получения,
    тексте письма и файлах вложений.
    Сообщение отправляется в определенную группу WebSocket.

    Args:
        email_message (MessageData): Экземпляр модели `MessageData`,
          содержащий данные письма для отправки.

    Returns:
        None: Функция не возвращает значения.

    Raises:
        Exception: Если возникает ошибка при отправке данных через WebSocket.
    """
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


async def progress_bar(
        mail_list: List[bytes],
        counter: int
        ) -> None:
    """
    Асинхронная функция для обновления прогресс-бара
    в реальном времени через WebSocket.

    Функция принимает список сообщений и текущий счетчик обработанных
    сообщений, рассчитывает общий прогресс и отправляет данные о текущем
    состоянии прогресс-бара через WebSocket. Эти данные включают количество
    уже обработанных сообщений и общее количество сообщений.

    Args:
        mail_list (List[bytes]): Список уникальных идентификаторов (UID)
        сообщений, которые нужно обработать.
        counter (int): Текущий счетчик обработанных сообщений.

    Returns:
        None: Функция не возвращает значения.

    Raises:
        Exception: Если возникает ошибка при отправке данных через WebSocket.
    """
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
def get_data_and_send_to_ws(
    email_id: int
        ) -> None:
    """
    Задача Celery для получения данных писем и отправки их через WebSocket.

    Эта задача выполняет следующие действия:
    1. Подключается к почтовому серверу с использованием учетных данных,
      связанных с `email_id`.
    2. Получает список всех писем из почтового ящика.
    3. Для каждого письма, начиная с самого последнего, извлекает его данные и
      сохраняет их в базе данных.
    4. Если письмо еще не существует в базе данных (определяется по UID),
      данные сохраняются, и информация о письме
       отправляется клиенту через WebSocket.
    5. Обновляет прогресс-бар в реальном времени через WebSocket.
    6. После обработки всех писем происходит отключение от почтового сервера.

    Args:
        email_id (int): Идентификатор почтового аккаунта, для которого
          необходимо получить письма.

    Returns:
        None: Функция не возвращает значения. Все результаты операции
          сохраняются в базе данных и отправляются клиенту через WebSocket.

    Raises:
        Exception: Если возникает ошибка при выполнении
          любого из этапов задачи.
    """
    i = 0
    email_account = Email.objects.get(id=email_id)
    imap = connect_to_mail_server(email_account)

    if not imap:
        return

    mail_list = get_mail_list(imap)

    for num in mail_list[::-1]:
        data_msg, file_name, file_data = get_mail_data(
            imap, num, email_account
        )
        if not MessageData.objects.filter(uid=num.decode('utf-8')).exists():
            email_message = save_data_in_db(data_msg, file_name, file_data)
            async_to_sync(send_email_by_websocket)(email_message)
            async_to_sync(progress_bar)(mail_list, i)
            i = i + 1

    imap.logout()

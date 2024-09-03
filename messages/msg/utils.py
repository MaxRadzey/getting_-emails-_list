from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .constants import ALLOWED_DOMAINS


@deconstructible
class EmailDomenValidator:
    """
    Кастомный валидатор доменов почты.

    Этот валидатор проверяет что почта удовлетворяет разрешенным доменам.
    """

    error_msg = f"""Недопустимый домен. Разрешены только следующие
    домены: {', '.join(ALLOWED_DOMAINS)}."""

    def __call__(self, email: str) -> None:
        """
        Основной метод, который выполняет проверку имени.

        Валидирует почту, проверяет на
        соответствие разрешенным доменам.

        Args:
            email (str): Почта.

        Raises:
            ValidationError: Если значение не удовлетворяет требованиям.
        """
        domain = email.split('@')[-1]
        if domain not in ALLOWED_DOMAINS:
            raise ValidationError(self.error_msg)


# async def get_email_data(email_login_data: 'Email'):

#     imap_server_map = {
#         'yandex': 'imap.yandex.ru',
#         'gmail': 'imap.gmail.com',
#         'mail': 'imap.mail.ru'
#     }
#     host = imap_server_map.get(email_login_data.provider)
#     if not host:
#         raise ValueError('Неверный потчовый индекс')

#     # Подключение к почтновому сервису
#     imap = imaplib.IMAP4_SSL(host=host)
#     imap.login(email_login_data.email, email_login_data.password)
#     imap.select('INBOX')  # ('OK', [b'19'])

#     # Получение количество вхлдящих сообщений
#     _, messages_count = imap.search(None, 'ALL')  # ('OK', [b'1 2 3 4 ... 10'])

#     for num in messages_count[0].split():
#         time.sleep(2)
#         # Получение данных из сообщения
#         _, message_data = imap.fetch(num, '(RFC822)')

#         # Проверка, что получены данные из письма
#         if not message_data or not message_data[0]:
#             raise ValueError('Ошибка получения данных письма')
#         msg = message_data[0][1]

#         # Создание экземпляра парсера
#         message = BytesParser().parsebytes(msg)

#         title = message.get('subject')
#         title = (
#             decode_header(title)[0][0].decode()
#             if title else 'Заголовок отсутствует'
#         )
#         sent_date = parsedate_to_datetime(message.get('date'))
#         email_from = message.get('from')
#         byte_or_str_email_from = (
#             decode_header(email_from)[-1][0] if email_from else None
#         )
#         email_from = (
#             byte_or_str_email_from.decode()
#             if not isinstance(byte_or_str_email_from, str)
#             else byte_or_str_email_from
#         )

#         text_content, html_content = '', ''
#         attachments = []

#         # Получение текста и вложений
#         for part in message.walk():
#             content_type = part.get_content_type()
#             content_disposition = part.get("Content-Disposition", "")

#             # Получчение текста и его декодирвоаине
#             if content_type == "text/plain" and "attachment" not in content_disposition:
#                 text_content += part.get_payload(decode=True).decode(
#                     part.get_content_charset() or 'utf-8'
#                 )
#             # Получение HTML и его декодирование
#             elif content_type == "text/html" and "attachment" not in content_disposition:
#                 html_content += part.get_payload(decode=True).decode(
#                     part.get_content_charset() or 'utf-8'
#                 )

#             # Получение вложений
#             elif "attachment" in content_disposition or part.get_filename():
#                 filename = part.get_filename()
#                 if filename:
#                     # Декодирование вложения
#                     file_data = part.get_payload(decode=True)
#                     attachments.append(
#                         {'filename': filename, 'data': file_data}
#                     )

#         data_msg = {
#             "email": email_from,
#             "title": title,
#             "dispatch_date": sent_date,
#             "receipt_date": dt.now(),
#             "text": [text_content, html_content],
#             "msg_read": True,
#             "files": attachments,
#         }  # Словарь данных к сохранению в БД

#         email_message = Email(**data_msg)

#         # Сохранение в БД через транзакцию
#         with transaction.atomic():
#             email_message.save()

#         await send_email_via_websocket(email_message)

#     imap.logout()

#     return data_msg

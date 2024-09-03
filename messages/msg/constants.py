YANDEX = 'YANDEX'
MAILRU = 'MAILRU'
GMAIL = 'GMAIL'
EMAIL_CHOICES = (
    (YANDEX, 'yandex.ru'),
    (MAILRU, 'mail.ru'),
    (GMAIL, 'gmail.com'),
)
EMAIL_DICKT = {
    'YANDEX': 'yandex.ru',
    'MAILRU': 'mail.ru',
    'GMAIL': 'gmail.com',
}
ALLOWED_DOMAINS = ('yandex.ru', 'gmail.com', 'mail.ru',)
MAX_PASSWORD_LEGTH = 128
MAX_TITLE_LEGTH = 256
MAX_EMAIL_LEGTH = 256

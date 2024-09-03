from django.db import models

from .base import BaseModel
from .constants import (EMAIL_CHOICES, MAX_PASSWORD_LEGTH, MAX_TITLE_LEGTH,
                        YANDEX, MAX_EMAIL_LEGTH)
from .utils import EmailDomenValidator


class Email(BaseModel):
    """Модель почты."""

    email = models.EmailField(
        'Почта', unique=True, validators=(EmailDomenValidator(),),
        max_length=MAX_EMAIL_LEGTH,
    )
    password = models.CharField(
        'Пароль', max_length=MAX_PASSWORD_LEGTH,
    )
    provider = models.CharField(
        'Провайдер почты', choices=EMAIL_CHOICES, default=YANDEX,
    )

    class Meta:
        verbose_name = 'Почта'
        verbose_name_plural = 'Почты'
        ordering = ('created_at',)

    def __str__(self) -> str:
        return f'{self.email}'


class MessageData(BaseModel):
    """Модель данных с почты."""

    email = models.ForeignKey(
        Email, on_delete=models.CASCADE,
        verbose_name='Почта',
        related_name='email_data',
    )
    email_from = models.CharField(
        'Отправитель', null=True
    )
    title = models.CharField(
        'Тема сообщения', null=True
    )
    dispatch_date = models.DateField(
        'Дата отправки',
    )
    receipt_date = models.DateField(
        'Дата получения',
    )
    text = models.TextField(
        'Текст сообщения', null=True
    )
    msg_read = models.BooleanField(
        'Письмо прочитано да/нет', default=False,
    )
    files = models.JSONField(
        'Прикрепленные файлы', blank=True, null=True
    )
    uid = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = 'Данные из письма'
        verbose_name_plural = 'Данные из писем'
        ordering = ('created_at',)

    def __str__(self) -> str:
        return f'{self.title}'


# class MessageFile(BaseModel):

#     message = models.ForeignKey(
#         MessageData, on_delete=models.CASCADE,
#         verbose_name='Прикрепленные файлы',
#         related_name='email_files',
#     )
#     file = models.FileField()

#     class Meta:
#         verbose_name = 'Файл'
#         verbose_name_plural = 'Файлы'
#         ordering = ('created_at',)

#     def __str__(self) -> str:
#         return f'Автор: {self.message} - {self.created_at}'

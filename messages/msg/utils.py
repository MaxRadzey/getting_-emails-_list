from pathlib import Path
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .constants import ALLOWED_DOMAINS

if TYPE_CHECKING:
    from .models import MessageFile


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


def mail_directory_path(instance: "MessageFile", file_name: str) -> Path:
    """
    Создает путь до файла договора или фотографии паспорта.

    Возвращает путь для сохранения файла из пиьсма,
    которые загружаются в папку MEDIA_ROOT/<mail_name>/<filename>.

    Args:
        instance (str): Экземпляр модели.
        file_name (str): Имя загружаемого файла.

    Returns:
        path (Path): Возвращает объект Path с путем загрузки документа
        в формате <mail_name>/<filename>.
    """
    email_name_list = instance.message.email.email.split('@')
    mail_name = email_name_list[0] + '-' + email_name_list[-1]
    return Path(f"{mail_name}/{file_name}")

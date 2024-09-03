from django.db import models


class BaseModel(models.Model):
    """Абстракная модель."""

    created_at = models.DateTimeField(
        'Дата создания записи', auto_now_add=True,
    )

    class Meta:
        abstract = True

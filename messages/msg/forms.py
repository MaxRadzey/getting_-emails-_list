from django import forms
from django.core.exceptions import ValidationError

from .constants import ALLOWED_DOMAINS, EMAIL_DICKT
from .models import Email


class EmailForm(forms.ModelForm):
    """Форма, для добавления потчы."""

    class Meta:
        model = Email
        fields = ('email', 'password', 'provider',)

    def clean_email(self):
        """Валидатор доменов почты в форме."""
        email = self.cleaned_data['email']
        domain = email.split('@')[-1]

        if domain not in ALLOWED_DOMAINS:
            raise ValidationError(
                f"""Разрешены только следующие домены:
                {', '.join(ALLOWED_DOMAINS)}."""
            )
        return email

    def clean(self):
        email = self.cleaned_data['email']
        email_domain = email.split('@')[-1]
        form_provider = self.cleaned_data['provider']
        form_provider = EMAIL_DICKT[form_provider]
        if email_domain != form_provider:
            raise ValidationError(
                'Введенный email должен соответствовать выбранному домену!'
            )

from threading import Thread

from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.generic import CreateView

from .forms import EmailForm
from .models import Email, MessageData
from .services import get_data_and_send_to_ws


def async_process_emails_in_background(email_account):
    thread = Thread(target=get_data_and_send_to_ws, args=(email_account,))
    thread.daemon = True
    thread.start()


class AddMailCreateView(CreateView):
    """Класс представления для добавления почты."""

    model = Email
    form_class = EmailForm
    template_name = 'msg/add_mail.html'

    def get_success_url(self):
        return reverse('msg:add_mail')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_accounts'] = Email.objects.all()
        return context


def get_emails(request, email):
    """Функция представления списка писем."""
    template = 'msg/get_data.html'
    account = get_object_or_404(Email, email=email)
    messages = MessageData.objects.filter(
        email=account
    ).order_by('-receipt_date')
    context = {
        'mail_to': email,
        'messages': messages
    }
    get_data_and_send_to_ws.delay(account.id)
    return render(request, template, context)

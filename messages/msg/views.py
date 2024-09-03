from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.forms import BaseModelForm
from django.http import HttpResponse
from asgiref.sync import async_to_sync
from threading import Thread

from django.urls import reverse
from django.views.generic import (
    CreateView,
)

from .models import Email, MessageData
from .forms import EmailForm
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

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        response = super().form_valid(form)
        # get_data_and_send_to_ws.delay(self.object.id)
        return response

    def get_success_url(self, **kwargs):
        return reverse(
            'msg:get_data',
            kwargs={'email': self.object.email}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email_accounts'] = Email.objects.all()
        return context


def get_emails(request, email):
    template = 'msg/get_data.html'
    # account = Email.objects.get(email=email)
    account = get_object_or_404(Email, email=email)
    messages = MessageData.objects.filter(
        email=account
    )
    context = {
        'mail_to': email,
        'messages': messages
    }
    return render(request, template, context)


# def fetch_messages(request, email):
#     email_account = get_object_or_404(Email, email=email)
#     get_data_and_send_to_ws.delay(email_account.id)
#     return redirect(f'/get-data/{email}', email=email)

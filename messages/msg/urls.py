from django.urls import path

from . import views

app_name = 'msg'

urlpatterns = [
    path(
        'add-mail/',
        views.AddMailCreateView.as_view(),
        name='add_mail'
    ),
    path(
        'get-data/<str:email>/',
        views.get_emails,
        name='get_data'
    ),
]

from django.contrib import admin

from .models import Email, MessageData, MessageFile


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "password",
        "provider",
    )
    search_fields = ("email",)
    list_filter = ("email",)


@admin.register(MessageData)
class MessageDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "email_from",
        "title",
        "dispatch_date",
        "receipt_date",
        "text",
        "msg_read",
        "files",
    )
    search_fields = ("email",)
    list_filter = ("email",)


@admin.register(MessageFile)
class MessageFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "message",
        "file",
    )
    search_fields = ("message",)
    list_filter = ("message",)

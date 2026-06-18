from django.contrib import admin

from .models import Client, Message, Mailing, MailingLog


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("email", "last_name", "first_name", "comment",)
    search_fields = ("email", "last_name", "first_name",)
    list_filter = ("last_name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject",)
    search_fields = ("subject", "body")
    list_filter = ("subject",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time", "status", "message")
    list_filter = ("status", "start_time")
    filter_horizontal = ("recipients",)


@admin.register(MailingLog)
class MailingLogAdmin(admin.ModelAdmin):
    list_display = ("mailing", "recipient", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("recipient__email", "mailing__id")
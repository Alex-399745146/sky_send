from django.contrib import admin

from .models import Client, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "email", "comment",)
    search_fields = ("last_name", "first_name", "email",)
    list_filter = ("last_name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject",)
    search_fields = ("subject", "body")
    list_filter = ("subject",)
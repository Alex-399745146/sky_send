# clients/views.py
from django.shortcuts import render

from .models import Client, Mailing


def home(request):
    total_mailings = Mailing.objects.count()
    active_mailings = Mailing.objects.filter(status=Mailing.STATUS_RUNNING).count()
    unique_recipients = Client.objects.count()  # если клиент может быть в нескольких рассылках

    active_status_label = dict(Mailing.STATUS_CHOICES)[Mailing.STATUS_RUNNING]

    context = {
        "total_mailings": total_mailings,
        "active_mailings": active_mailings,
        "unique_recipients": unique_recipients,
        "active_status_label": active_status_label,
    }
    return render(request, "clients/home.html", context)

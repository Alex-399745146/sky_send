# clients/views.py
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db import models
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


class ClientCreateView(LoginRequiredMixin, CreateView):
    """ Создание карточки клиента """
    model = Client
    fields = ["email", "first_name", "last_name", "comment"]
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")


class ClientListView(LoginRequiredMixin, ListView):
    """ Чтение карточек клиентов, всего списка """
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")  # поисковый запрос пользователя
        if q:
            qs = qs.filter(
                models.Q(email__icontains=q)
                | models.Q(first_name__icontains=q)
                | models.Q(last_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class ClientDetailView(LoginRequiredMixin, DetailView):
    """ Чтение карточки клиента, детальное """
    model = Client
    template_name = "clients/client_detail.html"
    context_object_name = "client"


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """ Редактирование карточек клиентов """
    model = Client
    fields = ["email", "first_name", "last_name", "comment"]
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """ Удаление карточки клиента """
    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("clients:client_list")
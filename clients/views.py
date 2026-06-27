# clients/views.py

from django.views import View
from django.db import models, transaction
from django.db.models import Count, Q
from django.db.models import Count, Q, FloatField, ExpressionWrapper
from .models import Client, Mailing, Message, MailingLog
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.utils import timezone



def home(request):
    """Функция передачи инфы в контексте для главной страницы"""
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


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
                user.is_superuser or user.groups.filter(name="manager").exists()
        )


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


class ClientUpdateView(ManagerRequiredMixin, LoginRequiredMixin, UpdateView):
    """ Редактирование карточек клиентов """
    model = Client
    fields = ["email", "first_name", "last_name", "comment"]
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("clients:client_list")


class ClientDeleteView(ManagerRequiredMixin, LoginRequiredMixin, DeleteView):
    """ Удаление карточки клиента """
    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("clients:client_list")


class MessageListView(LoginRequiredMixin, ListView):
    """ Чтение всех сообщений """
    model = Message
    template_name = "clients/message_list.html"
    context_object_name = "messages"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                models.Q(subject__icontains=q) |
                models.Q(body__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class MessageDetailView(LoginRequiredMixin, DetailView):
    """ Чтение конкретного сообщения """
    model = Message
    template_name = "clients/message_detail.html"
    context_object_name = "message"


class MessageCreateView(LoginRequiredMixin, CreateView):
    """ Создание сообщения(как объект класса) """
    model = Message
    fields = ["subject", "body"]
    template_name = "clients/message_form.html"
    success_url = reverse_lazy("clients:message_list")


class MessageUpdateView(ManagerRequiredMixin, LoginRequiredMixin, UpdateView):
    """ Редактирование сообщения """
    model = Message
    fields = ["subject", "body"]
    template_name = "clients/message_form.html"
    success_url = reverse_lazy("clients:message_list")


class MessageDeleteView(ManagerRequiredMixin, LoginRequiredMixin, DeleteView):
    """ Удаление сообщения """
    model = Message
    template_name = "clients/message_confirm_delete.html"
    success_url = reverse_lazy("clients:message_list")


class MailingForm(LoginRequiredMixin, forms.ModelForm):
    """ Форма для создания и редактирования рассылки с выбором получателей """

    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "recipients"]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"}
            ),
            "message": forms.Select(attrs={"class": "form-select"}),
            "recipients": forms.CheckboxSelectMultiple(attrs={"class": "ss-recipient-checkbox"}),
        }


class MailingListView(LoginRequiredMixin, ListView):
    """ Представление для списка всех рассылок пользователя """

    model = Mailing
    template_name = "clients/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("message")
            .prefetch_related("recipients")
            .annotate(
                total_recipients=Count("recipients", distinct=True),
                success_logs=Count(
                    "logs",
                    filter=Q(logs__status=MailingLog.STATUS_SUCCESS),
                    distinct=True,
                ),
            )
        )

        # динамический пересчёт статуса + процент отправки
        for mailing in qs:
            mailing.update_status(save=True)

            if mailing.total_recipients:
                mailing.send_percent = int(
                    mailing.success_logs * 100 / mailing.total_recipients
                )
            else:
                mailing.send_percent = 0

        return qs


class MailingDetailView(LoginRequiredMixin, DetailView):
    """ Представление для детального просмотра одной рассылки """

    model = Mailing
    template_name = "clients/mailing_detail.html"
    context_object_name = "mailing"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # пересчёт и сохранение статуса
        return obj


class MailingCreateView(ManagerRequiredMixin, LoginRequiredMixin, CreateView):
    """ Представление для создания новой рассылки """

    model = Mailing
    form_class = MailingForm
    template_name = "clients/mailing_form.html"
    success_url = reverse_lazy("clients:mailing_list")


class MailingUpdateView(ManagerRequiredMixin, LoginRequiredMixin, UpdateView):
    """ Представление для редактирования существующей рассылки """

    model = Mailing
    form_class = MailingForm
    template_name = "clients/mailing_form.html"
    success_url = reverse_lazy("clients:mailing_list")


class MailingDeleteView(ManagerRequiredMixin, LoginRequiredMixin, DeleteView):
    """ Представление для удаления рассылки """

    model = Mailing
    template_name = "clients/mailing_confirm_delete.html"
    success_url = reverse_lazy("clients:mailing_list")


class MailingSendNowView(ManagerRequiredMixin, LoginRequiredMixin, View):
    """ Ручной запуск рассылки - сейчас """

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        try:
            success_count, failed_count = mailing.send_now()
            messages.success(
                request,
                f"Рассылка запущена: успешно {success_count}, с ошибкой {failed_count}."
            )
        except ValueError as exc:
            # ошибка из can_be_sent_now (вне интервала)
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f"Ошибка при запуске рассылки: {exc}")

        return redirect("clients:mailing_detail", pk=pk)

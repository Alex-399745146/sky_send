# clients/models.py

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """
    Модель клиентов «Получатель рассылки»:
    - Email уникальный.
    - Имя и фамилия обязательные (для учебного проекта это даже плюс).
    - Комментарий — опциональный.
    """

    email = models.EmailField(
        unique=True,  # Поле email станет уникальным.
        max_length=254,  # Максимальная длина строки в БД.
        verbose_name="Email",  # Человеко‑читаемое имя поля (для админки и форм).
        help_text="Введите Ваш email",
    )

    first_name = models.CharField(
        max_length=50,
        verbose_name="Имя",
    )

    last_name = models.CharField(
        max_length=70,
        verbose_name="Фамилия",
    )

    comment = models.TextField(
        blank=True, null=True, verbose_name="Комментарий", help_text="Поле не обязательное для заполнения"
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Ссылка на кастомного пользователя без жёткой привязки к классу.
        on_delete=models.CASCADE,
        related_name="clients",
        verbose_name="Владелец",
    )

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name} ({self.email})"

    class Meta:
        verbose_name = "Получатель рассылки"
        verbose_name_plural = "Получатели рассылки"


class Message(models.Model):
    """Модель «Сообщение» для рассылки."""

    subject = models.CharField(
        max_length=255,
        verbose_name="Оглавление",
    )

    body = models.TextField(
        verbose_name="Сообщение",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Владелец",
    )

    def __str__(self) -> str:
        return self.subject

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"


class Mailing(models.Model):
    """Модель «Рассылки сообщений»."""

    STATUS_CREATED = "created"
    STATUS_RUNNING = "running"
    STATUS_FINISHED = "finished"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_RUNNING, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    start_time = models.DateTimeField(
        verbose_name="Дата и время начала",
    )

    end_time = models.DateTimeField(
        verbose_name="Дата и время окончания",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус",
    )

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
    )

    recipients = models.ManyToManyField(
        Client,
        related_name="mailings",
        verbose_name="Получатели",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Владелец",
    )

    def __str__(self) -> str:
        return f"Рассылка #{self.pk} — {self.get_status_display()}"

    def update_status(self, save: bool = True) -> None:
        """Пересчитать статус на основе текущего времени и интервала"""
        now = timezone.now()

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_FINISHED

        if new_status != self.status:
            self.status = new_status
            if save:
                self.save(update_fields=["status"])

    def clean(self):
        """Переопределить метод clean() у модели"""
        from django.core.exceptions import ValidationError

        now = timezone.now()

        if self.start_time < now:
            raise ValidationError("Время начала рассылки не может быть в прошлом.")

        if self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть раньше времени окончания.")

    def can_be_sent_now(self) -> bool:
        """Проверка: текущее время в допустимом интервале."""
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def send_now(self) -> tuple[int, int]:
        """
        Запустить данную рассылку вручную.
        Для каждого получателя отправляется письмо и создаётся запись MailingLog.
        Возвращает (success_count, failed_count).
        """

        # 1. Проверка времени
        if not self.can_be_sent_now():
            raise ValueError("Отправка не разрешена: текущее время вне интервала рассылки.")

        # 2. Обновим статус перед отправкой
        self.update_status()

        success_count = 0
        failed_count = 0
        logs_to_create: list[MailingLog] = []

        # 3. Проходим по всем получателям
        for client in self.recipients.all():
            try:
                send_mail(
                    subject=self.message.subject,
                    message=self.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[client.email],
                    fail_silently=False,
                )
                success_count += 1
                logs_to_create.append(
                    MailingLog(
                        mailing=self,
                        recipient=client,
                        status=MailingLog.STATUS_SUCCESS,
                        server_response="OK",
                    )
                )
            except Exception as exc:
                failed_count += 1
                logs_to_create.append(
                    MailingLog(
                        mailing=self,
                        recipient=client,
                        status=MailingLog.STATUS_FAILED,
                        server_response=str(exc),
                    )
                )

        if logs_to_create:
            MailingLog.objects.bulk_create(logs_to_create)

        if success_count > 0 and self.status != self.STATUS_RUNNING:
            self.status = self.STATUS_RUNNING
            self.save(update_fields=["status"])

        return success_count, failed_count

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class MailingLog(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Рассылка",
    )
    recipient = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name="Получатель",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name="Статус",
    )
    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ сервера / ошибка",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки",
    )

    class Meta:
        verbose_name = "Лог отправки"
        verbose_name_plural = "Логи отправки"

    def __str__(self) -> str:
        return f"Рассылка #{self.mailing_id} → {self.recipient.email} ({self.get_status_display()})"

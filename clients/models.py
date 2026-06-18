# clients/models.py
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
        blank=True,
        null=True,
        verbose_name="Комментарий",
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

    def __str__(self) -> str:
        return self.subject

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"


class Mailing(models.Model):
    """Модель «Рассылка»."""

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

    def __str__(self) -> str:
        return f"Рассылка #{self.pk} — {self.get_status_display()}"

    def update_status(self, save: bool = True) -> None:
        """ Пересчитать статус на основе текущего времени и интервала """
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
        """ Переопределить метод clean() у модели """
        from django.core.exceptions import ValidationError

        now = timezone.now()

        if self.start_time < now:
            raise ValidationError("Время начала рассылки не может быть в прошлом.")

        if self.start_time >= self.end_time:
            raise ValidationError("Время начала должно быть раньше времени окончания.")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"

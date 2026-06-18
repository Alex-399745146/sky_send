# clients/models.py
from django.db import models


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

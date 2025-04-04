from django.conf import settings
from django.db import models
from rest_framework.authtoken.models import Token


class UserAPIToken(Token):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="auth_token",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    description = models.TextField(help_text="Напишите для каких целей будет использоваться токен")
    expired = models.DateTimeField(
        null=True, blank=True, help_text="Укажите время истечения токена, если нужно"
    )
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_tokens"
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"

import binascii
import os

from django.contrib.auth import get_user_model
from django.db import models


class UserAPIToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True, verbose_name="Key")
    user = models.ForeignKey(
        get_user_model(),
        related_name="auth_token",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    description = models.TextField(help_text="Напишите для каких целей будет использоваться токен")
    expired = models.DateTimeField(
        null=True, blank=True, help_text="Укажите время истечения токена, если нужно"
    )
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_tokens"
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.key

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()

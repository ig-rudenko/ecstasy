import binascii
import os
from ipaddress import IPv4Address, IPv4Network

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models


def validate_ip_addresses(value):
    for ip in value.split(","):
        try:
            IPv4Network(ip.strip())
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc


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
    allowed_ips = models.TextField(
        verbose_name="Allowed IPs",
        blank=True,
        help_text="Укажите IP адреса через запятую. Можно указывать подсети в формате 192.168.0.0/24",
        validators=[validate_ip_addresses],
    )

    def validate_ip(self, ip):
        """Валидация доступа к токену по IP"""
        if not self.allowed_ips:
            return True
        try:
            client_ip = IPv4Address(ip)
        except ValueError:
            return False
        for allowed_ip in map(str.strip, self.allowed_ips.split(",")):
            try:
                if "/" in allowed_ip and client_ip in IPv4Network(allowed_ip):
                    return True
                if "/" not in allowed_ip and client_ip == IPv4Address(allowed_ip):
                    return True
            except ValueError:
                return False
        return False

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

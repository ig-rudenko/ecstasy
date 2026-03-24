import orjson
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# создаем клиент для отправки запросов
client = APIClient()

# определяем URL для получения и обновления токена
token_url = reverse("token_obtain_pair")
refresh_url = reverse("token_refresh")
# определяем данные для аутентификации пользователя
user_data = {"username": "testuser", "password": "testpassword"}


# определяем класс для тестирования JWT
class JWTTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Подготавливаем тестовую базу данных.
        Создаем тестового пользователя.
        """
        cls.user = User.objects.create_user(**user_data)

    def test_token_obtain(self):
        """
        # тестируем получение токена по URL /token
        """

        # отправляем POST-запрос с данными пользователя
        response = client.post(token_url, orjson.dumps(user_data), content_type="application/json")
        # проверяем статус ответа (должен быть 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # проверяем наличие полей access и refresh в ответе
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        # проверяем формат токенов (должен быть JSON Web Token)
        self.assertTrue(response.data["access"].startswith("eyJh"))
        self.assertTrue(response.data["refresh"].startswith("eyJh"))

    def test_token_refresh(self):
        """
        # тестируем обновление токена по URL /token/refresh
        """

        # получаем токены с помощью предыдущего метода
        response = client.post(token_url, orjson.dumps(user_data), content_type="application/json")
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        # отправляем POST-запрос с refresh токеном
        response = client.post(
            refresh_url,
            orjson.dumps({"refresh": refresh_token}),
            content_type="application/json",
        )
        # проверяем статус ответа (должен быть 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # проверяем наличие поля access в ответе
        self.assertIn("access", response.data)
        # проверяем формат нового access токена (должен быть JSON Web Token)
        self.assertTrue(response.data["access"].startswith("eyJh"))
        # проверяем, что новый access токен отличается от старого
        self.assertNotEqual(response.data["access"], access_token)

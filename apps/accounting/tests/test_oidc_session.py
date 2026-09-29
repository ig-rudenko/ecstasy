from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


@override_settings(
    KEYCLOAK_ENABLE=True,
    AUTHENTICATION_BACKENDS=(
        "ecstasy_project.authentication.KeycloakBackend",
        "django.contrib.auth.backends.ModelBackend",
    ),
    OIDC_OP_TOKEN_ENDPOINT="https://keycloak.example/token",
    OIDC_OP_USER_ENDPOINT="https://keycloak.example/userinfo",
    OIDC_OP_JWKS_ENDPOINT="https://keycloak.example/certs",
    OIDC_OP_AUTHORIZATION_ENDPOINT="https://keycloak.example/auth",
    OIDC_RP_CLIENT_ID="ecstasy",
    OIDC_RP_CLIENT_SECRET=None,
    OIDC_RP_SIGN_ALGO="RS256",
    OIDC_RP_SCOPES="openid profile email",
)
class LocalSessionLogoutAPITests(APITestCase):
    """Tests for local logout after an OIDC login."""

    def setUp(self) -> None:
        """Create a user for session logout tests."""

        self.user = get_user_model().objects.create_user(username="operator")
        self.url = reverse("oidc_session")

    def test_post_does_not_create_django_session(self):
        """The local logout endpoint does not create Django sessions."""

        self.client.force_authenticate(self.user, token=object())

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_oidc_config_requests_online_session(self):
        """OIDC login does not request an offline-only Keycloak session."""

        response = self.client.get(reverse("oidc_config"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["scopes"], "openid profile email")
        self.assertNotIn("offline_access", response.data["scopes"].split())

    def test_delete_clears_django_session(self):
        """Local logout removes an existing Django session."""

        self.client.force_login(
            self.user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        self.assertIn(SESSION_KEY, self.client.session)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_anonymous_user_cannot_delete_local_session(self):
        """Anonymous requests cannot use the local logout endpoint."""

        self.client.force_authenticate(user=None, token=None)

        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

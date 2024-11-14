from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomJWTAuthentication(JWTAuthentication):
    def auth_and_get_user(self, request):
        if not hasattr(request, "_force_auth_user"):
            # print("CustomJWTAuthentication user, token = self.authenticate(request)")
            try:
                data = self.authenticate(request)
            except APIException:
                return request.user
            if data is None:
                return request.user
            user, token = data
            request._force_auth_token = token
            request._force_auth_user = user
        # print("CustomJWTAuthentication", request._force_auth_user)
        return request._force_auth_user or request.user


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # print("JWTAuthenticationMiddleware", request.user, request.user.is_authenticated)
        if request.user.is_authenticated:
            return

        auth = CustomJWTAuthentication()

        request.user = auth.auth_and_get_user(request)

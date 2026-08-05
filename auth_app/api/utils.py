from django.conf import settings


def set_auth_cookie(response, key, token):
    response.set_cookie(
        key=key,
        value=token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax'
    )
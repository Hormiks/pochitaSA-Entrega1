# main/decorators.py
from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def roles_requeridos(*roles: str):
    """
    Restringe el acceso a usuarios autenticados que pertenezcan a al menos
    uno de los grupos indicados en 'roles'. Superuser siempre pasa.

    Uso:
        @roles_requeridos("Recepcionista")
        def mi_vista(...):
            ...
    """
    roles_set = set(roles)

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url=settings.LOGIN_URL)

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            if roles_set and user.groups.filter(name__in=roles_set).exists():
                return view_func(request, *args, **kwargs)

            raise PermissionDenied("No tienes permisos para acceder a esta sección.")

        return _wrapped

    return decorator

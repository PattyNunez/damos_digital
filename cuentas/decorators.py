from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles_permitidos):
    """Exige sesión iniciada (redirige a login si no) y que el rol del usuario esté entre
    los permitidos (403 si no). Los superusuarios de Django siempre pasan, sin importar
    su Perfil — necesario para poder entrar y asignar roles a los demás desde cero."""

    def decorador(vista_original):
        @login_required
        def envoltura(request, *args, **kwargs):
            if request.user.is_superuser:
                return vista_original(request, *args, **kwargs)
            perfil = getattr(request.user, "perfil", None)
            if perfil is None or perfil.rol not in roles_permitidos:
                raise PermissionDenied("No tienes permiso para acceder a esta sección.")
            return vista_original(request, *args, **kwargs)

        return wraps(vista_original)(envoltura)

    return decorador

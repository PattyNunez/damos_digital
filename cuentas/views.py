from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse

from .models import Rol

DESTINO_POR_ROL = {
    Rol.TECNICO: "servicios:mis_servicios",
    Rol.COMERCIAL: "clientes:lista",
    Rol.ADMINISTRADOR: "dashboard:inicio",
}


def _destino_para(usuario):
    perfil = getattr(usuario, "perfil", None)
    if perfil is None:
        return "dashboard:inicio"
    return DESTINO_POR_ROL.get(perfil.rol, "dashboard:inicio")


class LoginConRedireccionPorRol(LoginView):
    template_name = "cuentas/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        url = self.get_redirect_url()
        if url:
            return url
        return reverse(_destino_para(self.request.user))


def inicio(request):
    if not request.user.is_authenticated:
        return redirect("cuentas:login")
    return redirect(_destino_para(request.user))

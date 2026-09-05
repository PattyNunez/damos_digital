from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("login/", views.LoginConRedireccionPorRol.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="cuentas:login"), name="logout"),
]

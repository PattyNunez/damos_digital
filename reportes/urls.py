from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("servicios/<int:pk>/generar/", views.generar_informe, name="generar_informe"),
    path("servicios/<int:pk>/generar-propuesta/", views.generar_propuesta, name="generar_propuesta"),
]

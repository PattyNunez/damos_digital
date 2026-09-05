from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from cuentas.views import inicio

urlpatterns = [
    path("", inicio, name="inicio"),
    path("admin/", admin.site.urls),
    path("", include("cuentas.urls")),
    path("servicios/", include("servicios.urls")),
    path("informes/", include("reportes.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("clientes/", include("clientes.urls")),
    path("inventario/", include("inventario.urls")),
    path("cotizaciones/", include("cotizaciones.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

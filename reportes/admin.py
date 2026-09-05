from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import ConfiguracionInforme, InformeGenerado, PropuestaComercial


@admin.register(InformeGenerado)
class InformeGeneradoAdmin(admin.ModelAdmin):
    list_display = ("servicio", "numero_informe", "version", "generado_en", "generado_por")
    autocomplete_fields = ("servicio",)


@admin.register(PropuestaComercial)
class PropuestaComercialAdmin(admin.ModelAdmin):
    list_display = ("servicio", "version", "generado_en", "generado_por")
    autocomplete_fields = ("servicio",)


@admin.register(ConfiguracionInforme)
class ConfiguracionInformeAdmin(admin.ModelAdmin):
    """Fila única: el índice del admin redirige directo a editarla, sin pasar por un
    changelist que no tendría sentido para un solo registro."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = ConfiguracionInforme.obtener()
        url = reverse("admin:reportes_configuracioninforme_change", args=[obj.pk])
        return HttpResponseRedirect(url)

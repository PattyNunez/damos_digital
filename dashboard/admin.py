from django.contrib import admin

from .models import ConfiguracionAlertas


@admin.register(ConfiguracionAlertas)
class ConfiguracionAlertasAdmin(admin.ModelAdmin):
    list_display = ("dias_alerta_cotizado", "dias_alerta_ejecucion")

    def has_add_permission(self, request):
        # Singleton: si ya existe la fila, no se permite crear una segunda.
        return not ConfiguracionAlertas.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Atajo: ir directo al formulario de edición de la única fila, en vez de mostrar
        # una lista de un solo elemento.
        config = ConfiguracionAlertas.cargar()
        from django.shortcuts import redirect

        return redirect("admin:dashboard_configuracionalertas_change", config.pk)

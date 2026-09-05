from django.contrib import admin

from reportes.pdf import generar_pdf_servicio, guardar_informe

from .models import (
    Conclusion,
    FichaServicio,
    FirmaAprobacion,
    HistorialEstadoServicio,
    Observacion,
    Recomendacion,
    Servicio,
)


class ObservacionInline(admin.TabularInline):
    model = Observacion
    extra = 1


class RecomendacionInline(admin.TabularInline):
    model = Recomendacion
    extra = 1


class FichaServicioInline(admin.StackedInline):
    model = FichaServicio
    extra = 0


class ConclusionInline(admin.TabularInline):
    model = Conclusion
    extra = 1


class FirmaAprobacionInline(admin.StackedInline):
    model = FirmaAprobacion
    extra = 0


class HistorialEstadoServicioInline(admin.TabularInline):
    model = HistorialEstadoServicio
    extra = 0
    readonly_fields = ("estado", "fecha_cambio", "usuario")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.action(description="Generar informe PDF")
def generar_informe_pdf(modeladmin, request, queryset):
    for servicio in queryset:
        pdf_bytes = generar_pdf_servicio(servicio)
        guardar_informe(servicio, pdf_bytes, usuario=request.user)
    modeladmin.message_user(request, f"Informe(s) generado(s) para {queryset.count()} servicio(s).")


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "tipo_servicio",
        "cliente",
        "equipo",
        "estado",
        "monto_total",
        "creado_en",
    )
    list_filter = ("tipo_servicio", "estado", "cliente")
    search_fields = ("codigo", "orden_compra", "titulo")
    readonly_fields = ("codigo", "anio", "correlativo", "subtotal", "monto_igv", "monto_total")
    autocomplete_fields = ("cliente", "equipo", "ubicacion", "servicio_origen")
    actions = [generar_informe_pdf]
    inlines = [
        ObservacionInline,
        RecomendacionInline,
        FichaServicioInline,
        ConclusionInline,
        FirmaAprobacionInline,
        HistorialEstadoServicioInline,
    ]

from django.contrib import admin

from .models import (
    DetalleCotizacion,
    ItemAlcance,
    ItemEquipo,
    ItemExclusion,
    ItemLogistica,
    ItemManoObra,
    ItemMaterial,
    ItemProvisionCliente,
    ItemProvisionDamol,
)


class ItemManoObraInline(admin.TabularInline):
    model = ItemManoObra
    extra = 1


class ItemLogisticaInline(admin.TabularInline):
    model = ItemLogistica
    extra = 1


class ItemEquipoInline(admin.TabularInline):
    model = ItemEquipo
    extra = 1


class ItemMaterialInline(admin.TabularInline):
    model = ItemMaterial
    extra = 1
    autocomplete_fields = ("producto",)


class ItemAlcanceInline(admin.TabularInline):
    model = ItemAlcance
    extra = 1


class ItemExclusionInline(admin.TabularInline):
    model = ItemExclusion
    extra = 1


class ItemProvisionClienteInline(admin.TabularInline):
    model = ItemProvisionCliente
    extra = 1


class ItemProvisionDamolInline(admin.TabularInline):
    model = ItemProvisionDamol
    extra = 1


@admin.register(DetalleCotizacion)
class DetalleCotizacionAdmin(admin.ModelAdmin):
    list_display = ("servicio", "subtotal_servicio", "subtotal_repuestos")
    readonly_fields = (
        "subtotal_mano_obra",
        "subtotal_logistica",
        "subtotal_equipos",
        "subtotal_materiales",
        "monto_indirectos",
        "monto_utilidad_servicio",
        "monto_utilidad_repuestos",
        "subtotal_servicio",
        "subtotal_repuestos",
    )
    autocomplete_fields = ("servicio",)
    inlines = [
        ItemManoObraInline,
        ItemLogisticaInline,
        ItemEquipoInline,
        ItemMaterialInline,
        ItemAlcanceInline,
        ItemExclusionInline,
        ItemProvisionClienteInline,
        ItemProvisionDamolInline,
    ]

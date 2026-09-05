from django.contrib import admin

from .models import Producto, Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "ruc", "contacto_nombre", "activo")
    search_fields = ("razon_social", "ruc")
    list_filter = ("activo",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "precio_referencial", "moneda", "proveedor_principal", "activo")
    search_fields = ("codigo", "nombre", "categoria")
    list_filter = ("categoria", "moneda", "activo")

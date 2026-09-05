from django.contrib import admin

from .models import Cliente, Ubicacion


class UbicacionInline(admin.TabularInline):
    model = Ubicacion
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "codigo_corto", "ruc", "contacto_nombre")
    search_fields = ("razon_social", "codigo_corto", "ruc")
    inlines = [UbicacionInline]


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cliente")
    list_filter = ("cliente",)
    search_fields = ("nombre", "cliente__razon_social")

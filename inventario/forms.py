from django import forms
from django.core.validators import RegexValidator

from .models import Producto, Proveedor

validar_ruc = RegexValidator(
    regex=r"^(10|15|16|17|20)\d{9}$",
    message="El RUC debe tener 11 dígitos y empezar con 10, 15, 16, 17 o 20.",
)


class ProveedorForm(forms.ModelForm):
    ruc = forms.CharField(required=False, validators=[validar_ruc])

    class Meta:
        model = Proveedor
        fields = [
            "razon_social",
            "ruc",
            "direccion",
            "contacto_nombre",
            "contacto_telefono",
            "contacto_email",
            "activo",
        ]


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "categoria",
            "unidad_medida",
            "precio_referencial",
            "moneda",
            "proveedor_principal",
            "activo",
        ]


class ImportarProductosForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel (.xlsx)")


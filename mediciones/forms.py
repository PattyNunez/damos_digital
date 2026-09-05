from django import forms


class GrupoMedicionCreateForm(forms.Form):
    """Formulario simple para crear una tabla de mediciones nueva: se define el nombre
    y las etiquetas de columnas/filas como texto separado por comas, y la vista arma
    el grid (ColumnaMedicion x FilaMedicion) con celdas ValorMedicion vacías."""

    nombre = forms.CharField(max_length=150)
    unidad = forms.CharField(max_length=20, required=False)
    columnas = forms.CharField(
        max_length=500, help_text="Nombres de columna separados por coma, ej: Motor 1, Motor 2"
    )
    filas = forms.CharField(
        max_length=500, help_text="Nombres de fila separados por coma, ej: V1+T, V2+T, V3+T"
    )

    def limpiar_lista(self, campo):
        valor = self.cleaned_data[campo]
        return [parte.strip() for parte in valor.split(",") if parte.strip()]

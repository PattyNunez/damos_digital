from django.db import migrations

VALORES_INICIALES = {
    "mano_obra": [
        "Técnico mecánico (día)",
        "Técnico electricista (día)",
        "Ayudante mecánico (día)",
        "Supervisor operativo (día)",
        "Supervisor SSOMA (día)",
    ],
    "logistica": [
        "Movilidad local",
        "Viáticos por técnico/día",
        "Hospedaje por técnico/noche",
        "Transporte de equipos/herramientas",
    ],
    "equipo": [
        "Andamio multidireccional (semana)",
        "Manlift articulado (día)",
        "Grúa móvil de apoyo (día)",
    ],
    "alcance": [
        "Inspección visual de estructura y componentes",
        "Lubricación de mecanismos de izaje y traslación",
        "Medición de parámetros eléctricos (aislamiento, corriente, voltaje)",
        "Ajuste de frenos y verificación de límites de carrera",
        "Limpieza general de estructura y tablero eléctrico",
    ],
    "exclusion": [
        "No incluye repuestos ni materiales de reposición",
        "No incluye trabajos en altura sin autorización previa del cliente",
        "No incluye pruebas de carga certificadas",
        "No incluye reparaciones estructurales mayores",
    ],
    "provision_cliente": [
        "Acceso a planta y permisos de ingreso",
        "Energía eléctrica disponible en el punto de trabajo",
        "Punto de anclaje certificado para trabajos en altura",
    ],
    "provision_damol": [
        "Herramientas y equipos de medición",
        "EPP para el personal técnico",
        "Movilidad y viáticos del personal",
    ],
}


def cargar(apps, schema_editor):
    ItemCatalogo = apps.get_model("cotizaciones", "ItemCatalogo")
    for tipo, textos in VALORES_INICIALES.items():
        for texto in textos:
            ItemCatalogo.objects.get_or_create(tipo=tipo, texto=texto)


def revertir(apps, schema_editor):
    ItemCatalogo = apps.get_model("cotizaciones", "ItemCatalogo")
    for tipo, textos in VALORES_INICIALES.items():
        ItemCatalogo.objects.filter(tipo=tipo, texto__in=textos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("cotizaciones", "0004_itemcatalogo"),
    ]

    operations = [
        migrations.RunPython(cargar, revertir),
    ]

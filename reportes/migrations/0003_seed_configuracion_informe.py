from datetime import date

from django.db import migrations

# Texto real de la sección "3. NORMATIVIDAD" de JP-F-007 (referencias/INF-12625-OT-183-2024...pdf).
NORMATIVIDAD_TEXTO = """\
Norma ANSI / ASME B30.16: "Overhead Hoist (Underhung)"; (American Society of Mechanical Engineers)
Norma ANSI / ASME B30.2: "Overhead and Gantry Cranes"; (American Society of Mechanical Engineers)
CMAA 70: "Specification for Top and Running Bridge and Gantry Type Multiple Girder Electric Overhead Traveling Cranes". (Crane Manufacturers Association of America)
Norma ANSI / ASME B30.20: "Below the Hook Lifting Devices"; (American Society of Mechanical Engineers)
Norma FEM: "Federación Europea de Mantenimiento" grupo de mecanismos para polipastos.
Norma HMI: (Hoist Manufacturers Institute)
Norma ASME B30.10 Hooks (American Society of Mechanical Engineers).
Norma OSHA: (Occupational Safety and Health Administration)
D.S. Nº 024-2016-EM: Reglamento de Seguridad e Higiene Minera, MINISTERIO DE ENERGÍA Y MINAS DEL PERÚ\
"""


def sembrar_configuracion(apps, schema_editor):
    ConfiguracionInforme = apps.get_model("reportes", "ConfiguracionInforme")
    ConfiguracionInforme.objects.get_or_create(
        pk=1,
        defaults={
            "encabezado_codigo": "JP-F-007",
            "encabezado_version": "04",
            "encabezado_fecha_aprobacion": date(2022, 6, 16),
            "normatividad_texto": NORMATIVIDAD_TEXTO,
        },
    )


def revertir(apps, schema_editor):
    ConfiguracionInforme = apps.get_model("reportes", "ConfiguracionInforme")
    ConfiguracionInforme.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reportes", "0002_configuracioninforme_and_more"),
    ]

    operations = [
        migrations.RunPython(sembrar_configuracion, revertir),
    ]

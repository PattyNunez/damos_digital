# Damol Digital

Sistema interno de Damol Ingenieros para gestionar cotizaciones, servicios (preventivos y
correctivos), formularios técnicos de campo y generación de informes PDF de mantenimiento
de equipos de izaje.

## Requisitos

- Python 3.9+
- PostgreSQL 13+ (se probó con 16)

## Cómo levantarlo desde cero

### 1. Clonar y crear el entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate   # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Crear la base de datos en PostgreSQL

Con el servidor de PostgreSQL corriendo localmente:

```bash
psql postgres -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'damol_digital') THEN
      CREATE ROLE damol_digital WITH LOGIN PASSWORD 'damol_digital';
   END IF;
END
$$;
SELECT 'CREATE DATABASE damol_digital OWNER damol_digital'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'damol_digital')\gexec
SQL
```

Esto crea el rol `damol_digital` (contraseña `damol_digital`) y la base de datos
`damol_digital`, que son los valores por defecto que espera `.env.example`. Si prefieres
otro usuario/contraseña, ajústalos en el paso 3.

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` si tu usuario/contraseña/puerto de PostgreSQL son distintos a los valores
por defecto.

### 4. Migrar y crear un usuario administrador

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Correr el servidor

```bash
python manage.py runserver
```

Abre http://127.0.0.1:8000/admin/ e ingresa con el superusuario creado en el paso 4.

## Estructura del proyecto

Cada app cubre un módulo del dominio:

| App          | Responsabilidad                                                              |
|--------------|-------------------------------------------------------------------------------|
| `clientes`   | Clientes y sus ubicaciones/sedes                                              |
| `equipos`    | Tipos de equipo y equipos de izaje por cliente                                |
| `catalogos`  | Catálogos reutilizables: normas aplicables, equipos de medición de Damol      |
| `servicios`  | El núcleo: cotizaciones/servicios, correlativo, historial de estados, ítems de cotización, ficha de campo, observaciones/recomendaciones/conclusiones, firmas |
| `personal`   | Técnicos, personal ejecutor por servicio, materiales y herramientas, certificaciones |
| `checklist`  | Plantillas de checklist por tipo de equipo y respuestas con fotos por servicio |
| `mediciones` | Tablas de mediciones configurables (filas × columnas × valor) por servicio     |
| `reportes`   | Informes PDF generados a partir de un servicio                                |

### Numeración de servicios

El código de cada servicio tiene el formato:

```
{COT|SERV}-{PREV|CORR}-{AÑO}-{CLIENTE}-{CORRELATIVO}
```

Ejemplo: `COT-PREV-2026-VOLCAN-001` (cotización de un preventivo para Volcán) que, al
aprobarse, pasa a `SERV-PREV-2026-VOLCAN-001` (mismo correlativo, cambia solo el prefijo).

El correlativo (los últimos 3 dígitos) se reinicia cada año y es independiente por cada
combinación de tipo de servicio (preventivo/correctivo) + cliente. La asignación es
atómica (usa un bloqueo de fila en PostgreSQL vía `select_for_update`), por lo que dos
personas cotizando al mismo tiempo nunca terminan con el mismo correlativo.

## Estado actual

Modelos y admin del módulo 1 (cotización/correlativo) implementados y probados
(incluida una prueba de concurrencia con 8 procesos creando servicios en simultáneo).
Los siguientes módulos (formulario de campo, subida de fotos, generación de PDF,
dashboard, kanban) se construyen uno por uno sobre esta base.

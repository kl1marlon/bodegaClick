# Documentación: Flujo de Migración de Producción a Pruebas

Este documento describe el proceso estructurado para crear un entorno de pruebas a partir de una base de datos de producción y sincronizar productos desde una cuenta Loyverse destino. El objetivo es dejar un procedimiento claro, reproducible y seguro, útil para desarrolladores actuales y futuros.

---

## Contexto

### Descripción del Sistema
- **Backend:** Aplicación web desarrollada con el framework **Django** (Python).
- **Base de Datos:** Utiliza una base de datos relacional (**PostgreSQL**, basado en despliegues en Neon y sintaxis SQL utilizada).
- **Despliegue:** Gestionado a través de **Coolify**.
- **Integración Principal:** Interactúa intensivamente con la **API de Loyverse** para gestionar productos, stock, etc.

### Escenario
- El sistema está configurado para operar sobre una cuenta principal de Loyverse (producción).
- Se requiere crear un entorno de pruebas aislado, que permita hacer pruebas sin afectar producción.
- El proceso debe ser reutilizable para nuevos clientes o cuentas Loyverse.

---

## Flujo General
1. **Preparación del entorno**
2. **Creación y configuración de la base de datos de pruebas**
3. **Limpieza de datos previos**
4. **Sincronización inicial de productos desde Loyverse**
5. **Verificación y pruebas**

---

## Task List

### 1. Preparación del entorno
- [x] Definir y documentar las variables de entorno necesarias (tokens API, credenciales BD, etc.) _(Responsable: Usuario)_
- [x] Obtener el token de la cuenta Loyverse destino _(Responsable: Usuario)_

### 2. Creación y configuración de la base de datos de pruebas
- [x] Crear una nueva base de datos vacía (ejemplo: en Neon) _(Responsable: Usuario)_
- [x] Configurar la aplicación para apuntar a la nueva base de datos _(Responsable: Usuario)_
- [ ] Aplicar migraciones para crear la estructura de tablas _(Responsable: Usuario)_

> **Nota importante sobre migraciones:**
>
> - **Solo debes aplicar migraciones si:**
>   - La base de datos es completamente nueva y no tiene las tablas creadas.
>   - Has realizado cambios recientes en los modelos y necesitas actualizar la estructura de la base de datos.
> - **Si tu base de datos ya tiene la estructura correcta y solo borraste los datos (por ejemplo, usando TRUNCATE o DELETE), NO es necesario volver a aplicar migraciones.**
> - Puedes verificar si necesitas migrar intentando acceder a la app o usando Django admin/shell. Si ves errores de "tabla no existe" o "columna no existe", entonces sí debes migrar.
> - En este flujo, puedes trabajar en un branch separado y simplemente borrar los datos para pruebas, sin necesidad de migrar si la estructura ya está lista.

### 3. Limpieza de datos previos

> **IMPORTANTE:** Este paso es crítico para garantizar que la base de datos de pruebas esté completamente limpia antes de importar los productos desde Loyverse. Realízalo únicamente en la base de datos de pruebas, nunca en producción.

#### ¿Qué tablas limpiar?
- Productos (`facturacion_producto`)
- Facturas (`facturacion_factura`)
- Detalles de factura (`facturacion_detallefactura`)
- (Opcional) Tasas de cambio (`facturacion_tasacambio`)
- (Opcional) Webhooks (`facturacion_webhook`)

#### ¿Cómo hacerlo?

##### Opción A: Comandos SQL directos
Ejecuta estos comandos en la base de datos de pruebas (verifica siempre que es la correcta):

```sql
-- Borra facturas y detalles (por CASCADE)
TRUNCATE TABLE facturacion_factura RESTART IDENTITY CASCADE;

-- Borra productos (ya no debería haber dependencias)
TRUNCATE TABLE facturacion_producto RESTART IDENTITY CASCADE;

-- Opcional: borra tasas y webhooks
TRUNCATE TABLE facturacion_tasacambio RESTART IDENTITY CASCADE;
TRUNCATE TABLE facturacion_webhook RESTART IDENTITY CASCADE;
```

##### Opción B: Desde Django shell

```python
from facturacion.models import Producto, Factura, DetalleFactura, TasaCambio, Webhook

DetalleFactura.objects.all().delete()
Factura.objects.all().delete()
Producto.objects.all().delete()
TasaCambio.objects.all().delete()
Webhook.objects.all().delete()
```

> **Nota:** El método SQL es más rápido y seguro para grandes volúmenes de datos. El método Django shell es útil si no tienes acceso directo al gestor de la base de datos.

#### ¿Cuándo hacerlo?
- Justo antes de ejecutar la sincronización inicial de productos desde Loyverse.

#### ¿Quién lo hace?
- **Responsable:** Usuario (requiere acceso y precaución).

### 4. Sincronización inicial desde Loyverse
- [x] Crear módulo/comando de sincronización inicial de productos _(Responsable: AI)_
- [x] Documentar el uso del módulo y la lógica de cálculo de precios _(Responsable: AI)_
- [x] Ejecutar la sincronización y verificar resultados _(Responsable: Usuario)_
- [x] Verificar que todos los productos nuevos queden configurados con la tasa "PARALELO" _(Responsable: Usuario)_
- [ ] (Por hacer) Eliminar la lógica de múltiples tasas y dejar solo una tasa en el sistema _(Responsable: AI/Usuario)_ (por hacer luego)

#### Implementación y uso del módulo de sincronización

Se implementó el script `backend/scripts/sync_loyverse_products.py` para automatizar la sincronización inicial de productos desde Loyverse a la base de datos de pruebas. El flujo realizado es el siguiente:

1. **Preparación del entorno:**
    - Variables de entorno requeridas en el archivo `.env` en la raíz del proyecto:
      ```env
      LOYVERSE_API_TOKEN=tu_token_de_loyverse
      POSTGRES_HOST='ep-withered-heart-a4btm25j-pooler.us-east-1.aws.neon.tech'
      POSTGRES_DB='bodegaclicktest'
      POSTGRES_USER='bodegaclicktest_owner'
      POSTGRES_PASSWORD='tu_contraseña_de_neon'
      ```
    - El script carga automáticamente estas variables.

2. **Limpieza de la base de datos:**
    - Asegúrate de que la base de datos de pruebas esté vacía de productos antes de sincronizar (ver sección anterior para comandos SQL o Django shell).

3. **Ejecución del script:**
    - Desde la raíz del proyecto, ejecuta:
      ```bash
      python backend/scripts/sync_loyverse_products.py <tasa_cambio>
      ```
      Por ejemplo:
      ```bash
      python backend/scripts/sync_loyverse_products.py 95
      ```
    - El script solicitará confirmación si detecta productos existentes.
    - Descarga todos los productos de Loyverse, calcula el precio en USD (`precio_base_usd = precio_loyverse / tasa_cambio`), y configura `tipo_tasa = 'PARALELO'` para todos los productos.
    - Mapea correctamente las categorías y registra logs detallados.

4. **Verificación:**
    - Verifica en la base de datos que los productos se hayan importado correctamente.
    - Confirma que el campo `precio_base_usd` esté calculado según la tasa usada.
    - Confirma que el campo `tipo_tasa` esté en "PARALELO" para todos los productos.
    - Revisa el archivo de log `loyverse_initial_sync.log` para detalles y posibles advertencias.

#### Estado de tareas
- [x] Crear módulo/comando de sincronización inicial de productos
- [x] Documentar el uso del módulo y la lógica de cálculo de precios
- [x] Ejecutar la sincronización y verificar resultados
- [x] Verificar que todos los productos nuevos queden configurados con la tasa "PARALELO"
- [ ] (Por hacer) Eliminar la lógica de múltiples tasas y dejar solo una tasa en el sistema

### 5. Verificación y pruebas
- [ ] Verificar que los productos se hayan importado correctamente _(Responsable: Usuario)_
- [ ] Probar funcionalidades clave del sistema en el entorno de pruebas _(Responsable: Usuario)_

---

## Consideraciones para Escalabilidad y Comercialización
- Documentar cómo repetir este flujo para nuevos clientes/cuentas Loyverse.
- Evaluar automatización del proceso (scripts, panel de administración, etc.).
- Mantener este documento actualizado conforme se mejore el proceso.

---

## Notas
- Antes de ejecutar cualquier acción destructiva, asegúrate de estar en el entorno de pruebas.
- Consulta con el equipo antes de modificar este documento o el flujo.

---

## Historial de Cambios
- _27/04/2025: Documento inicial creado. Estructura de tasks y responsables._

---

## Próximos pasos
- Esperar aprobación del flujo y tasks antes de avanzar con la implementación del módulo de sincronización.

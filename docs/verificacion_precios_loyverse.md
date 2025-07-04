# Verificación de Precios Loyverse

## Cambios recientes en el flujo de actualización de precios

### Actualización masiva de precios base desde la interfaz
- Se implementó un endpoint en el backend (`/api/productos/actualizar-precios-base/`) que permite actualizar el campo `precio_base` de todos los productos, recibiendo la nueva tasa por POST.
- Este endpoint recorre todos los productos y recalcula su `precio_base` usando el campo `precio_base_usd` y la tasa enviada.
- Desde la interfaz (ListadoProductos.js) se agregará un botón para ejecutar esta acción de forma rápida y sencilla tras cambiar la tasa.
- El comando de management `actualizar_precios_base.py` sigue disponible para uso manual desde la terminal.

### Lógica de actualización individual
- Si el campo `precio_base_usd` de un producto cambia (por ejemplo, al registrar una nueva factura), el precio_base debe recalcularse usando la tasa vigente para mantener la integridad lógica.

### Decisión sobre workers
- Se descartó el uso de Celery/workers para mantener la solución simple y rápida. La actualización masiva se ejecuta como una petición HTTP y puede tomar algunos segundos dependiendo del número de productos.

---

## Nueva herramienta de actualización masiva vía script

- Se implementó un script Python independiente (`backend/scripts/actualizar_precios_base.py`) que permite actualizar el campo `precio_base` de todos los productos conectándose directamente a la base de datos PostgreSQL.
- El script solicita la tasa paralelo al usuario, la confirma y aplica la fórmula:
  
  > **precio_base = precio_base_usd * tasa**

- El proceso registra logs detallados, muestra el progreso y tiempos, y solo actualiza productos cuyo precio realmente cambia.
- Ejemplo de ejecución:
  ```bash
  python backend/scripts/actualizar_precios_base.py
  ```
- El log generado muestra el ID del producto y el cambio realizado. Al final, se muestra un resumen con el total de productos revisados, actualizados, sin cambios, la tasa aplicada y el tiempo total.

### Lógica de cálculo de precios en el código base
- La lógica de cálculo de precios base (`precio_base = precio_base_usd * tasa`) está presente en:
  - El script mencionado arriba.
  - El comando de management `actualizar_precios_base.py`.
  - El endpoint `/api/productos/actualizar-precios-base/`.
- En todos los casos, la actualización solo ocurre si el producto tiene un `precio_base_usd > 0` y si el nuevo precio difiere del actual.

---

## Mejora: Redondeo especial de precios base en el script de actualización

Desde abril 2025, el script `backend/scripts/actualizar_precios_base.py` aplica la misma lógica de redondeo especial utilizada en el frontend para los precios base en bolívares:

- **Lógica aplicada:**
  - Todos los precios base calculados (`precio_base_usd * tasa`) son redondeados automáticamente siguiendo reglas comerciales:
    - Precios menores a 20 Bs. se ajustan a múltiplos de 5 (ej: 3 y 4 → 5; 6-9 → 10; 12-14 → 15; etc.).
    - Precios iguales o mayores a 20 Bs. se redondean al múltiplo de 5 superior más cercano.
    - Si el precio termina en 0 o 5 y no tiene decimales, se mantiene igual.
    - Ejemplos: 22.7 → 25; 37 → 40; 14 → 15; 5 → 5.
- **Propósito:**
  - Garantizar coherencia total entre backend y frontend.
  - Facilitar la gestión de efectivo y precios comerciales.
  - Evitar precios incómodos o difíciles de cobrar.
- **Implementación:**
  - Se añadió la función `aplicar_redondeo_especial` en el script Python, replicando exactamente la lógica de negocio usada en el frontend (ver `src/utils/calculosPrecios.js`).
  - El precio base solo se actualiza si el nuevo valor redondeado difiere del actual.

Esta mejora asegura que todos los precios base en la base de datos estén alineados con la experiencia del usuario y la lógica comercial de la aplicación.

---

## Cambios recientes en la lógica de actualización de precios base

### 1. Soporte para múltiples tasas (BCV y Paralelo)
- Ahora el sistema soporta dos tasas de cambio: **BCV** y **PARALELO**, almacenadas en la tabla `facturacion_tasacambio`.
- Cada producto tiene un campo `tipo_tasa` que determina cuál tasa se usará para recalcular su precio base.
- El cálculo del precio base ahora es:
  ```
  precio_base = precio_base_usd * valor_de_la_tasa_seleccionada
  ```
  donde `valor_de_la_tasa_seleccionada` depende del `tipo_tasa` configurado en cada producto.

### 2. Actualización y confirmación de tasas
- Al ejecutar el script de actualización, el usuario puede consultar y modificar ambos valores de tasa (BCV y Paralelo) antes de recalcular precios.
- Si el usuario confirma los nuevos valores, estos se actualizan en la base de datos y se usan para el recálculo.

### 3. Registro detallado de la actualización
- El log de la operación ahora incluye:
  - Un resumen de productos revisados, actualizados y sin cambios.
  - Un bloque detallado con la lista de productos cuyo precio no cambió, incluyendo ID, nombre, precio actual, tipo de tasa y tasa aplicada.

---

## Guía paso a paso para actualizar precios en Loyverse

Esta guía describe el flujo recomendado para actualizar la tasa, recalcular los precios base y sincronizarlos de forma segura con Loyverse.

## 1. Cambiar la tasa y actualizar los precios_base

Puedes actualizar la tasa y recalcular los precios base de dos maneras:

### Opción A: Desde la interfaz web
1. Ve al Listado de Productos en el frontend.
2. Haz clic en el botón "Actualizar precios base" (debe estar disponible si tienes permisos de admin).
3. Ingresa la nueva tasa cuando se solicite.
4. Confirma la operación. El backend recalculará automáticamente todos los `precio_base` usando la nueva tasa y la lógica de redondeo comercial.
5. Espera el mensaje de confirmación.

### Opción B: Desde la terminal (script manual)
1. Abre una terminal en la raíz del proyecto.
2. Ejecuta el script:
   ```bash
   python backend/scripts/actualizar_precios_base.py
   ```
3. Ingresa la nueva tasa cuando el script lo solicite.
4. El script mostrará el progreso, los cambios realizados y un resumen al final.

> **Nota:** Ambos métodos aplican la lógica de redondeo especial y solo actualizan productos cuyo precio realmente cambia.

## 2. Verificar diferencias de precios con Loyverse (modo seguro)

Antes de actualizar precios en Loyverse, es recomendable verificar qué productos tienen diferencias:

1. Abre una terminal en la raíz del proyecto.
2. Ejecuta el siguiente comando en modo "solo verificación":
   ```bash
   python backend/scripts/sync_all_loyverse_prices_legacy.py --check-only
   ```
3. El script:
   - Comparará los precios locales (`precio_base`) con los de Loyverse.
   - Mostrará un reporte detallado de productos con diferencias, indicando si:
     - El precio ya coincide (no se hará nada).
     - El precio en Loyverse es mayor (requiere decisión especial).
     - El precio local es diferente y se actualizaría.
   - **No realizará ningún cambio real en Loyverse.**
4. Revisa el resumen y el reporte de diferencias en la terminal.

## 3. Ejecutar la actualización real de precios en Loyverse

Cuando estés seguro de que los precios locales son correctos:

- Para actualizar solo productos donde el precio local es igual o mayor que el de Loyverse:
  ```bash
  python backend/scripts/sync_all_loyverse_prices_legacy.py
  ```
- Para forzar la actualización incluso si el precio local es menor:
  ```bash
  python backend/scripts/sync_all_loyverse_prices_legacy.py --force-lower-price
  ```

El script mostrará el progreso, los cambios realizados y un resumen al final.

## 4. Recomendaciones de seguridad y respaldo

- **Haz siempre un respaldo** de la base de datos antes de ejecutar actualizaciones masivas.
- Usa primero el modo `--check-only` para evitar errores y sorpresas.
- Si tienes dudas sobre algún producto donde el precio en Loyverse es mayor, revisa manualmente antes de forzar la actualización.
- Guarda los logs de cada ejecución para auditoría y control.

---

**¡Listo! Siguiendo estos pasos puedes mantener tus precios sincronizados y bajo control entre tu sistema local y Loyverse.**

---

## Próximos pasos: Llevar la lógica a la interfaz web

Para que esta funcionalidad esté disponible desde la interfaz web, se recomienda:

### a) Backend
- Implementar un endpoint seguro (solo para admins) en la API REST que permita:
  1. Consultar las tasas actuales (BCV y Paralelo).
  2. Actualizar los valores de ambas tasas.
  3. Lanzar el proceso de recálculo de precios base para todos los productos, aplicando la lógica ya probada en el script.
- El endpoint debe devolver un resumen similar al del script (productos actualizados, sin cambios, errores, etc).

### b) Frontend
- Agregar un botón "Actualizar precios base" en la vista de productos (visible solo para administradores).
- Al hacer clic, mostrar un formulario para editar/confirmar los valores de las tasas BCV y Paralelo.
- Al confirmar, enviar la solicitud al backend y mostrar el progreso y el resumen de la actualización.
- Mostrar un mensaje de éxito o error según el resultado.

### c) Seguridad y registro
- Asegurar que solo usuarios con permisos de admin puedan acceder a esta funcionalidad.
- Registrar en logs de backend quién realizó la actualización y cuándo.

### d) Lógica de negocio
- Reutilizar la lógica de Python del script en el backend para evitar duplicar código y asegurar consistencia.
- Mantener la lógica de redondeo especial y el registro detallado de productos sin cambios.

---

## Resumen
- El proceso de actualización de precios base ahora es más flexible y auditable.
- Puedes actualizar tasas y precios desde terminal o, próximamente, desde la interfaz web.
- El siguiente paso es exponer esta lógica en la API y conectar la funcionalidad al frontend para una experiencia de usuario más sencilla y segura.

---

¿Dudas o sugerencias? ¡Contacta al equipo de desarrollo!

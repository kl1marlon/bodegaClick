# Sistema de Precios y Tasas de Cambio

## Descripción General
El sistema de precios de BodegaClick permite gestionar productos y sus precios en múltiples monedas, aplicando tasas de cambio dinámicas y lógica de redondeo especial para precios en bolívares. Este sistema es fundamental para la actualización masiva de precios y la sincronización con sistemas externos como Loyverse.

## Modelo de Datos

### Modelo `Producto`
- `precio_base_usd`: Precio base del producto en USD.
- `precio_base`: Precio base en moneda local (calculado aplicando la tasa de cambio y redondeo).
- `tipo_tasa`: Define si el producto usa la tasa BCV o PARALELO.
- Otros campos relevantes: `porcentaje_ganancia`, `es_precio_variable`.

### Modelo `TasaCambio`
- `tipo`: Puede ser 'BCV' o 'PARALELO'.
- `valor`: Valor decimal de la tasa.
- `fecha`: Fecha de la tasa registrada.

## Actualización de Tasas de Cambio
Las tasas de cambio se almacenan en la tabla `facturacion_tasacambio`. El script `actualizar_precios_base.py` permite:
- Consultar y actualizar las tasas BCV y PARALELO.
- Registrar cada cambio de tasa con fecha y tipo.

**Lógica:**
- Si no existe una tasa para el tipo, se crea.
- Si existe, se actualiza el valor y la fecha.

## Cálculo y Redondeo de Precios
La actualización de precios se realiza con el script `actualizar_precios_base.py`:
1. Se obtiene el `precio_base_usd` de cada producto.
2. Se multiplica por la tasa correspondiente (`tipo_tasa`).
3. Se aplica la función de redondeo especial para precios en bolívares:
   - Precios menores a 20 Bs se redondean a múltiplos de 5 o 10 según reglas específicas.
   - Para 20 Bs o más, se redondea al múltiplo de 5 más cercano hacia arriba.

**Ejemplo de Redondeo:**
- 2.80 Bs → 5.00 Bs
- 13.20 Bs → 15.00 Bs
- 23.50 Bs → 25.00 Bs

## Scripts y Automatización
- `backend/scripts/actualizar_precios_base.py`: Actualiza precios base de todos los productos según la tasa y lógica de redondeo.
- Permite entrada manual de tasas y confirmación antes de actualizar.
- Genera logs detallados del proceso y resumen de cambios.

## Sincronización con Loyverse
- Los precios calculados y actualizados se sincronizan con Loyverse usando `sync_all_loyverse_prices.py`.
- Solo se actualizan en Loyverse los productos cuyo precio local cambió o cuando se fuerza la actualización.

## Buenas Prácticas y Seguridad
- Las tasas de cambio deben ser confirmadas manualmente antes de aplicar cambios masivos.
- Se recomienda revisar los logs generados para auditar el proceso.
- El acceso a los scripts debe estar restringido a usuarios autorizados.

## Extensibilidad
- El sistema permite agregar nuevas tasas de cambio si se requiere soportar otras monedas.
- La lógica de redondeo puede ajustarse en el script para nuevas reglas comerciales.

---

**Referencia de Archivos:**
- `backend/facturacion/models.py`
- `backend/scripts/actualizar_precios_base.py`
- `backend/scripts/sync_all_loyverse_prices.py`

2. Se multiplica por la tasa correspondiente (`tipo_tasa`).
3. Se aplica la función de redondeo especial para precios en bolívares:
   - Precios menores a 20 Bs se redondean a múltiplos de 5 o 10 según reglas específicas.
   - Para 20 Bs o más, se redondea al múltiplo de 5 más cercano hacia arriba.

**Ejemplo de Redondeo:**
- 2.80 Bs → 5.00 Bs
- 13.20 Bs → 15.00 Bs
- 23.50 Bs → 25.00 Bs

## Scripts y Automatización
- `backend/scripts/actualizar_precios_base.py`: Actualiza precios base de todos los productos según la tasa y lógica de redondeo.
- Permite entrada manual de tasas y confirmación antes de actualizar.
- Genera logs detallados del proceso y resumen de cambios.

## Sincronización con Loyverse
- Los precios calculados y actualizados se sincronizan con Loyverse usando `sync_all_loyverse_prices.py`.
- Solo se actualizan en Loyverse los productos cuyo precio local cambió o cuando se fuerza la actualización.

## Buenas Prácticas y Seguridad
- Las tasas de cambio deben ser confirmadas manualmente antes de aplicar cambios masivos.
- Se recomienda revisar los logs generados para auditar el proceso.
- El acceso a los scripts debe estar restringido a usuarios autorizados.

## Extensibilidad
- El sistema permite agregar nuevas tasas de cambio si se requiere soportar otras monedas.
- La lógica de redondeo puede ajustarse en el script para nuevas reglas comerciales.

---

**Referencia de Archivos:**
- `backend/facturacion/models.py`
- `backend/scripts/actualizar_precios_base.py`
- `backend/scripts/sync_all_loyverse_prices.py`

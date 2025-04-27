# Módulo de Sincronización Inicial de Productos desde Loyverse

Este módulo permite realizar una sincronización inicial de productos desde una cuenta Loyverse hacia la base de datos de pruebas (o de un nuevo cliente), calculando correctamente los precios en USD y configurando todos los productos con la tasa "PARALELO".

## Requisitos previos

1. **Base de datos limpia**: Antes de ejecutar este script, la base de datos debe estar limpia. Consulta la sección "Limpieza de datos previos" en la documentación principal.

2. **Variables de entorno**: Asegúrate de tener configuradas las siguientes variables:
   - `LOYVERSE_API_TOKEN`: Token de API de la cuenta Loyverse destino
   - `DJANGO_SETTINGS_MODULE`: Configuración de Django (normalmente `config.settings`)

3. **Tasa de cambio**: Debes conocer la tasa de cambio actual que se utilizará para calcular los precios en USD.

## Uso del módulo

```bash
# Navega a la carpeta del proyecto
cd path/to/bodegaClick

# Ejecuta el script con la tasa de cambio como argumento
python backend/scripts/sync_loyverse_products.py <tasa_cambio>

# Ejemplo con tasa de 35.5 VES por 1 USD
python backend/scripts/sync_loyverse_products.py 35.5
```

## Lógica de cálculo de precios

El script implementa la siguiente lógica para el cálculo y almacenamiento de precios:

1. **Obtención del precio desde Loyverse**:
   - Se obtiene el precio del producto en Loyverse (normalmente en VES)
   - Se utiliza el precio de la primera variante y primera tienda disponible
   - Si no hay precio de tienda, se usa el precio predeterminado de la variante

2. **Cálculo del precio base en USD**:
   ```
   precio_base_usd = precio_loyverse / tasa_cambio
   ```
   Donde:
   - `precio_loyverse` es el precio del producto en Loyverse (en VES)
   - `tasa_cambio` es la tasa proporcionada como argumento al script

3. **Almacenamiento en la base de datos**:
   - El precio original de Loyverse se guarda en el campo `precio_base`
   - El precio calculado en USD se guarda en el campo `precio_base_usd`
   - Todos los productos se configuran con `tipo_tasa = 'PARALELO'`

## Verificación

Después de ejecutar el script, se recomienda verificar:

1. Que todos los productos se hayan importado correctamente
2. Que los precios en USD estén correctamente calculados
3. Que todos los productos tengan el tipo de tasa "PARALELO"

## Notas importantes

- Este script está diseñado para una sincronización inicial en una base de datos limpia
- No actualiza productos existentes; solo crea nuevos productos
- Registra información detallada en la consola y en el archivo `loyverse_initial_sync.log`
- Si la base de datos ya contiene productos, mostrará una advertencia y solicitará confirmación antes de continuar

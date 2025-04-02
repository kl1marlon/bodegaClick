# Funcionalidad de Creación de Productos

## Descripción General

La funcionalidad de creación de productos permite a los usuarios agregar nuevos productos tanto a la base de datos local como a Loyverse (sistema POS) desde la interfaz de BodegaClick. Esta característica facilita la gestión del inventario al permitir la creación rápida de productos con todos los datos necesarios, incluyendo:

- Información básica (nombre, descripción)
- Categoría (seleccionar existente o crear nueva)
- Precio de compra y precio de venta
- Configuración de inventario
- Aplicación de impuestos
- Tipo de tasa de cambio

## Implementación Técnica

### Frontend

La implementación del frontend consta de:

1. **Botón de acceso**: Se agregó un botón "Agregar Producto" en la página de listado de productos (`ListadoProductos.js`).
2. **Página de creación**: Se creó una nueva página (`CrearProducto.js`) con un formulario completo para ingresar todos los datos necesarios.
3. **Cálculos automáticos**: El precio base en USD se calcula automáticamente a partir del precio de compra, porcentaje de ganancia y si aplica IVA.
4. **Gestión de categorías**: Permite seleccionar categorías existentes o crear nuevas.
5. **Validaciones**: Verificación básica de campos requeridos y formatos válidos.

### Backend

En el backend se implementaron:

1. **Endpoint para categorías**: Para obtener todas las categorías existentes (`/api/productos/categorias/`).
2. **Endpoint de creación**: Para crear el producto tanto en la base de datos local como en Loyverse (`/api/productos/crear/`).
3. **Servicios Loyverse**:
   - `get_categories`: Para obtener las categorías desde Loyverse
   - `create_category`: Para crear nuevas categorías en Loyverse
   - `create_item`: Para crear productos en Loyverse

### Sincronización de Categorías

El sistema maneja la sincronización de categorías entre la base de datos local y Loyverse de la siguiente manera:

1. **Obtención de categorías**: Al cargar el formulario, se obtienen todas las categorías únicas existentes en la base de datos local.

2. **Al crear un producto**:
   - El backend verifica si la categoría proporcionada existe en Loyverse mediante una llamada a la API de Loyverse.
   - Si la categoría existe, utiliza su ID existente para asociar el producto.
   - Si la categoría no existe, crea automáticamente la categoría en Loyverse y obtiene el nuevo ID.
   - El backend registra en los logs cada paso de la verificación y creación de categorías.
   - El producto se crea en Loyverse con el ID de categoría correcto.
   - La categoría también se almacena como texto en la base de datos local para futuras referencias.

3. **Creación de categorías desde el frontend**:
   - El usuario puede crear una nueva categoría directamente desde el formulario.
   - El sistema verificará si esa categoría ya existe (ignorando mayúsculas/minúsculas).
   - La nueva categoría se agrega a la lista de selección y se establece como la categoría actual del producto.

### Flujo de creación de productos

1. El usuario hace clic en "Agregar Producto" desde la página de listado
2. Se carga el formulario de creación de productos con las categorías existentes
3. El usuario completa la información del producto
4. Al guardar:
   - Se validan los campos
   - Se crea la categoría en Loyverse si es necesario
   - Se crea el producto en Loyverse
   - Se guarda el producto en la base de datos local con el ID y variant_id recibidos
   - Se redirige al usuario al listado de productos

## Uso

### Acceso a la funcionalidad

1. Ingresar a la página de listado de productos
2. Hacer clic en el botón "Agregar Producto" situado en la esquina superior derecha

### Completar el formulario

El formulario de creación de productos está dividido en secciones:

#### Información Básica
- **Nombre del Producto**: Campo obligatorio
- **Descripción**: Campo opcional para detalles del producto

#### Categoría
- Selección de categoría existente, o
- Opción para crear una nueva categoría:
  1. Seleccionar "Crear nueva categoría" en el desplegable
  2. Ingresar el nombre de la nueva categoría
  3. Hacer clic en "Agregar"

#### Inventario
- **Seguimiento de inventario**: Habilitar/deshabilitar
- **Unidades por Paquete**: Cantidad de unidades en un paquete del producto

#### Información de Precios
- **Precio de Compra (USD)**: Campo obligatorio
- **Porcentaje de Ganancia (%)**: Para calcular el precio de venta
- **Aplicar IVA (16%)**: Opción para incluir IVA en el precio
- **Tipo de Tasa**: BCV o Paralelo para conversiones Bs/USD
- **Precio Base (USD)**: Calculado automáticamente a partir del precio de compra, porcentaje de ganancia, unidades por paquete y aplicación de IVA
- **Precio en Bolívares**: Muestra el equivalente en Bs con las reglas de redondeo aplicadas
- **Precio Variable**: Opción para precios variables al momento de venta

### Cálculo del Precio Base USD

El precio base USD se calcula automáticamente siguiendo estos pasos:
1. Se divide el precio de compra USD entre las unidades por paquete para obtener el costo unitario
2. Se aplica el porcentaje de ganancia: `precio_unitario * (1 + porcentaje_ganancia/100)`
3. Si está activado "Aplicar IVA", se multiplica por 1.16 (16% IVA)
4. El resultado se redondea a 2 decimales

### Guardado y Sincronización

Al hacer clic en "Guardar Producto", el sistema:
1. Crea el producto en Loyverse
2. Guarda el producto en la base de datos local
3. Vincula ambos mediante IDs
4. Redirige al listado de productos actualizado

## Consideraciones Técnicas

- La creación de categorías en Loyverse es automática si no existe
- Los precios se calculan automáticamente basados en porcentaje de ganancia
- La redirección ocurre después de 2 segundos para permitir ver la confirmación
- Se mantienen los IDs de Loyverse para sincronización
- El sistema incluye logs detallados en el backend para rastrear el proceso de creación

## Posibles Mejoras Futuras

- Agregar soporte para imágenes de productos
- Implementar clonación de productos existentes
- Permitir la creación de productos con variantes (tallas, colores)
- Mejorar la validación de campos con mensajes de error específicos
- Agregar campo de código de barras manual
- Implementar una vista previa de cómo se verá el producto en Loyverse
- Añadir la funcionalidad de importación masiva de productos 
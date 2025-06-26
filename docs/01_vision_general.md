# Visión General y Arquitectura de BodegaClick

## 1. Introducción

BodegaClick es un sistema integral de gestión de inventario y facturación desarrollado con Django, diseñado específicamente para negocios que operan en entornos con múltiples monedas. El sistema se integra con Loyverse, una plataforma de punto de venta (POS), para sincronizar productos, precios e inventario en tiempo real.

La característica distintiva de BodegaClick es su capacidad para manejar precios en dólares estadounidenses (USD) y bolívares venezolanos (BS), utilizando dos tasas de cambio diferentes (BCV y PARALELO) y aplicando lógicas de redondeo especiales para optimizar los precios de venta.

## 2. Objetivos del Sistema

- **Gestión centralizada de inventario**: Mantener un registro actualizado de todos los productos, sus precios y niveles de stock.
- **Sincronización con Loyverse**: Garantizar que los datos del sistema estén siempre sincronizados con el punto de venta.
- **Manejo de múltiples monedas**: Facilitar operaciones en USD y BS con conversiones automáticas basadas en tasas de cambio actualizadas.
- **Automatización de precios**: Calcular y actualizar precios de forma masiva según tasas de cambio y porcentajes de ganancia.
- **Facturación eficiente**: Generar facturas con cálculos precisos de precios, impuestos y ganancias.
- **Reportes y análisis**: Proporcionar información detallada sobre ventas, inventario y rentabilidad.

## 3. Arquitectura Técnica

### 3.1 Stack Tecnológico

- **Backend**: Django 4.2 (Python)
- **Frontend**: React.js con Material-UI
- **Base de datos**: PostgreSQL
- **Caché y tareas asíncronas**: Redis y Celery
- **Despliegue**: Docker, Railway, AWS
- **Integración externa**: API REST de Loyverse

### 3.2 Componentes Principales

#### Backend (Django)

- **facturacion**: App principal que maneja productos, tasas de cambio, facturas y webhooks.
- **config**: Configuración central de Django, URLs y middlewares.
- **scripts**: Utilidades para actualización de precios y sincronización con Loyverse.
- **loyverse_sync**: Módulo específico para la integración con la API de Loyverse.
- **webhook**: Gestión de eventos y notificaciones desde Loyverse.

#### Frontend (React)

- **Páginas principales**:
  - Dashboard
  - Listado de Productos
  - Creación de Productos
  - Listado de Facturas
  - Nueva Factura
  - Búsqueda de Productos y Historial

- **Componentes reutilizables**:
  - Selección de Tasa de Cambio
  - Notificaciones de Inventario
  - Buscador de Productos
  - Layout y Navegación

### 3.3 Modelo de Datos

#### Entidades Principales

1. **Producto**:
   - Información básica (nombre, descripción, categoría)
   - Precios (base, compra, venta) en USD y BS
   - Configuración de ganancia y tipo de tasa
   - Información de stock y sincronización con Loyverse

2. **TasaCambio**:
   - Tipos: BCV y PARALELO
   - Valor y fecha de actualización

3. **Factura**:
   - Información general (número, fecha, moneda)
   - Totales en USD y BS
   - Estado de sincronización con Loyverse

4. **DetalleFactura**:
   - Relación con Factura y Producto
   - Cantidad, precio unitario y total
   - Información de ganancia y configuración

5. **Webhook**:
   - Configuración de eventos de Loyverse
   - Estado y tipo de notificación

## 4. Flujos de Datos Principales

### 4.1 Actualización de Precios Base

1. El sistema obtiene las tasas de cambio actuales (BCV y PARALELO).
2. Para cada producto, calcula el precio base según la tasa correspondiente.
3. Aplica lógicas de redondeo especiales para precios en bolívares.
4. Actualiza los precios en la base de datos local.
5. Opcionalmente sincroniza los nuevos precios con Loyverse.

### 4.2 Sincronización con Loyverse

#### De BodegaClick a Loyverse:
1. El sistema recopila los productos actualizados localmente.
2. Compara los precios locales con los de Loyverse.
3. Actualiza solo los productos con diferencias de precio.
4. Registra los resultados de la sincronización.

#### De Loyverse a BodegaClick:
1. Loyverse envía notificaciones vía webhooks cuando hay cambios.
2. El sistema procesa estos eventos y actualiza la base de datos local.
3. Se mantiene un registro de todas las actualizaciones.

### 4.3 Proceso de Facturación

1. El usuario selecciona productos y cantidades.
2. El sistema calcula precios según la moneda y tasa seleccionadas.
3. Se aplican porcentajes de ganancia y posibles impuestos.
4. Se genera la factura en la base de datos.
5. Opcionalmente, se actualiza el inventario en Loyverse.

## 5. Despliegue y Entornos

### 5.1 Entorno Local (Desarrollo)

- Docker y Docker Compose para contenedores de servicios
- Variables de entorno en archivo `.env`
- Sincronización manual con Loyverse

### 5.2 Railway (Producción/Pruebas)

- Despliegue automatizado desde repositorio Git
- Variables de entorno configuradas en la plataforma
- Tareas programadas para sincronización periódica

### 5.3 AWS (Alternativa de Producción)

- Servicios utilizados: EC2, RDS, Lambda
- Configuración de alta disponibilidad
- Tareas programadas mediante CloudWatch Events

## 6. Consideraciones de Seguridad

- Autenticación para acceso al sistema
- Token de API de Loyverse almacenado de forma segura
- CORS configurado para permitir solo orígenes específicos
- Validación de datos en todas las entradas de usuario
- Protección contra inyección SQL mediante ORM de Django

## 7. Extensibilidad y Mantenimiento

El sistema está diseñado con modularidad para facilitar:

- Incorporación de nuevas funcionalidades
- Adaptación a cambios en la API de Loyverse
- Soporte para múltiples monedas adicionales
- Escalabilidad para manejar mayor volumen de productos y transacciones
- Mejoras en la lógica de precios y redondeo

## 8. Próximos Pasos y Mejoras Planificadas

- Implementación de dashboard con métricas en tiempo real
- Mejoras en la interfaz de usuario para dispositivos móviles
- Optimización de consultas para mejor rendimiento con grandes volúmenes de datos
- Integración con sistemas de contabilidad
- Exportación de reportes en múltiples formatos

---

*Última actualización: 26 de junio de 2025*

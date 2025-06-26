# API Reference

## Introducción

Esta documentación describe los endpoints de la API REST de BodegaClick. La API permite interactuar con los recursos del sistema, como productos, facturas, tasas de cambio y webhooks.

**URL Base**: `/api/`

## Autenticación

Actualmente, la mayoría de los endpoints están abiertos para facilitar el desarrollo. Sin embargo, endpoints sensibles como la sincronización de inventario pueden requerir un token de administrador (`x-admin-token`) en la cabecera.

## Endpoints Principales

### Productos (`/api/productos/`)

#### `GET /api/productos/`

- **Descripción**: Obtiene una lista de todos los productos.
- **Respuesta Exitosa (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "loyverse_id": "...",
      "variant_id": "...",
      "nombre": "Producto de Ejemplo",
      "precio_base": "10.00",
      "precio_compra_usd": "5.00",
      "stock_actual": "100.00",
      "categoria": "General",
      "aplicar_iva": false,
      "fuente_actualizacion": "loyverse",
      "porcentaje_ganancia": "30.00",
      "tipo_tasa": "BCV",
      "es_precio_variable": false
    }
  ]
  ```

#### `POST /api/productos/`

- **Descripción**: Crea un nuevo producto.
- **Cuerpo de la Petición**:
  ```json
  {
    "nombre": "Nuevo Producto",
    "precio_base_usd": 15.00,
    "precio_compra_usd": 10.00,
    "porcentaje_ganancia": 30.00,
    "unidades_paquete": 1,
    "aplicar_iva": false,
    "tipo_tasa": "PARALELO"
  }
  ```
- **Respuesta Exitosa (201 Created)**: Devuelve el objeto del producto creado.

#### `GET /api/productos/{id}/`

- **Descripción**: Obtiene los detalles de un producto específico.
- **Respuesta Exitosa (200 OK)**: Devuelve el objeto del producto.

#### `PUT /api/productos/{id}/` & `PATCH /api/productos/{id}/`

- **Descripción**: Actualiza un producto existente.
- **Cuerpo de la Petición**: Objeto con los campos a actualizar.
- **Respuesta Exitosa (200 OK)**: Devuelve el objeto del producto actualizado.

#### `DELETE /api/productos/{id}/`

- **Descripción**: Elimina un producto.
- **Respuesta Exitosa (204 No Content)**.

---

### Tasas de Cambio (`/api/tasas-cambio/`)

#### `GET /api/tasas-cambio/`

- **Descripción**: Obtiene una lista de todas las tasas de cambio registradas, ordenadas por fecha descendente.
- **Respuesta Exitosa (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "tipo": "BCV",
      "valor": "36.50",
      "fecha": "2025-06-26T15:00:00Z"
    }
  ]
  ```

#### `GET /api/tasas-cambio/latest/?tipo={tipo}`

- **Descripción**: Obtiene la última tasa de cambio para un tipo específico (`BCV` o `PARALELO`).
- **Parámetros de Consulta**:
  - `tipo` (string, opcional, default: `BCV`): `BCV` o `PARALELO`.
- **Respuesta Exitosa (200 OK)**: Devuelve el objeto de la tasa de cambio.

---

### Facturas (`/api/facturas/`)

#### `GET /api/facturas/`

- **Descripción**: Obtiene una lista de todas las facturas.
- **Respuesta Exitosa (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "numero": "F20250626-1234",
      "fecha": "2025-06-26T15:00:00Z",
      "moneda": "USD",
      "tasa_cambio": 1,
      "tasa_cambio_valor": "36.50",
      "total_bs": "3650.00",
      "total_usd": "100.00",
      "detalles": [
        {
          "id": 1,
          "producto": 1,
          "producto_nombre": "Producto de Ejemplo",
          "cantidad": "10.00",
          "precio_unitario": "10.00",
          "total": "100.00"
        }
      ]
    }
  ]
  ```

#### `POST /api/facturas/`

- **Descripción**: Crea una nueva factura.
- **Cuerpo de la Petición**:
  ```json
  {
    "moneda": "USD",
    "tasa_cambio": 1,
    "porcentaje_ganancia": 30.00,
    "detalles": [
      {
        "producto": 1,
        "cantidad": "10.00",
        "precio_unitario": "10.00",
        "precio_compra_usd": "5.00",
        "unidades_paquete": "1.00"
      }
    ]
  }
  ```
- **Respuesta Exitosa (201 Created)**: Devuelve el objeto de la factura creada.

#### `GET /api/facturas/{id}/`

- **Descripción**: Obtiene los detalles de una factura específica.
- **Respuesta Exitosa (200 OK)**: Devuelve el objeto de la factura.

---

### Webhooks (`/api/webhooks/`)

#### `GET /api/webhooks/`

- **Descripción**: Lista todos los webhooks configurados.
- **Respuesta Exitosa (200 OK)**:
  ```json
  [
    {
      "id": "uuid-string",
      "merchant_id": "uuid-string",
      "url": "https://example.com/webhook",
      "type": "inventory_levels.update",
      "status": "ENABLED"
    }
  ]
  ```

#### `POST /api/webhooks/`

- **Descripción**: Crea un nuevo webhook.
- **Cuerpo de la Petición**:
  ```json
  {
    "url": "https://example.com/webhook",
    "type": "inventory_levels.update"
  }
  ```
- **Respuesta Exitosa (201 Created)**: Devuelve el objeto del webhook creado.

---

## Endpoints de Sincronización y Acciones

#### `POST /api/productos/sync_from_loyverse/`

- **Descripción**: Sincroniza productos desde Loyverse a la base de datos local.
- **Cuerpo de la Petición (opcional)**:
  ```json
  {
    "actualizar_precios": false,
    "categorias": ["Bebidas"],
    "tipo_tasa": "PARALELO",
    "productos_ids": [1, 2, 3],
    "tamaño_lote": 50
  }
  ```
- **Respuesta Exitosa (200 OK)**: Devuelve un resumen de la sincronización.

#### `POST /api/productos/calcular_precios/`

- **Descripción**: Calcula precios de venta para productos.
- **Cuerpo de la Petición**:
  ```json
  {
    "producto_id": 1,
    "porcentaje_ganancia": 35.00
  }
  ```
  o
  ```json
  {
    "factura_id": 1
  }
  ```
- **Respuesta Exitosa (200 OK)**: Devuelve un resumen de los precios calculados.

#### `POST /api/actualizar-precios-base/`

- **Descripción**: Actualiza los precios base de todos los productos según las tasas de cambio actuales.
- **Respuesta Exitosa (200 OK)**: Devuelve un resumen de la actualización.

#### `POST /api/sincronizar-inventario/`

- **Descripción**: Sincroniza los niveles de inventario con Loyverse.
- **Cabeceras**: Requiere `X-Admin-Token`.
- **Cuerpo de la Petición**:
  ```json
  {
    "solo_sin_stock": true
  }
  ```
- **Respuesta Exitosa (200 OK)**: Devuelve un resumen de la sincronización de inventario.

---

## Endpoints de Tareas Asíncronas

#### `GET /api/tareas/iniciar/`

- **Descripción**: Inicia una tarea asíncrona (ej. sincronización).
- **Respuesta Exitosa (202 Accepted)**:
  ```json
  {
    "task_id": "uuid-string"
  }
  ```

#### `GET /api/tareas/estado/{task_id}/`

- **Descripción**: Consulta el estado de una tarea asíncrona.
- **Respuesta Exitosa (200 OK)**:
  ```json
  {
    "task_id": "uuid-string",
    "status": "SUCCESS",
    "result": { ... }
  }
  ```

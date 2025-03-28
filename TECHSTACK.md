# Stack Tecnológico BodegaClick

## Backend
- Lenguaje: Python (archivos .py, manage.py)
- Framework: Django (estructura detectada)
- Base de datos: PostgreSQL (por referencia en scripts)
- Docker: Configuración detectada (Dockerfile, docker-compose.yml)

## Frontend
- Framework: React (package.json, estructura src/public)
- Build tool: npm
- Web server: Nginx (configuración detectada)

## DevOps
- Docker Compose: Orquestación de contenedores
- Implementación: Configuraciones Docker para backend/frontend

## Scripts Notables
- Sync_products.py: Integración con Loyverse
- Ver_datos_bdd.py: Utilidades de base de datos
- Test_connection.py: Pruebas de conectividad

## Estructura del Proyecto

```
bodegaClick/
├── .env.example                # Ejemplo de variables de entorno
├── .gitignore                  # Archivos ignorados por git
├── docker-compose.yml          # Configuración de servicios Docker
├── railway.json                # Configuración para despliegue en Railway
├── README.md                   # Documentación principal
├── TECHSTACK.md                # Documentación técnica (este archivo)
│
├── backend/                    # Aplicación Django (API y lógica de negocio)
│   ├── .dockerignore           # Archivos ignorados en la imagen Docker
│   ├── Dockerfile              # Configuración para construir imagen Docker
│   ├── manage.py               # Script de administración de Django
│   ├── requirements.txt        # Dependencias Python
│   ├── check_products.py       # Script para verificar productos
│   ├── create_webhook.py       # Script para crear webhooks en Loyverse
│   ├── sync_products.py        # Script de sincronización con Loyverse
│   ├── test_connection.py      # Script para probar conexiones
│   ├── test_tasas.py           # Script para probar tasas de cambio
│   ├── ver_datos_bdd.py        # Utilidad para visualizar datos de la BD
│   │
│   ├── config/                 # Configuración principal de Django
│   │   ├── asgi.py             # Configuración ASGI para servidores como Daphne
│   │   ├── settings.py         # Configuración de Django
│   │   ├── urls.py             # Rutas principales de la API
│   │   └── wsgi.py             # Configuración WSGI para servidores como Gunicorn
│   │
│   ├── facturacion/            # Aplicación principal de facturación
│   │   ├── admin.py            # Configuración del panel de administración
│   │   ├── consumers.py        # Consumidores para WebSockets
│   │   ├── migrations/         # Migraciones de la base de datos
│   │   ├── models.py           # Modelos de datos (ORM)
│   │   ├── routing.py          # Rutas para WebSockets
│   │   ├── serializers.py      # Serializadores para la API REST
│   │   ├── services.py         # Servicios y lógica de negocio
│   │   └── views.py            # Vistas y endpoints de la API
│   │
│   └── loyverse_sync/          # Módulo de sincronización con Loyverse
│       └── ...                 # Archivos para integración con Loyverse
│
└── frontend/                   # Aplicación React (interfaz de usuario)
    ├── .dockerignore           # Archivos ignorados en la imagen Docker
    ├── Dockerfile              # Configuración para construir imagen Docker
    ├── nginx.conf              # Configuración de Nginx para servir la app
    ├── package.json            # Dependencias y scripts npm
    ├── public/                 # Archivos públicos estáticos
    │   └── ...                 # Favicon, index.html, etc.
    │
    └── src/                    # Código fuente de React
        ├── App.js              # Componente principal de la aplicación
        ├── index.js            # Punto de entrada de la aplicación
        ├── index.css           # Estilos globales
        ├── theme.js            # Configuración del tema visual
        │
        ├── components/         # Componentes reutilizables
        │   └── ...             # Botones, formularios, tablas, etc.
        │
        ├── pages/              # Páginas/vistas de la aplicación
        │   └── ...             # Página de inicio, productos, facturas, etc.
        │
        ├── services/           # Servicios para comunicación con la API
        │   └── ...             # Clientes HTTP, funciones de autenticación, etc.
        │
        ├── store/              # Estado global (Redux)
        │   └── ...             # Acciones, reducers, store, etc.
        │
        └── utils/              # Utilidades y funciones auxiliares
            └── ...             # Formateo de datos, validaciones, etc.
```

### Descripción de Componentes Principales

#### Backend

1. **config/**
   - Núcleo de configuración de Django
   - `settings.py`: Configuración principal (BD, apps, middleware, etc.)
   - `urls.py`: Enrutamiento de la API
   - `asgi.py` y `wsgi.py`: Interfaces para servidores web

2. **facturacion/**
   - Aplicación principal del sistema
   - `models.py`: Define la estructura de la base de datos
   - `views.py`: Implementa los endpoints de la API REST
   - `serializers.py`: Convierte objetos Python a JSON y viceversa
   - `services.py`: Contiene la lógica de negocio principal
   - `consumers.py`: Maneja conexiones WebSocket para actualizaciones en tiempo real

3. **loyverse_sync/**
   - Módulo para integración con Loyverse POS
   - Contiene clases y funciones para sincronizar productos, ventas, etc.

4. **Scripts Principales**
   - `sync_products.py`: Sincroniza productos entre Loyverse y la base de datos local
   - `ver_datos_bdd.py`: Herramienta para inspeccionar datos en la base de datos
   - `test_connection.py`: Verifica la conectividad con servicios externos
   - `create_webhook.py`: Configura webhooks en Loyverse para recibir notificaciones

#### Frontend

1. **src/components/**
   - Componentes React reutilizables
   - Incluye elementos de UI como tablas, formularios, botones, etc.

2. **src/pages/**
   - Páginas completas de la aplicación
   - Cada archivo representa una vista diferente (dashboard, productos, ventas, etc.)

3. **src/services/**
   - Funciones para comunicación con la API backend
   - Maneja peticiones HTTP, autenticación, etc.

4. **src/store/**
   - Implementación de Redux para gestión del estado global
   - Incluye acciones, reducers y configuración del store

5. **src/utils/**
   - Funciones utilitarias para formateo, validación, etc.
   - Código auxiliar reutilizable en toda la aplicación

## Flujo de Inicio de la Aplicación

### Requisitos Previos
- Docker y Docker Compose instalados
- Token de API de Loyverse
- Git para clonar el repositorio

### Pasos para Iniciar la Aplicación Localmente
1. **Configuración del Entorno**:
   - Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:
     ```
     POSTGRES_DB=bodegaclick
     POSTGRES_USER=usuario
     POSTGRES_PASSWORD=contraseña
     LOYVERSE_API_TOKEN=tu_token_de_loyverse
     DEBUG=True
     SECRET_KEY=your-secret-key-here
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

2. **Iniciar los Servicios con Docker Compose**:
   - Ejecutar `docker-compose up -d` en la raíz del proyecto
   - Esto iniciará tres servicios:
     - **db**: Base de datos PostgreSQL
     - **backend**: Servidor Django en el puerto 8000
     - **frontend**: Aplicación React servida por Nginx en el puerto 3000

3. **Verificar el Estado de los Servicios**:
   - Ejecutar `docker-compose ps` para verificar que todos los servicios estén en estado "Up"

4. **Acceder a la Aplicación**:
   - Frontend: http://localhost:3000
   - API Backend: http://localhost:8000/api
   - Admin Django: http://localhost:8000/admin

5. **Sincronización con Loyverse** (opcional):
   - Ejecutar `docker-compose run backend python sync_products.py` para sincronizar productos con Loyverse

## Guía de Despliegue en Railway

Railway es una plataforma PaaS que facilita el despliegue de aplicaciones containerizadas. A continuación, se detallan los pasos para desplegar BodegaClick en Railway:

### 1. Preparación Inicial

1. **Instalar Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Inicializar el Proyecto en Railway**:
   ```bash
   cd bodegaClick
   railway init
   ```
   - Seleccionar "Create a new project" cuando se solicite

### 2. Configuración de la Base de Datos

1. **Agregar Servicio de PostgreSQL**:
   - Desde el dashboard de Railway, ir a "New Service" → "Database" → "PostgreSQL"
   - Railway generará automáticamente las credenciales y la URL de conexión

2. **Vincular la Base de Datos al Proyecto**:
   - En el dashboard de Railway, asegurarse de que la base de datos esté vinculada al proyecto

### 3. Configuración de Variables de Entorno

1. **Configurar Variables en Railway**:
   - En el dashboard de Railway, ir a "Variables"
   - Agregar las siguientes variables:
     ```
     POSTGRES_DB=bodegaclick
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=<generado-por-railway>
     LOYVERSE_API_TOKEN=<tu-token-de-loyverse>
     DEBUG=False
     SECRET_KEY=<generar-clave-segura>
     ALLOWED_HOSTS=.railway.app
     DATABASE_URL=<proporcionado-por-railway>
     RAILWAY_DOCKERFILE_PATH=Dockerfile
     PORT=8000
     ```

### 4. Despliegue del Backend

1. **Preparar el Dockerfile del Backend**:
   - Asegurarse de que el Dockerfile en la carpeta `backend` tenga un comando CMD para iniciar la aplicación:
   ```
   CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p $PORT config.asgi:application"]
   ```

2. **Desplegar el Backend**:
   ```bash
   cd backend
   railway up
   ```

3. **Ejecutar Migraciones** (si es necesario):
   ```bash
   railway run python manage.py migrate
   ```

### 5. Despliegue del Frontend

1. **Modificar la Configuración del Frontend**:
   - Actualizar la URL de la API en el frontend para que apunte al backend desplegado
   - En el archivo `.env` del frontend:
   ```
   REACT_APP_API_URL=https://<backend-url>.railway.app/api
   ```

2. **Desplegar el Frontend**:
   ```bash
   cd frontend
   railway up
   ```

### 6. Configuración de Dominios (Opcional)

1. **Configurar Dominios Personalizados**:
   - En el dashboard de Railway, ir a "Settings" → "Domains"
   - Agregar dominios personalizados para el backend y frontend

### 7. Configuración de Tareas Programadas

1. **Configurar Sincronización Periódica con Loyverse**:
   ```bash
   railway cron add "0 */6 * * *" "python sync_products.py"
   ```

### 8. Monitoreo y Logs

1. **Verificar Logs**:
   - En el dashboard de Railway, ir a "Deployments" → seleccionar el despliegue → "Logs"
   - Monitorear los logs para detectar posibles errores

### 9. Escalado (Opcional)

1. **Ajustar Recursos**:
   - En el dashboard de Railway, ir a "Settings" → "Resources"
   - Ajustar CPU y memoria según las necesidades

⚠️ **Observaciones**:
- Sistema en fase de desarrollo local
- Configuraciones de Docker listas para producción
- Integración activa con API de Loyverse
- El despliegue en Railway aprovecha los Dockerfiles existentes
- Las variables de entorno son críticas para el funcionamiento correcto

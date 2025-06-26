# Guía para Desarrolladores

## Visión General

Esta guía está diseñada para ayudar a los desarrolladores a comprender la estructura, convenciones y flujos de trabajo en el proyecto BodegaClick. El objetivo es facilitar la incorporación de nuevos miembros al equipo y mantener la consistencia en el desarrollo.

## Estructura del Proyecto

BodegaClick sigue una arquitectura cliente-servidor con un backend Django y un frontend React. La estructura general es la siguiente:

```
bodegaClick/
│
├── backend/               # Servidor Django
│   ├── config/           # Configuración general del proyecto
│   ├── facturacion/      # Aplicación principal de facturación e inventario
│   ├── loyverse_sync/    # Módulos para sincronización con Loyverse
│   ├── scripts/          # Scripts de utilidad y mantenimiento
│   └── webhook/          # Gestión de webhooks para Loyverse
│
├── frontend/             # Cliente React
│   ├── public/           # Archivos estáticos y configuración pública
│   └── src/              # Código fuente React
│       ├── components/   # Componentes reutilizables
│       ├── context/      # Contextos React
│       ├── pages/        # Páginas de la aplicación
│       ├── services/     # Servicios y conexión a API
│       ├── store/        # Estado global con Redux
│       └── utils/        # Utilidades varias
│
├── docs/                 # Documentación del proyecto
└── scripts/              # Scripts de nivel raíz
```

### Backend (Django)

#### Estructura de Aplicaciones

El backend está organizado siguiendo la estructura estándar de Django:

1. **facturacion**: Aplicación principal que gestiona el inventario, facturas, productos y tasas de cambio.
2. **loyverse_sync**: Módulo encargado de la comunicación con la API de Loyverse.
3. **webhook**: Gestión de eventos recibidos desde Loyverse a través de webhooks.

#### Estructura de Archivos por Aplicación

Cada aplicación Django sigue un patrón similar:

```
facturacion/
├── admin.py              # Configuración del panel de administración
├── models.py             # Modelos de datos
├── serializers.py        # Serializadores para la API REST
├── services.py           # Servicios y lógica de negocio
├── urls.py               # Mapeo de URLs
├── views.py              # Vistas principales
├── views_*.py            # Vistas adicionales organizadas por funcionalidad
├── management/           # Comandos personalizados
│   └── commands/         # Implementación de comandos Django
└── templates/            # Plantillas HTML
```

### Frontend (React)

El frontend está organizado siguiendo una estructura modular:

```
src/
├── components/           # Componentes reutilizables
├── context/              # Contextos de React (AuthContext, etc.)
├── pages/                # Páginas principales de la aplicación
├── services/             # Servicios para conectar con la API
├── store/                # Estado global con Redux
│   ├── index.js          # Configuración de store
│   └── *Slice.js         # Slices de Redux Toolkit
└── utils/                # Utilidades y helpers
```

## Stack Tecnológico

### Backend

- **Framework principal**: Django 4.2
- **API REST**: Django REST Framework
- **Base de datos**: PostgreSQL
- **Caché y tareas**: Redis + Celery
- **Despliegue**: Configuración para Docker y Railway

### Frontend

- **Framework principal**: React 18
- **Gestión de estado**: Redux Toolkit
- **UI Framework**: Material UI 5
- **Routing**: React Router 6
- **Formularios**: Formik + Yup
- **Cliente HTTP**: Axios
- **Visualización**: Recharts

## Convenciones de Código

### Python (Backend)

1. **Estilo de código**: Seguir PEP 8
   - Indentación de 4 espacios
   - Nombres de variables y funciones en snake_case
   - Nombres de clases en PascalCase
   - Líneas de máximo 79 caracteres

2. **Modelos**:
   - Nombres en singular (ej. `Producto`, no `Productos`)
   - Atributos descriptivos
   - Implementar método `__str__` para representación legible

3. **Vistas**:
   - Organizar por funcionalidad en archivos separados cuando crezcan demasiado
   - Para vistas complejas, usar ViewSets de DRF
   - Para vistas simples, usar APIView o vistas basadas en funciones

4. **Servicios**:
   - La lógica de negocio compleja debe ir en clases de servicio
   - Los servicios deben ser testables independientemente

### JavaScript (Frontend)

1. **Estilo de código**:
   - Usar ES6+ con sintaxis moderna
   - Preferir funciones de flecha (arrow functions)
   - Usar destructuring para props y estados
   - Nombres de variables y funciones en camelCase
   - Nombres de componentes y clases en PascalCase

2. **Componentes React**:
   - Preferir componentes funcionales con hooks
   - Separar la lógica de presentación y estado cuando sea posible
   - Usar prop-types o TypeScript para tipado

3. **Gestión de estado**:
   - Estado local con useState para estado simple de componentes
   - Context API para estado compartido entre componentes cercanos
   - Redux para estado global y complejo

4. **Peticiones API**:
   - Centralizar en el directorio `services`
   - Usar async/await para manejo asíncrono

## Flujos de Desarrollo

### Instalación del Entorno de Desarrollo

1. Clonar el repositorio
2. Configurar variables de entorno según `docs/02_instalacion_configuracion.md`
3. Instalar dependencias del backend y frontend
4. Iniciar servicios (PostgreSQL, Redis)
5. Ejecutar migraciones y cargar datos iniciales

### Ciclo de Desarrollo

1. **Implementar cambios**:
   - Backend: Desarrollar modelos, serializers, views, etc.
   - Frontend: Desarrollar componentes, páginas, estado, etc.

2. **Pruebas locales**:
   - Backend: Ejecutar `python manage.py test`
   - Frontend: Ejecutar `npm test`

3. **Despliegue**:
   - Seguir el flujo de CI/CD configurado en Railway
   - Verificar logs post-despliegue

## Pruebas (Testing)

### Backend

El backend utiliza el framework de pruebas de Django. Ejecutar las pruebas:

```bash
cd backend
python manage.py test
```

Los tests están organizados según la estructura de Django:

```
facturacion/
└── tests/
    ├── test_models.py    # Pruebas para modelos
    ├── test_views.py     # Pruebas para vistas
    └── test_services.py  # Pruebas para servicios
```

### Frontend

El frontend utiliza Jest y React Testing Library. Ejecutar las pruebas:

```bash
cd frontend
npm test
```

Los tests están típicamente colocados junto a los componentes que prueban con la extensión `.test.js`.

## Solución de Problemas Comunes

### Problemas de Conexión con Loyverse

1. Verificar que el token API es válido en las variables de entorno
2. Comprobar la conectividad mediante `test_connection.py`
3. Revisar los logs en `backend/scripts/sync_loyverse_products.py`

### Errores de Base de Datos

1. Verificar la conexión a PostgreSQL con `test_coolify_connection.py`
2. Asegurarse de que las migraciones están actualizadas: `python manage.py showmigrations`
3. Comprobar si hay conflictos en migraciones

### Problemas con Redis y Celery

1. Verificar la conexión a Redis con `test_redis.py`
2. Comprobar los logs de Celery para tareas fallidas
3. Asegurarse de que Celery está ejecutándose correctamente

## Buenas Prácticas de Desarrollo

1. **Mantener la Documentación Actualizada**:
   - Documentar las funciones y clases con docstrings
   - Actualizar los documentos técnicos cuando se implementen cambios significativos

2. **Control de Versiones**:
   - Realizar commits pequeños y con mensajes descriptivos
   - Seguir el flujo de trabajo basado en ramas (feature branches)

3. **Seguridad**:
   - No hardcodear credenciales ni tokens
   - Usar variables de entorno para toda la configuración sensible
   - Implementar validación de datos en todas las entradas de usuario

4. **Rendimiento**:
   - Optimizar consultas a la base de datos (usar select_related y prefetch_related)
   - Implementar caché para operaciones costosas
   - Paginar respuestas API cuando devuelvan muchos elementos

5. **Integración Continua**:
   - Ejecutar tests antes de hacer push
   - Revisar los logs de despliegue en Railway

## Extensiones Recomendadas

### Para VS Code

- Python Extension Pack
- Django Extension Pack
- ESLint
- Prettier
- React Developer Tools
- Redux DevTools

## Recursos y Referencias

1. **Documentación oficial**:
   - [Django](https://docs.djangoproject.com/)
   - [Django REST Framework](https://www.django-rest-framework.org/)
   - [React](https://reactjs.org/docs/getting-started.html)
   - [Redux Toolkit](https://redux-toolkit.js.org/)
   - [Material UI](https://mui.com/)

2. **API de Loyverse**:
   - [Documentación de API Loyverse](https://developer.loyverse.com/docs)

3. **Documentación Interna**:
   - Ver carpeta `/docs` para documentación técnica detallada del proyecto

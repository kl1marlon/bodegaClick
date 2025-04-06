# Ejecutar BodegaClick en Entorno Local

Este documento proporciona instrucciones para ejecutar BodegaClick en un entorno local de desarrollo.

## Requisitos Previos

- Docker y Docker Compose
- Git

## Pasos para Ejecutar

### 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd bodegaClick
```

### 2. Configurar Variables de Entorno

Los archivos `.env` ya están configurados para el entorno local:

- `.env` (archivo principal)
- `backend/.env` (para el backend)
- `frontend/.env` (para el frontend)

### 3. Iniciar los Servicios con Docker Compose

```bash
docker-compose up -d
```

Esto iniciará los siguientes servicios:
- PostgreSQL (base de datos)
- Redis (para Celery y caché)
- Backend (Django)
- Worker (Celery)
- Frontend (React)

### 4. Verificar que los Servicios Estén Funcionando

```bash
docker-compose ps
```

### 5. Acceder a la Aplicación

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin de Django: http://localhost:8000/admin

### 6. Inicializar la Base de Datos (Si es Necesario)

Si necesitas cargar datos iniciales, puedes ejecutar:

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 7. Logs y Depuración

Para ver los logs de un servicio específico:

```bash
docker-compose logs -f backend  # para backend
docker-compose logs -f worker   # para worker
docker-compose logs -f frontend # para frontend
```

### 8. Detener los Servicios

```bash
docker-compose down
```

Si deseas eliminar también los volúmenes (esto borrará los datos persistentes):

```bash
docker-compose down -v
```

## Solución de Problemas

### Problemas de Conexión a la Base de Datos

Si tienes problemas para conectarte a la base de datos, asegúrate de que:

1. El servicio de PostgreSQL esté en ejecución
2. Las variables de entorno `DATABASE_URL` y `DATABASE_PUBLIC_URL` estén correctamente configuradas

### Problemas con Redis y Celery

Si las tareas de Celery no se están ejecutando:

1. Verifica que Redis esté funcionando: `docker-compose exec redis redis-cli ping`
2. Revisa los logs del worker: `docker-compose logs -f worker`

### Problemas con el Frontend

Si el frontend no muestra datos del backend:

1. Asegúrate de que `REACT_APP_API_URL` esté configurado correctamente
2. Verifica que el backend esté funcionando y respondiendo a las solicitudes API
3. Comprueba las conexiones CORS en la configuración del backend

## Notas Adicionales

- Para desarrollo local, se recomienda usar `docker-compose up` sin la opción `-d` para ver los logs en tiempo real.
- Puedes modificar los archivos y el código mientras los contenedores están en ejecución; los cambios se reflejarán automáticamente gracias a los volúmenes montados. 
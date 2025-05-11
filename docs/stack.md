# Stack Tecnológico de BodegaClick

## Arquitectura General

BodegaClick es un sistema de gestión de inventario y ventas, diseñado bajo una arquitectura moderna basada en microservicios y contenedores. El stack tecnológico permite escalabilidad, portabilidad y facilidad de despliegue en plataformas cloud.

---

## Componentes Principales

### Backend
- **Framework:** Django 4.2.0 + Django REST Framework 3.14.0
- **Procesamiento Asíncrono:** Celery 5.4.0 + Redis 5.2.1
- **Servidor Web:** Gunicorn 21.2.0
- **Base de Datos:** PostgreSQL 13
- **Integraciones:** API Loyverse para sincronización de inventario y ventas, sistema de webhooks para eventos en tiempo real

### Frontend
- **Framework:** React (Node.js 16)
- **Servidor Web:** Nginx
- **Configuración Dinámica:** Variables de entorno inyectadas en build y runtime

### Orquestación y Contenerización
- **Docker y Docker Compose:** Todos los servicios (frontend, backend, db, redis) están contenerizados y definidos en `docker-compose.yml`.
- **Optimización:** Uso de imágenes slim y multi-stage builds para reducir el tamaño final de los contenedores.
- **Límites de Recursos:** Configuración de límites de CPU y memoria por servicio.

---

## Gestión de Variables de Entorno

- **Centralización:** Uso de `.env` y `python-dotenv` para cargar variables en desarrollo y producción.
- **Base de Datos:** Configuración mediante variables para host, puerto, usuario, password y nombre de la base de datos. Soporte para `DATABASE_URL`.
- **Tokens y Credenciales:** Todas las credenciales sensibles se gestionan por variables de entorno, nunca en el código fuente.
- **Frontend:** El build de React y la configuración de Nginx permiten inyectar la URL de la API y otros parámetros en tiempo de ejecución.

---

## Despliegue en Coolify

- **Contenedores:** Coolify despliega usando los Dockerfiles ya definidos para backend y frontend.
- **Variables de Entorno:** Todas las credenciales y configuraciones se gestionan desde el panel de Coolify.
- **Migración desde Railway:** El stack soporta ambos proveedores, permitiendo una transición fluida.
- **Base de Datos:** Compatible con PostgreSQL tanto en Railway, Neon como en Coolify.

---

## Características Avanzadas

- **Webhooks:** Sistema robusto para recibir eventos en tiempo real desde Loyverse.
- **Celery:** Procesamiento de tareas en segundo plano para sincronización, cálculos y otras operaciones pesadas.
- **Gestión de Tasas de Cambio:** Soporte para múltiples tasas (BCV, paralelo) y conversión automática de monedas.
- **Optimización de Nginx:** Compresión gzip y configuración personalizada para servir el frontend con eficiencia.

---

## Recomendaciones

- Mantener dependencias actualizadas.
- Documentar procesos de despliegue y migración.
- Implementar monitoreo y alertas en producción.
- Añadir pruebas automatizadas para garantizar calidad y estabilidad.

---

**Última actualización:** 2025-05-10

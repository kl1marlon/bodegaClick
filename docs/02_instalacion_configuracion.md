# Guía de Instalación y Configuración

Esta guía proporciona instrucciones detalladas para instalar, configurar y desplegar BodegaClick en diferentes entornos.

## 1. Requisitos Previos

### 1.1 Software Necesario

- **Docker y Docker Compose** (para desarrollo local)
  - Docker Engine 20.10.x o superior
  - Docker Compose 2.x o superior

- **Git** (para gestión de código)
  - Git 2.30.x o superior

- **Cuenta de Loyverse**
  - Acceso a la API de Loyverse
  - Token de API con permisos adecuados

- **Para despliegue en Railway**
  - Cuenta en Railway
  - CLI de Railway (`npm i -g @railway/cli`)

- **Para despliegue en AWS**
  - Cuenta AWS con permisos adecuados
  - AWS CLI configurado

### 1.2 Conocimientos Recomendados

- Fundamentos de Django y Python
- Conceptos básicos de Docker
- Conocimiento básico de React (para desarrollo frontend)
- Familiaridad con PostgreSQL

## 2. Instalación Local con Docker

### 2.1 Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd bodegaClick
```

### 2.2 Configuración del Entorno

1. **Crear archivo `.env` en la raíz del proyecto**:

```env
# Configuración de PostgreSQL
POSTGRES_DB=bodegaclick
POSTGRES_USER=usuario
POSTGRES_PASSWORD=contraseña
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Configuración de Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# API de Loyverse
LOYVERSE_API_TOKEN=tu_token_de_loyverse

# Configuración de Redis (opcional)
REDIS_URL=redis://redis:6379/0
```

2. **Verificar estructura de directorios**:

Asegúrate de que la estructura básica del proyecto esté completa:

```
bodegaClick/
├── backend/
│   ├── config/
│   ├── facturacion/
│   ├── scripts/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env
```

### 2.3 Iniciar Servicios con Docker Compose

1. **Construir e iniciar los contenedores**:

```bash
docker-compose up -d
```

2. **Verificar que los servicios estén funcionando**:

```bash
docker-compose ps
```

Deberías ver tres servicios en ejecución: `db`, `backend` y `frontend`.

### 2.4 Inicialización de la Base de Datos

Las migraciones se ejecutan automáticamente al iniciar el contenedor `backend`. Para verificar:

```bash
docker-compose exec backend python manage.py showmigrations
```

Si necesitas ejecutar migraciones manualmente:

```bash
docker-compose exec backend python manage.py migrate
```

### 2.5 Crear Superusuario (Opcional)

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 2.6 Sincronización Inicial con Loyverse

```bash
docker-compose exec backend python sync_products.py
```

## 3. Configuración de Entornos

### 3.1 Entorno de Desarrollo

- **Backend**: Accesible en `http://localhost:8000`
- **Frontend**: Accesible en `http://localhost:3000`
- **Admin de Django**: `http://localhost:8000/admin`
- **API**: `http://localhost:8000/api`

#### Comandos Útiles para Desarrollo

- **Ver logs de los servicios**:
  ```bash
  docker-compose logs -f backend
  ```

- **Ejecutar scripts de actualización de precios**:
  ```bash
  docker-compose exec backend python scripts/actualizar_precios_base.py
  ```

- **Sincronizar precios con Loyverse**:
  ```bash
  docker-compose exec backend python scripts/sync_all_loyverse_prices.py
  ```

### 3.2 Entorno de Pruebas

Para configurar un entorno de pruebas separado:

1. **Crear archivo `.env.test`** con configuración específica para pruebas
2. **Iniciar servicios con configuración de pruebas**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d
   ```

## 4. Despliegue en Railway

### 4.1 Preparación para Railway

1. **Instalar y configurar CLI de Railway**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Inicializar proyecto en Railway**:
   ```bash
   railway init
   ```

### 4.2 Configuración de Variables de Entorno en Railway

En el dashboard de Railway:

1. Ir a **Variables**
2. Configurar las siguientes variables:
   ```
   POSTGRES_DB=bodegaclick
   POSTGRES_USER=usuario
   POSTGRES_PASSWORD=<password-seguro>
   LOYVERSE_API_TOKEN=<tu-token>
   DEBUG=False
   SECRET_KEY=<secret-key-seguro>
   ALLOWED_HOSTS=.railway.app
   DATABASE_URL=<proporcionado-por-railway>
   ```

### 4.3 Despliegue de Servicios

1. **Backend**:
   ```bash
   cd backend
   railway up
   ```

2. **Frontend**:
   ```bash
   cd frontend
   railway up
   ```

### 4.4 Configuración de Base de Datos en Railway

1. Agregar PostgreSQL desde el marketplace de Railway
2. Railway proporcionará automáticamente `DATABASE_URL`
3. Ejecutar migraciones:
   ```bash
   railway run python manage.py migrate
   ```

### 4.5 Configuración de Tareas Programadas

```bash
railway cron add "0 */6 * * *" "python sync_products.py"
```

## 5. Despliegue en AWS

### 5.1 Requisitos AWS

- Cuenta AWS
- Permisos para crear recursos EC2, RDS, S3, etc.
- AWS CLI configurado

### 5.2 Configuración de Infraestructura

1. **Base de datos RDS**:
   - Crear instancia PostgreSQL
   - Configurar grupo de seguridad para permitir conexiones desde EC2

2. **Instancia EC2**:
   - Crear instancia con Amazon Linux 2
   - Configurar grupo de seguridad para permitir tráfico HTTP/HTTPS
   - Asignar IP elástica (opcional)

3. **S3 para archivos estáticos** (opcional):
   - Crear bucket S3
   - Configurar permisos para acceso público a archivos estáticos

### 5.3 Despliegue en EC2

1. **Conectar a la instancia EC2**:
   ```bash
   ssh -i your-key.pem ec2-user@your-instance-ip
   ```

2. **Instalar dependencias**:
   ```bash
   sudo yum update -y
   sudo amazon-linux-extras install docker -y
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Clonar repositorio y configurar**:
   ```bash
   git clone <url-repositorio>
   cd bodegaClick
   ```

4. **Crear archivo `.env` con configuración de producción**

5. **Iniciar servicios**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 6. Configuración de Webhooks de Loyverse

### 6.1 Crear Webhook

```bash
python create_webhook.py --type inventory_levels.update --url https://tu-dominio.com/api/webhooks/inventory
```

### 6.2 Tipos de Webhooks Disponibles

- `inventory_levels.update`: Actualización de niveles de inventario
- `items.update`: Actualización de productos
- `customers.update`: Actualización de clientes
- `receipts.update`: Actualización de recibos
- `shifts.create`: Creación de turnos

## 7. Troubleshooting

### 7.1 Problemas Comunes y Soluciones

#### Problemas de Conexión a la Base de Datos

**Síntoma**: Error "could not connect to server: Connection refused"

**Solución**:
1. Verificar que el servicio de PostgreSQL esté en ejecución:
   ```bash
   docker-compose ps db
   ```
2. Comprobar las variables de entorno de conexión a la base de datos
3. Verificar que el host y puerto sean correctos

#### Errores de Sincronización con Loyverse

**Síntoma**: Error "401 Unauthorized" al sincronizar con Loyverse

**Solución**:
1. Verificar que el token de API sea válido
2. Regenerar el token en el panel de administración de Loyverse
3. Actualizar la variable de entorno `LOYVERSE_API_TOKEN`

#### Problemas con Docker

**Síntoma**: Error "port is already allocated"

**Solución**:
1. Verificar qué proceso está usando el puerto:
   ```bash
   sudo lsof -i :8000
   ```
2. Detener el proceso o cambiar el puerto en `docker-compose.yml`

### 7.2 Logs y Diagnóstico

- **Logs de Django**:
  ```bash
  docker-compose logs -f backend
  ```

- **Logs de React**:
  ```bash
  docker-compose logs -f frontend
  ```

- **Logs de PostgreSQL**:
  ```bash
  docker-compose logs -f db
  ```

## 8. Mantenimiento

### 8.1 Backups de Base de Datos

1. **Crear backup**:
   ```bash
   docker-compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Restaurar backup**:
   ```bash
   cat backup_file.sql | docker-compose exec -T db psql -U $POSTGRES_USER -d $POSTGRES_DB
   ```

### 8.2 Actualización del Sistema

1. **Obtener cambios del repositorio**:
   ```bash
   git pull origin main
   ```

2. **Reconstruir contenedores**:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

3. **Aplicar migraciones**:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

---

*Última actualización: 26 de junio de 2025*

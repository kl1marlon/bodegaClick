# Bodega Click

Sistema de gestión de inventario y ventas integrado con Loyverse.

## Desarrollo Local

### Requisitos Previos
- Docker y Docker Compose
- Token de API de Loyverse
- Git

### Configuración Local
1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd bodegaClick
```

2. Crear archivo `.env` en la raíz:
```env
POSTGRES_DB=bodegaclick
POSTGRES_USER=usuario
POSTGRES_PASSWORD=contraseña
LOYVERSE_API_TOKEN=tu_token_de_loyverse
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

3. Iniciar servicios:
```bash
docker-compose up -d
```

4. Sincronizar productos:
```bash
docker-compose run sync
```

## Despliegue en Railway

Railway es una plataforma PaaS que facilita el despliegue de aplicaciones containerizadas.

### Preparación para Railway

1. **Configurar CLI de Railway**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Preparar el proyecto**
   ```bash
   railway init
   ```

3. **Configurar Variables de Entorno en Railway**
   - Ir a Dashboard → Variables
   - Configurar las siguientes variables:
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

4. **Configurar Servicios**
   - Backend:
     ```bash
     cd backend
     railway up
     ```
   - Frontend:
     ```bash
     cd frontend
     railway up
     ```

### Configuración de Base de Datos en Railway
1. Agregar PostgreSQL desde el marketplace de Railway
2. Railway proporcionará automáticamente DATABASE_URL
3. Ejecutar migraciones:
   ```bash
   railway run python manage.py migrate
   ```

### Sincronización en Railway
1. Configurar tarea programada:
   ```bash
   railway cron add "0 */6 * * *" "python sync_products.py"
   ```

## Despliegue en AWS

### Requisitos AWS
- Cuenta AWS
- AWS CLI instalado y configurado
- Elastic Beanstalk CLI
- Docker

### 1. Configuración Inicial AWS

1. **Crear repositorio ECR**
   ```bash
   aws ecr create-repository --repository-name bodegaclick
   ```

2. **Configurar RDS (PostgreSQL)**
   - Crear instancia RDS desde la consola AWS
   - Configurar grupo de seguridad
   - Guardar credenciales

3. **Configurar S3 (Archivos estáticos)**
   ```bash
   aws s3 mb s3://bodegaclick-static
   aws s3api put-bucket-policy --bucket bodegaclick-static --policy file://s3-policy.json
   ```

### 2. Preparación de la Aplicación

1. **Crear archivo Dockerrun.aws.json**
```json
{
  "AWSEBDockerrunVersion": "3",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<aws-account-id>.dkr.ecr.<region>.amazonaws.com/bodegaclick:backend",
      "essential": true,
      "memory": 512,
      "portMappings": [
        {
          "hostPort": 8000,
          "containerPort": 8000
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_HOSTNAME}:${RDS_PORT}/${RDS_DB_NAME}"
        }
      ]
    },
    {
      "name": "frontend",
      "image": "<aws-account-id>.dkr.ecr.<region>.amazonaws.com/bodegaclick:frontend",
      "essential": true,
      "memory": 256,
      "portMappings": [
        {
          "hostPort": 3000,
          "containerPort": 3000
        }
      ]
    }
  ]
}
```

2. **Configurar Variables de Entorno en .ebextensions**
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    POSTGRES_DB: bodegaclick
    POSTGRES_USER: ${RDS_USERNAME}
    POSTGRES_PASSWORD: ${RDS_PASSWORD}
    LOYVERSE_API_TOKEN: <tu-token>
    DEBUG: False
    ALLOWED_HOSTS: .elasticbeanstalk.com
    AWS_STORAGE_BUCKET_NAME: bodegaclick-static
```

### 3. Despliegue en AWS

1. **Construir y Subir Imágenes**
   ```bash
   # Login en ECR
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com

   # Construir y subir backend
   docker build -t bodegaclick:backend ./backend
   docker tag bodegaclick:backend <aws-account-id>.dkr.ecr.<region>.amazonaws.com/bodegaclick:backend
   docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/bodegaclick:backend

   # Construir y subir frontend
   docker build -t bodegaclick:frontend ./frontend
   docker tag bodegaclick:frontend <aws-account-id>.dkr.ecr.<region>.amazonaws.com/bodegaclick:frontend
   docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/bodegaclick:frontend
   ```

2. **Crear Aplicación en Elastic Beanstalk**
   ```bash
   eb init -p docker bodegaclick
   eb create bodegaclick-env
   ```

3. **Configurar Base de Datos**
   ```bash
   eb ssh
   cd /var/app/current
   source /var/app/venv/*/bin/activate
   python manage.py migrate
   ```

### 4. Configuración de Sincronización AWS

1. **Crear Lambda Function**
   - Crear función Lambda usando la imagen de Docker
   - Configurar variables de entorno
   - Agregar trigger CloudWatch Events para ejecución programada

2. **IAM Role para Lambda**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "rds:*",
           "logs:*"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

### 5. Monitoreo y Mantenimiento

1. **CloudWatch Logs**
   - Configurar grupos de logs
   - Establecer alertas

2. **Backup y Recuperación**
   - Configurar snapshots RDS
   - Backup S3

### Comandos Útiles

**Railway:**
```bash
# Ver logs
railway logs

# Ejecutar comando
railway run <comando>

# Actualizar despliegue
railway up
```

**AWS:**
```bash
# Ver logs
eb logs

# SSH a instancia
eb ssh

# Actualizar aplicación
eb deploy

# Escalar
eb scale <número-instancias>
```

## Solución de Problemas

### Railway
1. **Error de conexión a DB**
   - Verificar DATABASE_URL
   - Comprobar firewall

2. **Error en sincronización**
   - Verificar LOYVERSE_API_TOKEN
   - Revisar logs: `railway logs`

### AWS
1. **Error de despliegue**
   - Verificar Dockerrun.aws.json
   - Revisar logs: `eb logs`

2. **Error de conexión RDS**
   - Verificar grupo de seguridad
   - Comprobar credenciales

## Mantenimiento

### Actualizaciones
1. Probar en entorno local
2. Commit y push a Git
3. Desplegar según plataforma:
   - Railway: `railway up`
   - AWS: `eb deploy`

### Backups
- Railway: Usar railway backup
- AWS: Configurar snapshots RDS

## Webhooks de Loyverse

El sistema permite configurar webhooks para mantener sincronizada la información con Loyverse. Los webhooks son notificaciones en tiempo real que envía Loyverse cuando ocurren cambios en sus datos, como actualizaciones de inventario, nuevas órdenes, etc.

### Configuración de Webhook para Inventario

Para mantener actualizado el inventario en tiempo real, se ha implementado un webhook para el evento `inventory_levels.update`. Este webhook recibe notificaciones cada vez que cambia el nivel de inventario en Loyverse.

#### Requisitos previos

1. Un servidor con acceso público (URL con HTTPS)
2. Credenciales de API de Loyverse configuradas en el archivo `.env`

#### Crear un Webhook de Inventario

Hay dos formas de configurar el webhook:

1. **Usando el script de creación automatizada**:

```bash
python backend/create_webhook.py --url https://midominio.com/webhook/
```

2. **Usando la API REST**:

```bash
curl -X POST http://localhost:8000/api/webhooks/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://midominio.com/webhook/", "type": "inventory_levels.update"}'
```

3. **Usando la interfaz web de Loyverse**:
   - Accede a https://r.loyverse.com/dashboard/#/webhooks
   - Configura la URL del webhook: `https://midominio.com/webhook/`
   - Selecciona el tipo: `inventory_levels.update`

### Verificación de Seguridad

Los webhooks incluyen una firma para verificar que la solicitud proviene de Loyverse. Esta firma se valida automáticamente en cada solicitud recibida. Para ello, debes configurar la variable `LOYVERSE_WEBHOOK_SECRET` en tu archivo `.env` con el secreto proporcionado por Loyverse.

### Prueba de Webhooks

Para probar un webhook configurado, puedes usar el endpoint de prueba:

```bash
curl -X POST http://localhost:8000/api/webhooks/[ID]/test/
```

Este endpoint enviará datos de prueba a la URL configurada y verificará que todo funcione correctamente.

### Estructura de Datos Recibidos

Cuando se actualiza el inventario, Loyverse envía un payload JSON con la siguiente estructura:

```json
{
  "merchant_id": "5fk4f446-01d2-8787-4fd5-7b7b1995df85",
  "type": "inventory_levels.update",
  "created_at": "2020-06-07T17:23:48.562Z",
  "inventory_levels": [
    {
      "variant_id": "5fk4f446-01d2-8787-4fd5-7b7b1995df85",
      "store_id": "5fk4f446-01d2-8787-4fd5-7b7b1995df85",
      "in_stock": 0,
      "updated_at": "2019-08-24T14:15:22Z"
    }
  ]
}
```

El sistema procesa automáticamente estas actualizaciones y mantiene la base de datos local sincronizada con Loyverse.

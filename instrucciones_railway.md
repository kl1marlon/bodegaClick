# Instrucciones de Despliegue en Railway

## Paso 1: Desplegar la aplicación sin migraciones

1. **Sube estos cambios a tu repositorio de Git**
   - Los archivos ya están modificados para omitir las migraciones iniciales

2. **Crea un nuevo proyecto en Railway**
   - Inicia sesión en [Railway](https://railway.app/)
   - Crea un nuevo proyecto > Deploy from GitHub repo
   - Selecciona tu repositorio de BodegaClick

3. **Añade un servicio de PostgreSQL**
   - En la página de tu proyecto, haz clic en "New"
   - Selecciona "Database" > "PostgreSQL"

4. **Configura las variables de entorno**
   - Ve a la pestaña "Variables" de tu servicio web
   - Asegúrate de añadir todas las variables de entorno necesarias:
     ```
     DEBUG=False
     SECRET_KEY=una_clave_secreta_fuerte_y_aleatoria
     ALLOWED_HOSTS=.railway.app,api.railway.app
     LOYVERSE_API_TOKEN=46791ab21b0f4ad6b69f59b1a61acdf6
     LOYVERSE_MERCHANT_ID='tu_id_de_comerciante'
     LOYVERSE_WEBHOOK_SECRET='tu_secreto_de_webhook'
     ```
   - Railway configurará automáticamente la conexión a PostgreSQL, no necesitas configurarla manualmente

## Paso 2: Aplicar migraciones manualmente

Cuando tu aplicación esté desplegada:

1. **Instala la CLI de Railway**
   ```bash
   npm i -g @railway/cli
   ```

2. **Autentícate en Railway**
   ```bash
   railway login
   ```

3. **Conecta a tu proyecto**
   ```bash
   railway link
   ```

4. **Ejecuta las migraciones**
   ```bash
   railway run python manage.py migrate --fake-initial
   ```

5. **Si encuentras errores**:
   ```bash
   railway run python manage.py migrate --fake
   ```

## Paso 3: Importar datos esenciales

1. **Sube el archivo de datos a tu proyecto**
   ```bash
   railway run "cat solo_datos_sin_celery.sql | psql $DATABASE_URL"
   ```

## Paso 4: Restaurar configuración para futuros despliegues

1. **Restaura el railway.json a su estado original**
   - Reemplaza el contenido con el respaldo `railway.json.bak`

2. **Restaura el Dockerfile a su estado original**
   - Reemplaza el contenido con el respaldo `Dockerfile.bak`

3. **Sube los cambios a tu repositorio**
   ```bash
   git add .
   git commit -m "Restaurar configuración para migraciones automáticas"
   git push
   ```

4. **Realiza un despliegue manual**
   - En Railway, haz clic en tu servicio web
   - Haz clic en "Deploy" para aplicar los cambios

## Solución de problemas

Si encuentras errores durante el despliegue, consulta los logs en Railway:

1. **Ver logs**
   - En Railway, selecciona tu servicio web
   - Haz clic en "Deployments"
   - Selecciona el despliegue más reciente
   - Revisa los logs para identificar errores específicos

2. **Problemas comunes**:
   - **Error de conexión a DB**: Verifica que las variables de entorno estén configuradas correctamente
   - **Error de migración**: Usa `--fake` o `--fake-initial`
   - **Error de importación**: Verifica que el formato del archivo SQL sea compatible

3. **Ayuda adicional**:
   - Consulta la documentación oficial de Railway: [docs.railway.app](https://docs.railway.app/) 
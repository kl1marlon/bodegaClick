# 🚨 BodegaClick - Versión de Recuperación Mínima

## 📋 Situación Actual

El servidor se congeló después del último despliegue. Esta es una **versión ultra minimalista** diseñada específicamente para recuperar el servidor en Coolify.

## 🎯 Objetivo

Restaurar el servidor con la configuración más básica posible para luego ir agregando funcionalidades gradualmente.

## 🔧 Cambios Realizados

### Backend Mínimo
- ✅ Django 4.2 + Django REST Framework básico
- ✅ Eliminado: Celery, Redis, django-celery-results
- ✅ Base de datos: SQLite por defecto (PostgreSQL si hay DATABASE_URL)
- ✅ Middleware reducido al mínimo
- ✅ Apps: Solo las esenciales de Django + DRF + CORS
- ✅ Health check endpoint: `/health/` y `/api/health/`

### Frontend Mínimo
- ✅ React básico (sin Redux, Material-UI, ni dependencias complejas)
- ✅ Una sola página con estado del sistema
- ✅ Verificación automática del backend cada 30 segundos
- ✅ Interfaz de "Sistema en Mantenimiento"

### Docker Optimizado
- ✅ Dockerfile backend simplificado
- ✅ Dockerfile frontend con nginx básico
- ✅ Docker-compose mínimo con health checks

## 🚀 Despliegue en Coolify

1. **Hacer commit de los cambios:**
   ```bash
   git add .
   git commit -m "Versión mínima de recuperación - Sin Celery/Redis"
   git push origin main
   ```

2. **Coolify detectará automáticamente los cambios**
   - El despliegue debería ser mucho más rápido
   - Sin dependencias problemáticas
   - Configuración mínima y estable

3. **Verificar que funciona:**
   - Frontend: Página de mantenimiento
   - Backend: `/health/` devuelve status OK
   - Admin: `/admin/` accesible

## 📁 Archivos de Respaldo

Los archivos originales están respaldados en `./backup_original/`:
- `settings_original.py`
- `urls_original.py`
- `requirements_original.txt`
- `package_original.json`

## 🔄 Plan de Restauración Gradual

Una vez que el servidor esté funcionando:

1. **Fase 1:** Verificar que todo funciona básicamente
2. **Fase 2:** Agregar la app `facturacion` de vuelta
3. **Fase 3:** Restaurar modelos básicos (Producto, TasaCambio)
4. **Fase 4:** Agregar Redis y Celery gradualmente
5. **Fase 5:** Restaurar funcionalidades completas

## 🆘 Si Algo Sale Mal

```bash
# Restaurar archivos originales
cp backup_original/settings_original.py backend/config/settings.py
cp backup_original/urls_original.py backend/config/urls.py
cp backup_original/requirements_original.txt backend/requirements.txt
cp backup_original/package_original.json frontend/package.json
```

## 🎯 Endpoints Disponibles

- `/` - Página principal de mantenimiento
- `/health/` - Health check del sistema
- `/api/health/` - Health check de la API
- `/admin/` - Panel de administración Django

## 💡 Notas Importantes

- Esta versión usa SQLite por defecto para evitar problemas de conexión
- Si hay `DATABASE_URL` en las variables de entorno, usará PostgreSQL
- Sin autenticación compleja - Todo en modo permisivo para recuperación
- Logs mínimos para evitar spam en Coolify

---

**🎉 Una vez que el servidor esté funcionando, podremos ir restaurando las funcionalidades paso a paso.**

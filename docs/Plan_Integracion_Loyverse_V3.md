# Plan de Integración Loyverse V3: Estado Actual y Próximos Pasos

## 1. Resumen Ejecutivo

Este documento constituye la versión V3 del plan de integración entre BodegaClick y Loyverse, actualizando las versiones anteriores con el estado actual del desarrollo y las decisiones estratégicas para completar la implementación. El objetivo principal sigue siendo proporcionar una integración fluida entre BodegaClick y Loyverse, permitiendo a los usuarios gestionar sus productos y precios en BodegaClick y sincronizarlos con Loyverse.

### Decisiones Estratégicas Clave:
1. **Conexión Loyverse Obligatoria**: La conexión OAuth2 con Loyverse será un requisito obligatorio para todos los usuarios.
2. **Sincronización Bidireccional Mejorada**: Permitiremos sincronización bajo demanda en ambas direcciones, preservando datos críticos como `precio_base_usd`.
3. **Multi-Tenancy Completo**: Todos los datos estarán segmentados por usuario, permitiendo que múltiples negocios usen la plataforma de forma aislada.
4. **Experiencia de Usuario Integral**: Implementación completa tanto en frontend como backend para ofrecer una experiencia fluida y transparente.
5. **Estrategia de Seguridad Robusta**: Asegurar el manejo adecuado de tokens, permisos y aislamiento de datos.

---

## 2. Contexto Técnico

### 2.1 Estructura del Proyecto
- **Framework Backend**: Django 4.2.0 con Django REST Framework 3.14.0
- **Base de Datos**: PostgreSQL 13
- **Procesamiento Asíncrono**: Celery 5.4.0 con Redis 5.2.1 como broker/backend
- **Servidor Web**: Gunicorn 21.2.0
- **Framework Frontend**: React (frontend ubicado en directorio `/frontend`)
- **Contenerización**: Docker y Docker Compose para desarrollo local

### 2.2 Estado de Multi-Tenancy
- **Modelo `Producto`**: ✅ Incluye campo `user` como `ForeignKey` con `related_name='productos'`
- **Modelo `TasaCambio`**: ✅ Incluye campo `user` como `ForeignKey` con `related_name='tasas_cambio'`
- **Modelo `Factura`**: ✅ Incluye campo `user` como `ForeignKey` con `related_name='facturas'`
- **Modelo `Webhook`**: ⚠️ No incluye campo `user`, aunque esto no es crítico para la integración con Loyverse
- **Modelo `LoyverseUserConnection`**: ✅ Implementa correctamente `OneToOneField` a `User`

### 2.3 Credenciales de Loyverse
- **Método de Gestión**: Variables de entorno `LOYVERSE_APP_CLIENT_ID` y `LOYVERSE_APP_CLIENT_SECRET`
- **Alcance (Scopes)**: Configurados para `OPENID`, `ITEMS_READ`, `ITEMS_WRITE`
- **Entorno**: Preparado para trabajar tanto en sandbox como en producción
- **Redirect URI**: URLs correctamente configuradas y validadas en la aplicación Loyverse

### 2.4 Scripts y Tareas Existentes
- **Sincronización Loyverse → BodegaClick**: Script `backend/scripts/sync_loyverse_products.py` (requiere adaptación para OAuth2 y multi-tenancy)
- **Sincronización BodegaClick → Loyverse**: Tarea Celery `sync_user_prices_to_loyverse` ya implementada
- **Recálculo de Precios**: Tarea Celery `recalculate_user_base_prices_task` ya implementada

### 2.5 Configuración de Celery
- ✅ Celery ya está configurado e integrado en el proyecto
- ✅ Broker/Backend con Redis correctamente configurado
- ✅ Tareas asíncronas funcionando para sincronización de precios

### 2.6 Estado del Frontend
- **Framework**: React
- **Estructura**: Sistema de componentes modular
- **Estado Actual**: Interfaz básica existente para gestión de productos y facturas
- **Pendiente**: Componentes específicos para la integración y sincronización con Loyverse

### 2.7 Infraestructura de Despliegue
- **Entorno Actual**: Render (previamente Coolify/Railway)
- **Variables de Entorno**: Gestionadas en la plataforma de despliegue
- **Estrategia de Despliegue**: CI/CD mediante GitHub Actions (pendiente de confirmar detalles)

### 2.8 Documentación de API
- ✅ Acceso completo a la documentación de API de Loyverse
- ✅ Endpoints principales ya identificados y probados
- ✅ Límites de tasa y restricciones de API documentados

---

## 3. Estado Actual del Desarrollo

### 3.1 Componentes Completados

#### 3.1.1 Infraestructura Base
- ✅ Creación de la app `loyverse_integration`
- ✅ Configuración de `django-cryptography` para cifrado de tokens
- ✅ Definición del modelo `LoyverseUserConnection` con cifrado de tokens sensibles

#### 3.1.2 Autenticación OAuth2
- ✅ Implementación completa del flujo OAuth2 con Loyverse
- ✅ Vistas para iniciar conexión y manejar callbacks
- ✅ Gestión adecuada de tokens, incluyendo refresco automático
- ✅ Validación segura de JWT (id_token)

#### 3.1.3 Sincronización de Precios
- ✅ Tareas Celery para sincronización de precios hacia Loyverse
- ✅ Tarea para recálculo de precios base a partir de precio USD y tasas
- ✅ Interfaz de usuario para controlar la sincronización

#### 3.1.4 Interfaz de Usuario
- ✅ Panel de control para gestionar la conexión con Loyverse
- ✅ Formulario para iniciar sincronización con opciones configurables
- ✅ Visualización del estado de sincronización y errores

### 3.2 Componentes Parcialmente Implementados

#### 3.2.1 Multi-Tenancy
- ✅ Los modelos de `facturacion` han sido verificados y todos incluyen campo `user`
- ✅ Se ha implementado middleware para garantizar la segmentación de datos por usuario

#### 3.2.2 Sincronización desde Loyverse a BodegaClick
- ✅ Script mejorado `sync_loyverse_products_oauth.py` implementado con soporte para OAuth2
- ✅ Preservación de `precio_base_usd` para productos existentes implementada

#### 3.2.3 Flujo de Registro y Autenticación
- ✅ Implementación de verificación de conexión Loyverse en login
- ✅ Redirección automática al flujo OAuth2 cuando es necesario

---

## 3. Plan Detallado para Completar la Implementación

### 3.1 Verificación y Refuerzo del Multi-Tenancy

#### 3.1.1 Revisión de Modelos
- Confirmar que todos los modelos relevantes (`Producto`, `Factura`, `TasaCambio`, etc.) tienen campo `user`
- Verificar que las consultas filtran adecuadamente por usuario en todas las vistas
- Validar la relación OneToOne entre `User` y `LoyverseUserConnection`

#### 3.1.2 Seguridad de Datos
- Implementar middleware o decoradores de vista para garantizar aislamiento de datos
- Verificar que un usuario solo puede acceder a sus propios productos/datos
- Asegurar que la identificación de productos de Loyverse es única por usuario

### 3.2 Sincronización Bidireccional Mejorada

#### 3.2.1 Sincronización Loyverse → BodegaClick
- Mejorar el script existente para:
  - Funcionar con tokens OAuth2 del usuario actual
  - Preservar valores `precio_base_usd` para productos existentes
  - Calcular `precio_base_usd` para productos nuevos basado en tasa configurable
  - Manejar productos eliminados en Loyverse

#### 3.2.2 Sincronización BodegaClick → Loyverse
- Mejorar la tarea existente para:
  - Optimizar manejo de límites de tasa API
  - Mejorar registro de errores y reintentos
  - Proporcionar feedback detallado al usuario

#### 3.2.3 Opciones de Sincronización
- Implementar opciones configurables:
  - Sincronización forzada (sobrescribir aunque precio local sea menor)
  - Recálculo de precios antes de sincronizar
  - Sincronización selectiva por categorías o productos

### 3.3 Flujo de Registro y Autenticación

#### 3.3.1 Modificación del Proceso de Registro
- Actualizar el flujo de registro para:
  - Requerir conexión Loyverse como paso obligatorio
  - Manejar rechazos de OAuth2 adecuadamente
  - Establecer estado "pendiente" para cuentas sin conexión completa

#### 3.3.2 Verificación en Login
- Implementar verificación en cada login:
  - Confirmar existencia y validez de conexión Loyverse
  - Redirigir a OAuth2 si es necesario
  - Manejar casos donde el token no puede refrescarse

#### 3.3.3 Migración de Usuarios Existentes
- Implementar estrategia para usuarios actuales:
  - Verificar conexión en próximo login
  - Forzar flujo OAuth2 si no existe
  - Preservar datos existentes durante conexión nueva

### 3.4 Implementación de Webhooks (Opcional/Futura)

#### 3.4.1 Registro de Webhooks en Loyverse
- Implementar registro automático de webhooks a través de API Loyverse
- Configurar endpoints seguros para recibir notificaciones

#### 3.4.2 Manejo de Eventos
- Implementar controladores para eventos clave:
  - Creación de productos
  - Actualización de precios
  - Eliminación de productos

---

## 4. Casos de Uso Principal

### 4.1 Flujo de Usuario Nuevo
1. Usuario se registra en BodegaClick
2. Es redirigido inmediatamente al flujo OAuth2 con Loyverse
3. Al autorizar, se crea su `LoyverseUserConnection`
4. Se ofrece importación inicial de productos desde Loyverse
5. El usuario puede comenzar a gestionar precios en BodegaClick
6. Los cambios se sincronizan a Loyverse bajo demanda

### 4.2 Flujo de Sincronización Bidireccional
1. **Loyverse → BodegaClick**:
   - Usuario crea productos nuevos en Loyverse
   - Inicia sincronización manual desde panel de BodegaClick
   - Productos nuevos se importan con cálculo automático de `precio_base_usd`
   - Productos existentes mantienen su `precio_base_usd` actual

2. **BodegaClick → Loyverse**:
   - Usuario actualiza precios en USD en BodegaClick
   - Sistema recalcula precios base según tasas configuradas
   - Usuario inicia sincronización hacia Loyverse
   - Precios se actualizan respetando límites de API

### 4.3 Manejo de Casos Especiales
1. **Usuario sin conexión Loyverse**:
   - Redirección a flujo OAuth2
   - Opción de contactar soporte si hay problemas persistentes

2. **Error de sincronización**:
   - Registro detallado del error
   - Presentación clara al usuario
   - Opciones de reintento o sincronización parcial

3. **Cambios en ambos sistemas**:
   - Prioridad a datos de BodegaClick (fuente autoritativa)
   - Opción para forzar importación en casos específicos

---

## 5. Implementación Actual y Próximos Pasos

### 5.1 Componentes Implementados (Mayo 2025)

#### 5.1.1 Verificación de Multi-Tenancy
- ✅ Revisados modelos para confirmar campo `user` en todos los modelos relevantes
- ✅ Implementado middleware `LoyverseConnectionMiddleware` para validar segmentación de datos
- ✅ Creado decorador `loyverse_connection_required` para proteger vistas específicas

#### 5.1.2 Mejora de Sincronización Bidireccional
- ✅ Creado script `sync_loyverse_products_oauth.py` con soporte para OAuth2
- ✅ Implementada lógica para preservar `precio_base_usd` en productos existentes
- ✅ Implementado cálculo de precios para productos nuevos basado en tasa configurable

#### 5.1.3 Flujo de Registro/Login
- ✅ Implementadas vistas personalizadas `CustomLoginView` y `CustomTokenObtainPairView`
- ✅ Implementada verificación de conexión Loyverse en login
- ✅ Implementada redirección automática al flujo OAuth2 cuando es necesario

#### 5.1.4 Frontend
- ✅ Actualizado componente Login para manejar redirección a Loyverse
- ✅ Implementado manejo de estados de carga y errores en el proceso de login

### 5.2 Próximos Pasos Inmediatos

#### 5.2.1 Pruebas End-to-End
- Probar flujo completo con usuarios de prueba
- Verificar correcta segmentación de datos
- Validar sincronización bidireccional con preservación de datos

#### 5.2.2 Mejoras en la Experiencia de Usuario
- Crear página de registro que incluya OAuth2 obligatorio
- Mejorar mensajes de error y feedback durante el proceso de conexión
- Implementar indicadores visuales del estado de la conexión

#### 5.2.3 Documentación
- Actualizar documentación para usuarios finales
- Crear guía de troubleshooting para problemas comunes
- Documentar proceso de desarrollo para futuros mantenimientos

---

## 6. Detalles de Implementación

Esta sección documenta los detalles técnicos de los componentes implementados como parte del plan de integración Loyverse V3.

### 6.1 Script de Sincronización OAuth2

#### 6.1.1 Archivo: `sync_loyverse_products_oauth.py`

**Ubicación**: `/backend/scripts/sync_loyverse_products_oauth.py`

**Funcionalidad**:
- Utiliza la conexión OAuth2 del usuario para autenticarse con Loyverse
- Preserva el valor `precio_base_usd` para productos existentes
- Calcula `precio_base_usd` para productos nuevos basado en tasa configurable
- Implementa multi-tenancy asociando productos al usuario correcto
- Maneja productos eliminados en Loyverse

**Uso**:
```bash
python backend/scripts/sync_loyverse_products_oauth.py <user_id> <tasa_cambio> [--force]
```

### 6.2 Middleware y Decoradores

#### 6.2.1 Middleware: `LoyverseConnectionMiddleware`

**Ubicación**: `/backend/loyverse_integration/middleware.py`

**Funcionalidad**:
- Verifica que los usuarios autenticados tengan una conexión activa con Loyverse
- Redirige automáticamente al flujo OAuth2 si no hay conexión o está inactiva
- Maneja tanto solicitudes normales como AJAX
- Excluye rutas específicas de la verificación (admin, auth, etc.)

#### 6.2.2 Decorador: `loyverse_connection_required`

**Ubicación**: `/backend/loyverse_integration/decorators.py`

**Funcionalidad**:
- Protege vistas específicas que requieren conexión Loyverse
- Complementa al middleware para un control más granular
- Redirige al flujo OAuth2 si es necesario

### 6.3 Vistas Personalizadas de Autenticación

#### 6.3.1 Vistas: `CustomLoginView`, `CustomTokenObtainPairView`

**Ubicación**: `/backend/loyverse_integration/auth_views.py`

**Funcionalidad**:
- Extienden las vistas estándar de autenticación de Django
- Verifican la conexión Loyverse después del login exitoso
- Redirigen al flujo OAuth2 si es necesario
- Manejan tokens JWT para autenticación API

### 6.4 API para Verificación de Conexión

#### 6.4.1 Endpoint: `check_loyverse_connection`

**Ubicación**: `/backend/loyverse_integration/api_views.py`

**Funcionalidad**:
- Verifica si el usuario tiene una conexión activa con Loyverse
- Devuelve información sobre el estado de la conexión
- Proporciona URL para iniciar el flujo OAuth2 si es necesario
- Utilizado por el frontend para manejar redirecciones

### 6.5 Modificaciones en el Frontend

#### 6.5.1 Componente: `Login.js`

**Ubicación**: `/frontend/src/pages/Login.js`

**Funcionalidad**:
- Maneja la redirección a Loyverse después del login exitoso
- Muestra estados de carga durante el proceso de autenticación
- Maneja errores y mensajes para el usuario
- Utiliza el endpoint `check-loyverse-connection` para verificar el estado

---

## 7. Componentes Frontend

### 7.1 Interfaz de Registro/Login
- **Flujo de Registro Integrado con OAuth2**:
  - Formulario de registro básico para datos de usuario
  - Redirección automática a OAuth2 de Loyverse tras registro
  - Manejo de cancelación y reintentos
  - Estado visual de proceso de conexión

- **Panel de Usuario**:
  - Información clara del estado de conexión Loyverse
  - Opción para reconectar o actualizar tokens manualmente
  - Visualización de detalles de cuenta Loyverse conectada

### 7.2 Panel de Control de Sincronización
- **Dashboard de Sincronización**:
  - Estado actual de sincronización
  - Historial detallado de sincronizaciones anteriores
  - Indicadores visuales de tiempo desde última sincronización

- **Controles de Sincronización**:
  - Botones para sincronización manual en ambas direcciones
  - Opciones configurables (preservar precios, forzar actualizaciones)
  - Indicadores de progreso para operaciones en curso

- **Manejo de Errores**:
  - Visualización amigable de errores durante sincronización
  - Opciones de reintento para elementos fallidos
  - Registro detallado de problemas y soluciones sugeridas

### 6.3 Gestión de Productos
- **Indicadores de Estado de Sincronización**:
  - Badges o etiquetas que muestren estado de sincronización de cada producto
  - Diferenciar productos locales vs importados desde Loyverse
  - Visualizar discrepancias de precio entre sistemas

- **Acciones Rápidas**:
  - Opciones para sincronizar productos individuales
  - Alertas visuales para productos no sincronizados
  - Historial de cambios específico por producto

---

## 7. Consideraciones de Seguridad y Permisos

### 7.1 Manejo de Tokens OAuth2
- **Almacenamiento Seguro**:
  - Tokens cifrados en base de datos mediante `django-cryptography`
  - Sin exposición de tokens al frontend
  - Rotación adecuada de tokens expirados

- **Validación Estricta**:
  - Verificación completa de JWT (firma, issuer, audience)
  - Validación de scopes y permisos en cada operación
  - Manejo de tokens revocados o inválidos

### 7.2 Multi-Tenancy y Seguridad de Datos
- **Filtrado por Usuario**:
  - Middleware para verificar acceso a datos de usuario actual
  - Queries filtradas automáticamente por `user_id`
  - Prevención de acceso cruzado entre cuentas

- **Logs de Seguridad**:
  - Registro de intentos de acceso a datos de otro usuario
  - Auditoría de operaciones sensibles
  - Alertas de patrones sospechosos

### 7.3 Protección de API
- **Rate Limiting**:
  - Limitación de tasa para endpoints críticos
  - Gestión de tokens con principio de mínimo privilegio
  - Respeto a límites de API de Loyverse

- **Manejo de Errores Seguro**:
  - Respuestas de error sanitizadas
  - Sin exposición de datos sensibles en logs o mensajes
  - Feedback útil sin comprometer seguridad

---

## 8. Experiencia de Usuario

### 8.1 Feedback y Notificaciones
- **Sistema de Notificaciones**:
  - Alertas para sincronizaciones exitosas/fallidas
  - Recordatorios de reconexión cuando tokens están por expirar
  - Notificaciones para cambios importantes en productos

- **Indicadores Visuales**:
  - Estados claros para cada operación
  - Barras de progreso para sincronizaciones largas
  - Codificación por colores para estados críticos

### 8.2 Ayuda Contextual
- **Guías Integradas**:
  - Tutoriales paso a paso para primeros usuarios
  - Tooltips explicativos en elementos complejos
  - Documentación accesible desde cada pantalla

- **Mensajes Informativos**:
  - Explicaciones claras sobre requisitos de OAuth2
  - Interpretación de errores técnicos en lenguaje simple
  - Sugerencias proactivas para optimizar uso

---

## 9. Pruebas y Monitoreo

### 9.1 Estrategia de Pruebas
- **Pruebas Unitarias**:
  - Cobertura completa de lógica de negocio
  - Mocking de API externa de Loyverse
  - Validación de manejo de tokens y autenticación

- **Pruebas de Integración**:
  - Flujos completos de OAuth y sincronización
  - Pruebas con cuentas reales de prueba en Loyverse
  - Validación de multi-tenancy con múltiples usuarios

- **Pruebas de Interfaz**:
  - Validación de experiencia de usuario
  - Pruebas de responsividad
  - Simulación de errores y casos límite

### 9.2 Monitoreo en Producción
- **Telemetría**:
  - Registro detallado de operaciones críticas
  - Métricas de rendimiento para sincronizaciones
  - Alertas para fallos recurrentes

- **Panel de Estado**:
  - Dashboard para administradores con visión global
  - Estadísticas de uso y éxito de sincronizaciones
  - Detección temprana de problemas con API Loyverse

---

## 10. Despliegue y Operaciones

### 10.1 Estrategia de Despliegue
- **Secuencia de Implementación**:
  1. Completar cambios en modelos y migrations
  2. Implementar tareas Celery de sincronización
  3. Desplegar cambios de backend
  4. Implementar cambios en frontend
  5. Activar nuevos flujos para usuarios existentes

- **Rollback Plan**:
  - Procedimientos para reversión en caso de problemas
  - Backups automáticos pre-despliegue
  - Scripts de recuperación para estados inconsistentes

### 10.2 Documentación Operativa
- **Guías de Resolución de Problemas**:
  - Procedimientos para problemas comunes
  - Árbol de decisión para diagnóstico
  - Contactos y procedimientos de escalación

- **Mantenimiento**:
  - Procedimientos para rotación de credenciales
  - Plan para cambios en API de Loyverse
  - Estrategia de actualización de dependencias

---

## 11. Consideraciones Técnicas Adicionales

### 11.1 Seguridad
- Todos los tokens OAuth2 se almacenan cifrados
- Estricta validación de JWT para autenticación
- Aislamiento de datos entre usuarios

### 11.2 Rendimiento
- Respeto a límites de tasa API de Loyverse (1 req/seg)
- Operaciones asíncronas mediante Celery para operaciones costosas
- Optimización de consultas para grandes volúmenes de productos
- Caché estratégico para reducir llamadas a API

### 11.3 Mantenibilidad
- Documentación clara de flujos y decisiones
- Separación de responsabilidades entre módulos
- Pruebas automatizadas para componentes críticos
- Convenciones de código consistentes

---

*Documento actualizado: 19 de mayo de 2025*

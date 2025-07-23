# Cómo Solicitar Ayuda a un Arquitecto de Software

## Introducción

Este documento tiene como objetivo guiar a los desarrolladores sobre la manera más efectiva de solicitar asistencia a un arquitecto de software. Una solicitud bien estructurada no solo facilita la comprensión del problema, sino que también acelera la implementación de una solución robusta y escalable.

Usaremos como caso de estudio el proceso de **actualización masiva de precios**, actualmente descrito en `docs/verificacion_precios_loyverse.md`, para ilustrar cómo transformar un proceso manual en una tarea asíncrona gestionada por workers.

---

## Caso de Estudio: Refactorización de la Actualización de Precios con Workers

### Problema Actual

El documento `verificacion_precios_loyverse.md` describe un flujo donde la actualización masiva de precios se ejecuta como una única petición HTTP. Si bien es funcional, este enfoque presenta varias desventajas:

1.  **Bloqueo de la Interfaz:** El usuario debe esperar en la pantalla sin poder realizar otras acciones hasta que el proceso termine.
2.  **Riesgo de Timeouts:** Si hay una gran cantidad de productos, la petición puede exceder el tiempo límite del servidor (timeout), resultando en una operación fallida o incompleta.
3.  **Falta de Escalabilidad:** A medida que el número de productos crezca, el problema de rendimiento se agravará.

### Solución Propuesta: Uso de Workers con Celery

La solución idónea es refactorizar este proceso para que se ejecute de forma asíncrona en segundo plano, utilizando la infraestructura de Celery que ya tenemos configurada en el proyecto.

**¿Cómo funcionaría?**

1.  **El Frontend Inicia la Tarea:** El usuario, desde la interfaz, hace clic en "Actualizar precios base".
2.  **El Backend Delega a un Worker:** En lugar de procesar la actualización directamente, el endpoint de la API crea una nueva tarea en Celery y le pasa los parámetros necesarios (ej. la nueva tasa de cambio). El endpoint responde inmediatamente al frontend con un ID de la tarea.
3.  **El Worker Hace el Trabajo Pesado:** Un worker de Celery toma la tarea de la cola y comienza a actualizar los precios en la base de datos, uno por uno o en lotes. Este proceso ocurre de forma independiente, sin bloquear al servidor web.
4.  **El Frontend Consulta el Estado:** La interfaz utiliza el ID de la tarea para consultar periódicamente el estado de la operación (ej. "Procesando 50 de 1000 productos...", "Completado", "Error").
5.  **Notificación al Usuario:** Una vez que el worker finaliza, el frontend notifica al usuario que la actualización ha sido completada.

---

## Cómo Estructurar tu Solicitud al Arquitecto

Para solicitar este cambio (o cualquier otro), estructura tu petición de la siguiente manera. Esto le dará al arquitecto todo el contexto que necesita.

### 1. Título Descriptivo

**Ejemplo:** "Refactorizar la actualización masiva de precios para usar workers asíncronos"

### 2. Descripción del Problema

Explica claramente la situación actual y por qué es un problema.

**Ejemplo:**
> "Actualmente, la actualización masiva de precios desde el listado de productos se ejecuta como una petición síncrona. Con más de 5,000 productos, la operación tarda más de 60 segundos y a menudo falla por timeouts del servidor. Esto bloquea la interfaz del usuario y ofrece una mala experiencia. Quiero convertir esto en un proceso asíncrono."

### 3. Referencias al Código Actual

Indica los archivos o partes del sistema que están involucrados.

**Ejemplo:**
> -   **Frontend:** La lógica se inicia en `frontend/src/pages/ListadoProductos.js`, en la función que llama al endpoint de la API.
> -   **Backend:** El endpoint involucrado es `/api/productos/actualizar-precios-base/` en `backend/facturacion/views.py`.
> -   **Lógica de Negocio:** La lógica de cálculo está en el comando `backend/scripts/actualizar_precios_base.py`, y quiero que el worker reutilice esta misma lógica.

### 4. Propuesta de Solución (Qué esperas lograr)

Describe el resultado final que deseas. No necesitas saber *exactamente* cómo implementarlo, para eso está el arquitecto, pero sí debes tener claro *qué* quieres.

**Ejemplo:**
> "Mi objetivo es que, al hacer clic en el botón, el backend inicie una tarea de Celery y responda inmediatamente. El frontend deberá mostrar el progreso de la tarea y notificar al usuario cuando se complete. El worker de Celery debe encargarse de toda la lógica de actualización de precios que hoy se hace en la petición HTTP."

### 5. Beneficios Esperados

Enumera las ventajas que traerá el cambio.

**Ejemplo:**
> -   **Mejora de la Experiencia de Usuario (UX):** El usuario no tendrá que esperar y podrá seguir usando la aplicación.
> -   **Fiabilidad:** Se eliminan los timeouts, asegurando que la actualización siempre se complete.
> -   **Escalabilidad:** El sistema podrá manejar un crecimiento futuro en el número de productos sin problemas de rendimiento.
> -   **Visibilidad:** El frontend podrá mostrar el progreso real de la tarea.

---

## Conclusión

Siguiendo esta estructura, le proporcionarás al arquitecto de software una visión completa y clara de tus necesidades. Esto no solo demuestra tu comprensión del problema, sino que también facilita una colaboración mucho más eficiente para diseñar e implementar la mejor solución posible.

**¡Ahora estás listo para solicitar ayuda como un profesional!**

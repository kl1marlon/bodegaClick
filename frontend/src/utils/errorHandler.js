/**
 * Utilidades para el manejo de errores en la aplicación
 */

/**
 * Formatea un error de API para mostrar un mensaje amigable al usuario
 * @param {Object|string} error - El error a formatear
 * @param {string} defaultMessage - Mensaje por defecto si no se puede extraer uno del error
 * @returns {string} Mensaje de error formateado
 */
export const formatApiError = (error, defaultMessage = 'Ocurrió un error inesperado') => {
  // Si el error es una cadena, devolverla directamente
  if (typeof error === 'string') {
    return error;
  }

  // Si hay un mensaje en error.payload (típico de Redux Toolkit rejectWithValue)
  if (error.payload) {
    return error.payload;
  }

  // Si hay un mensaje en error.response.data (respuesta de API)
  if (error.response && error.response.data) {
    if (typeof error.response.data === 'string') {
      return error.response.data;
    }
    if (error.response.data.error) {
      return error.response.data.error;
    }
    if (error.response.data.detail) {
      return error.response.data.detail;
    }
  }

  // Si tiene un message estándar
  if (error.message) {
    return error.message;
  }

  // Si no se pudo extraer un mensaje útil, usar el default
  return defaultMessage;
};

/**
 * Proporciona una sugerencia de solución basada en el tipo de error
 * @param {Object|string} error - El error para el que se requiere sugerencia
 * @returns {string|null} Sugerencia de solución o null si no hay sugerencia
 */
export const getSolutionSuggestion = (error) => {
  if (typeof error === 'string') {
    // Errores de conectividad
    if (error.includes('No se recibió respuesta del servidor')) {
      return `
        1. Verifica tu conexión a Internet
        2. La API podría estar caída - Verifica el estado del servicio de Railway
        3. Intenta acceder directamente al API en: https://bodegaclick-production.up.railway.app/api/
        4. Si estás en desarrollo local, verifica que el servidor backend esté funcionando
      `;
    }
    // Errores de autenticación
    if (error.includes('401') || error.includes('Unauthorized')) {
      return 'Tu sesión podría haber expirado. Intenta recargar la página o iniciar sesión nuevamente.';
    }
    // Errores de permisos
    if (error.includes('403') || error.includes('Forbidden')) {
      return 'No tienes permisos suficientes para realizar esta acción. Contacta al administrador.';
    }
  } else if (error && error.message) {
    // Errores de red específicos
    if (error.message.includes('Network Error')) {
      return `
        Problema de red detectado:
        1. Verifica tu conexión a Internet
        2. Si estás usando VPN, prueba desactivándola
        3. Comprueba si puedes acceder a otros sitios web
        4. Verifica la URL de la API en la configuración
      `;
    }
    // Errores de CORS
    if (error.message.includes('CORS')) {
      return `
        Error de CORS (Cross-Origin Resource Sharing):
        1. Verifica que los dominios frontend y backend estén correctamente configurados
        2. En desarrollo local, asegúrate de que el servidor tenga CORS habilitado para tu dominio
        3. Contacta al administrador del sistema si el problema persiste
      `;
    }
    // Errores de timeout
    if (error.message.includes('timeout')) {
      return 'La solicitud tardó demasiado tiempo. El servidor podría estar sobrecargado o la conexión es lenta.';
    }
  }

  // Si no coincide con ningún patrón específico
  return null;
};

/**
 * Verifica si un error es debido a problemas de red/conectividad
 * @param {Object|string} error - El error a verificar
 * @returns {boolean} true si es un error de conectividad
 */
export const isConnectivityError = (error) => {
  if (!error) return false;
  
  if (typeof error === 'string') {
    return (
      error.includes('Network Error') ||
      error.includes('No se recibió respuesta') ||
      error.includes('Failed to fetch') ||
      error.includes('timeout') ||
      error.includes('connection')
    );
  }
  
  if (error.message) {
    return (
      error.message.includes('Network Error') ||
      error.message.includes('Failed to fetch') ||
      error.message.includes('timeout') ||
      error.message.includes('connection')
    );
  }
  
  return false;
};

export default {
  formatApiError,
  getSolutionSuggestion,
  isConnectivityError
}; 
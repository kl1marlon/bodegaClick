/**
 * Utilidad para manejar errores HTTP y de red
 */

/**
 * Formatea un error para mostrar información relevante al usuario
 * @param {Error} error - El error capturado
 * @param {string} defaultMessage - Mensaje por defecto si no se puede determinar el error
 * @returns {string} - Mensaje de error formateado
 */
export const formatApiError = (error, defaultMessage = 'Ocurrió un error inesperado') => {
  if (!error) return defaultMessage;
  
  // Si es un error de axios con respuesta del servidor
  if (error.response) {
    const statusCode = error.response.status;
    
    // Manejar códigos de error comunes
    switch (statusCode) {
      case 400:
        return 'Solicitud incorrecta. Verifique los datos enviados.';
      case 401:
        return 'No autorizado. Por favor inicie sesión nuevamente.';
      case 403:
        return 'Acceso prohibido. No tiene permisos para esta acción.';
      case 404:
        return 'Recurso no encontrado. La URL solicitada no existe.';
      case 500:
        return 'Error interno del servidor. Por favor intente más tarde.';
      case 502:
        return 'Error de puerta de enlace. Hay problemas de comunicación entre servidores.';
      case 503:
        return 'Servicio no disponible. El servidor está sobrecargado o en mantenimiento.';
      default:
        if (error.response.data && error.response.data.error) {
          return `Error (${statusCode}): ${error.response.data.error}`;
        }
        return `Error de servidor (${statusCode}). Por favor intente más tarde.`;
    }
  }
  
  // Si la petición fue hecha pero no hubo respuesta
  if (error.request) {
    return 'No se recibió respuesta del servidor. Verifique su conexión a internet.';
  }
  
  // Error en la configuración de la petición
  if (error.message) {
    if (error.message.includes('Network Error')) {
      return 'Error de red. Verifique su conexión a internet.';
    }
    return error.message;
  }
  
  // Si es un string simple
  if (typeof error === 'string') {
    return error;
  }
  
  return defaultMessage;
};

/**
 * Verifica si hay problemas de CORS
 * @param {Error} error - El error capturado
 * @returns {boolean} - true si parece ser un error de CORS
 */
export const isCorsError = (error) => {
  if (!error) return false;
  
  // Mensajes comunes de error de CORS
  const corsErrorPatterns = [
    'Access-Control-Allow-Origin',
    'CORS',
    'cross-origin',
    'Cross-Origin Request Blocked',
    'from origin',
    'has been blocked by CORS policy'
  ];
  
  const errorMsg = error.message || '';
  return corsErrorPatterns.some(pattern => errorMsg.includes(pattern));
};

/**
 * Sugiere soluciones para errores comunes
 * @param {Error} error - El error capturado
 * @returns {string|null} - Sugerencia de solución o null si no hay sugerencias
 */
export const getSolutionSuggestion = (error) => {
  if (!error) return null;
  
  // Sugerencia para problemas de CORS
  if (isCorsError(error)) {
    return 'Este parece ser un problema de CORS. Verifique que el backend tenga configurados los encabezados CORS correctamente.';
  }
  
  // Sugerencias para errores de red
  if (error.message && error.message.includes('Network Error')) {
    return 'Verifique su conexión a internet y asegúrese de que el servidor API esté funcionando.';
  }
  
  // Sugerencias para problemas de autenticación
  if (error.response && [401, 403].includes(error.response.status)) {
    return 'Intente cerrar sesión y volver a iniciar sesión para renovar sus credenciales.';
  }
  
  return null;
};

export default {
  formatApiError,
  isCorsError,
  getSolutionSuggestion
}; 
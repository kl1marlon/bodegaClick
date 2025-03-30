import axios from 'axios';

// Usar la configuración dinámica si está disponible, o fallback a variables de entorno o localhost
const getApiBaseUrl = () => {
  // Primero intentar usar la configuración dinámica
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  // Si no está disponible, usar variable de entorno o localhost
  return process.env.REACT_APP_API_URL || 'http://localhost:8000';
};

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  }
});

// Para depuración
console.log('API baseURL:', api.defaults.baseURL);

export const fetchProductosAPI = () => api.get('/api/productos/');
export const fetchTasaCambioAPI = (tipo) => api.get(`/api/tasas-cambio/?tipo=${tipo}`);
export const createFacturaAPI = (data) => api.post('/api/facturas/', data);

export default api; 
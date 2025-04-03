import axios from 'axios';

// Usar la configuración dinámica si está disponible, o fallback a variables de entorno o localhost
const getApiBaseUrl = () => {
  // Primero intentar usar la configuración dinámica
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  // Si no está disponible, usar variable de entorno o localhost
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const api = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  }
});

// Para depuración
console.log('API baseURL configurada:', api.defaults.baseURL);

// Endpoints correctos - sin duplicar /api/ si ya está en la baseURL
export const fetchProductosAPI = () => api.get('/productos/');
export const fetchTasaCambioAPI = (tipo) => api.get(`/tasas-cambio/?tipo=${tipo}`);
export const createFacturaAPI = (data) => api.post('/facturas/', data);

export default api; 
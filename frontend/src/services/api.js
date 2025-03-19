import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  }
});

export const fetchProductosAPI = () => api.get('/api/productos/');
export const fetchTasaCambioAPI = (tipo) => api.get(`/api/tasas-cambio/?tipo=${tipo}`);
export const createFacturaAPI = (data) => api.post('/api/facturas/', data);

export default api; 
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import { fetchFacturasAPI } from '../services/api';
import { detectApiUrl } from '../utils/apiTest';

// Variable para almacenar la URL del API que funciona
let WORKING_API_URL = null;

// Función para obtener la URL de la API con verificación
const getApiUrl = async () => {
  // Si ya tenemos una URL que sabemos que funciona, usarla
  if (WORKING_API_URL) {
    return WORKING_API_URL;
  }
  
  // Probar diferentes URLs hasta encontrar una que funcione
  try {
    console.log('Detectando URL de API...');
    const result = await detectApiUrl();
    if (result.success) {
      console.log('✅ URL de API detectada:', result.url);
      WORKING_API_URL = result.url;
      return result.url;
    }
  } catch (error) {
    console.error('Error al detectar URL de API:', error);
  }
  
  // Fallback a métodos anteriores
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

// Thunks asíncronos
export const fetchFacturas = createAsyncThunk(
  'facturas/fetchFacturas',
  async (filtros = {}, { rejectWithValue }) => {
    try {
      // Normalizar todos los parámetros de filtrado
      const apiParams = {
        // Parámetros de fecha (soporta tanto los nuevos como los antiguos nombres)
        fechaDesde: filtros.fechaDesde || filtros.fechaInicio || null,
        fechaHasta: filtros.fechaHasta || filtros.fechaFin || null,
        // Parámetros adicionales si son necesarios en el futuro
        montoMinUSD: filtros.montoMinUSD || null,
        montoMaxUSD: filtros.montoMaxUSD || null,
        sincronizado: filtros.sincronizado && filtros.sincronizado !== 'todos' ? 
          (filtros.sincronizado === 'si') : null,
        tipoTasa: filtros.tipoTasa && filtros.tipoTasa !== 'todos' ? 
          filtros.tipoTasa : null,
      };
      
      console.log('Obteniendo facturas con filtros:', apiParams);
      
      // Usar la nueva función API que maneja los parámetros internamente
      const response = await fetchFacturasAPI(apiParams);
      
      // Verificar si la respuesta contiene datos
      if (!response.data || (Array.isArray(response.data) && response.data.length === 0)) {
        console.log('La respuesta no contiene facturas o está vacía');
        return [];
      }
      
      console.log('Respuesta recibida:', response.data);
      
      // Asegurar que los valores numéricos sean números
      const facturas = Array.isArray(response.data) ? response.data : [];
      return facturas.map(factura => ({
        ...factura,
        total_usd: parseFloat(factura.total_usd) || 0,
        total_bs: parseFloat(factura.total_bs) || 0,
        porcentaje_ganancia: parseFloat(factura.porcentaje_ganancia) || 30
      }));
    } catch (error) {
      console.error('Error en fetchFacturas:', error);
      
      let errorMessage = 'No se pudieron cargar las facturas';
      
      if (error.response) {
        errorMessage += ` - Status: ${error.response.status}`;
        if (error.response.data && error.response.data.error) {
          errorMessage += ` - ${error.response.data.error}`;
        }
      } else if (error.request) {
        errorMessage += ' - No se recibió respuesta del servidor';
      } else {
        errorMessage += ` - ${error.message}`;
      }
      
      return rejectWithValue(errorMessage);
    }
  }
);

export const fetchFacturaDetalle = createAsyncThunk(
  'facturas/fetchFacturaDetalle',
  async (id, { rejectWithValue }) => {
    try {
      const API_URL = await getApiUrl();
      console.log(`Obteniendo detalle de factura ID: ${id} desde ${API_URL}`);
      
      const response = await axios.get(`${API_URL}/facturas/${id}/`, {
        timeout: 15000
        // Encabezados eliminados temporalmente hasta que se actualice la configuración CORS en el backend
        // headers: {
        //   'Cache-Control': 'no-cache'
        // }
      });
      
      // Verificar si la respuesta contiene datos
      if (!response.data) {
        return rejectWithValue('No se encontraron datos para esta factura');
      }
      
      console.log('Detalle de factura recibido:', response.data);
      
      // Procesar los datos para asegurar que los valores numéricos sean números
      const factura = response.data;
      
      // Convertir valores numéricos
      const facturaProcessed = {
        ...factura,
        total_usd: parseFloat(factura.total_usd) || 0,
        total_bs: parseFloat(factura.total_bs) || 0,
        porcentaje_ganancia: parseFloat(factura.porcentaje_ganancia) || 30
      };
      
      // Procesar detalles si existen
      if (factura.detalles && Array.isArray(factura.detalles)) {
        facturaProcessed.detalles = factura.detalles.map(detalle => ({
          ...detalle,
          cantidad: parseFloat(detalle.cantidad) || 0,
          precio_unitario: parseFloat(detalle.precio_unitario) || 0,
          total: parseFloat(detalle.total) || 0,
          precio_compra_usd: parseFloat(detalle.precio_compra_usd) || 0,
          unidades_paquete: parseFloat(detalle.unidades_paquete) || 1,
          porcentaje_ganancia: parseFloat(detalle.porcentaje_ganancia) || facturaProcessed.porcentaje_ganancia
        }));
      } else {
        facturaProcessed.detalles = [];
      }
      
      return facturaProcessed;
    } catch (error) {
      console.error('Error al obtener detalle de factura:', error);
      
      let errorMessage = `Error al obtener detalle de factura ID: ${id}`;
      
      if (error.response) {
        errorMessage += ` - Status: ${error.response.status}`;
      } else if (error.request) {
        errorMessage += ' - No se recibió respuesta del servidor';
      } else {
        errorMessage += ` - ${error.message}`;
      }
      
      return rejectWithValue(errorMessage);
    }
  }
);

export const sincronizarFactura = createAsyncThunk(
  'facturas/sincronizarFactura',
  async (id, { rejectWithValue }) => {
    try {
      const API_URL = await getApiUrl();
      const response = await axios.post(`${API_URL}/facturas/${id}/sincronizar/`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Error al sincronizar la factura');
    }
  }
);

export const createFactura = createAsyncThunk(
  'facturas/createFactura',
  async (facturaData, { rejectWithValue }) => {
    try {
      const API_URL = await getApiUrl();
      const response = await axios.post(`${API_URL}/facturas/`, facturaData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Error al crear la factura');
    }
  }
);

// Nuevos Thunks asíncronos optimizados
export const fetchFacturasOptimizado = createAsyncThunk(
  'facturas/fetchFacturasOptimizado',
  async (params = {}, { rejectWithValue }) => {
    try {
      // Obtener la URL de la API
      const API_URL = await getApiUrl();
      console.log('URL de API usada (optimizado):', API_URL);
      
      // Construir parámetros de consulta
      const queryParams = new URLSearchParams();
      
      // Parámetros de paginación
      if (params.page) queryParams.append('page', params.page);
      if (params.pageSize) queryParams.append('page_size', params.pageSize);
      
      // Parámetros de filtro por fecha
      if (params.fechaDesde) queryParams.append('fecha_desde', params.fechaDesde);
      if (params.fechaHasta) queryParams.append('fecha_hasta', params.fechaHasta);
      
      // Añadir timestamp para evitar caché
      queryParams.append('_', Date.now());
      
      console.log('Parámetros de filtrado completos:', Object.fromEntries(queryParams.entries()));
      
      // Usar el nuevo endpoint optimizado
      const requestUrl = `${API_URL}/facturas/listado_simple/?${queryParams.toString()}`;
      console.log('Haciendo fetch a URL optimizada:', requestUrl);
      
      // Hacer la solicitud con un timeout más largo
      const response = await axios.get(requestUrl, {
        timeout: 30000 // 30 segundos
      });
      
      console.log('Respuesta optimizada recibida:', response.data);
      
      // Verificar la estructura de la respuesta y adaptarla si es necesario
      let processedResponse;
      
      if (Array.isArray(response.data)) {
        // Si la respuesta es un array, adaptarla al formato esperado
        console.log('La respuesta es un array, adaptando formato...');
        processedResponse = {
          results: response.data,
          count: response.data.length,
          page: params.page || 1,
          page_size: params.pageSize || 20,
          total_pages: Math.ceil(response.data.length / (params.pageSize || 20))
        };
      } else if (response.data && response.data.results) {
        // Si la respuesta ya tiene el formato esperado
        processedResponse = response.data;
      } else {
        // Si la respuesta tiene otro formato inesperado
        console.error('Estructura de respuesta inesperada:', response.data);
        processedResponse = {
          results: response.data ? (typeof response.data === 'object' ? [response.data] : []) : [],
          count: response.data ? 1 : 0,
          page: params.page || 1,
          page_size: params.pageSize || 20,
          total_pages: response.data ? 1 : 0
        };
      }
      
      console.log('Respuesta procesada:', processedResponse);
      return processedResponse;
    } catch (error) {
      console.error('Error en fetchFacturasOptimizado:', error);
      
      let errorMessage = 'No se pudieron cargar las facturas';
      
      if (error.response) {
        errorMessage += ` - Status: ${error.response.status}`;
        if (error.response.data && error.response.data.error) {
          errorMessage += ` - ${error.response.data.error}`;
        }
      } else if (error.request) {
        errorMessage += ' - No se recibió respuesta del servidor';
      } else {
        errorMessage += ` - ${error.message}`;
      }
      
      return rejectWithValue(errorMessage);
    }
  }
);

export const fetchFacturaDetalleOptimizado = createAsyncThunk(
  'facturas/fetchFacturaDetalleOptimizado',
  async (id, { rejectWithValue }) => {
    try {
      const API_URL = await getApiUrl();
      console.log(`Obteniendo detalle optimizado de factura ID: ${id} desde ${API_URL}`);
      
      // Usar el nuevo endpoint optimizado
      const response = await axios.get(`${API_URL}/facturas/${id}/detalle_simple/`, {
        timeout: 30000 // 30 segundos
      });
      
      console.log('Detalle de factura optimizado recibido:', response.data);
      
      return response.data;
    } catch (error) {
      console.error('Error al obtener detalle optimizado de factura:', error);
      
      let errorMessage = `Error al obtener detalle de factura ID: ${id}`;
      
      if (error.response) {
        errorMessage += ` - Status: ${error.response.status}`;
      } else if (error.request) {
        errorMessage += ' - No se recibió respuesta del servidor';
      } else {
        errorMessage += ` - ${error.message}`;
      }
      
      return rejectWithValue(errorMessage);
    }
  }
);

// Slice de Redux
const facturasSlice = createSlice({
  name: 'facturas',
  initialState: {
    items: [],
    detalleActual: null,
    status: 'idle', // 'idle' | 'loading' | 'succeeded' | 'failed'
    error: null,
    sincronizacionStatus: 'idle',
    sincronizacionError: null,
    creacionStatus: 'idle',
    creacionError: null,
    paginacion: {
      page: 1,
      pageSize: 20,
      totalPages: 0,
      totalItems: 0
    }
  },
  reducers: {
    // Reducers adicionales si son necesarios
    setPage: (state, action) => {
      state.paginacion.page = action.payload;
    },
    setPageSize: (state, action) => {
      state.paginacion.pageSize = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      // Manejar fetchFacturas original
      .addCase(fetchFacturas.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchFacturas.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
        state.error = null;
      })
      .addCase(fetchFacturas.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Error desconocido';
      })
      
      // Manejar fetchFacturasOptimizado
      .addCase(fetchFacturasOptimizado.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchFacturasOptimizado.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload.results;
        state.paginacion = {
          page: action.payload.page,
          pageSize: action.payload.page_size,
          totalPages: action.payload.total_pages,
          totalItems: action.payload.count
        };
        state.error = null;
      })
      .addCase(fetchFacturasOptimizado.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Error desconocido';
      })
      
      // Manejar fetchFacturaDetalle original
      .addCase(fetchFacturaDetalle.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchFacturaDetalle.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.detalleActual = action.payload;
        state.error = null;
      })
      .addCase(fetchFacturaDetalle.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Error desconocido';
      })
      
      // Manejar fetchFacturaDetalleOptimizado
      .addCase(fetchFacturaDetalleOptimizado.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchFacturaDetalleOptimizado.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.detalleActual = action.payload;
        state.error = null;
      })
      .addCase(fetchFacturaDetalleOptimizado.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || 'Error desconocido';
      })
      
      // Manejar sincronizarFactura
      .addCase(sincronizarFactura.pending, (state) => {
        state.sincronizacionStatus = 'loading';
      })
      .addCase(sincronizarFactura.fulfilled, (state, action) => {
        state.sincronizacionStatus = 'succeeded';
        
        // Actualizar la factura en la lista
        const index = state.items.findIndex(f => f.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        
        // Actualizar detalle actual si corresponde
        if (state.detalleActual && state.detalleActual.id === action.payload.id) {
          state.detalleActual = action.payload;
        }
        
        state.sincronizacionError = null;
      })
      .addCase(sincronizarFactura.rejected, (state, action) => {
        state.sincronizacionStatus = 'failed';
        state.sincronizacionError = action.payload || 'Error desconocido';
      })
      
      // Manejar createFactura
      .addCase(createFactura.pending, (state) => {
        state.creacionStatus = 'loading';
      })
      .addCase(createFactura.fulfilled, (state, action) => {
        state.creacionStatus = 'succeeded';
        state.items = [action.payload, ...state.items]; // Añadir la nueva factura al principio
        state.creacionError = null;
      })
      .addCase(createFactura.rejected, (state, action) => {
        state.creacionStatus = 'failed';
        state.creacionError = action.payload || 'Error desconocido';
      });
  },
});

export default facturasSlice.reducer;
export const { setPage, setPageSize } = facturasSlice.actions;
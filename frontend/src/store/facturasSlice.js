import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// URLs base para las APIs
const getApiUrl = () => {
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const API_URL = getApiUrl();

// Thunks asíncronos
export const fetchFacturas = createAsyncThunk(
  'facturas/fetchFacturas',
  async (filtros = {}, { rejectWithValue }) => {
    try {
      // Diagnostico de la URL
      console.log('URL de API usada:', API_URL);
      
      // Construir params para filtros
      const params = new URLSearchParams();
      
      if (filtros.fechaInicio) params.append('fecha_inicio', filtros.fechaInicio);
      if (filtros.fechaFin) params.append('fecha_fin', filtros.fechaFin);
      if (filtros.montoMinUSD) params.append('monto_min_usd', filtros.montoMinUSD);
      if (filtros.montoMaxUSD) params.append('monto_max_usd', filtros.montoMaxUSD);
      if (filtros.sincronizado && filtros.sincronizado !== 'todos') {
        params.append('sincronizado', filtros.sincronizado === 'si');
      }
      if (filtros.tipoTasa && filtros.tipoTasa !== 'todos') {
        params.append('tipo_tasa', filtros.tipoTasa);
      }
      
      const requestUrl = `${API_URL}/facturas/?${params.toString()}`;
      console.log('Haciendo fetch a URL:', requestUrl);
      
      const response = await axios.get(requestUrl);
      console.log('Respuesta recibida:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error en fetchFacturas:', error);
      console.error('Mensaje de error:', error.message);
      console.error('Respuesta del servidor:', error.response);
      
      // Crear un mensaje de error más detallado
      let errorMessage = 'No se pudieron cargar las facturas';
      
      if (error.response) {
        // El servidor respondió con un código de error
        errorMessage += ` - Status: ${error.response.status}`;
        if (error.response.data && error.response.data.error) {
          errorMessage += ` - ${error.response.data.error}`;
        }
      } else if (error.request) {
        // La petición fue hecha pero no se recibió respuesta
        errorMessage += ' - No se recibió respuesta del servidor';
      } else {
        // Algo salió mal en la configuración de la petición
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
      const response = await axios.get(`${API_URL}/facturas/${id}/`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'No se pudo cargar el detalle de la factura');
    }
  }
);

export const sincronizarFactura = createAsyncThunk(
  'facturas/sincronizarFactura',
  async (id, { rejectWithValue }) => {
    try {
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
      const response = await axios.post(`${API_URL}/facturas/`, facturaData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Error al crear la factura');
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
  },
  reducers: {
    // Reducers adicionales si son necesarios
  },
  extraReducers: (builder) => {
    builder
      // Manejar fetchFacturas
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
      
      // Manejar fetchFacturaDetalle
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
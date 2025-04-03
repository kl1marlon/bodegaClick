import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';
import api from '../services/api'; // Importar la instancia de api configurada

// Función auxiliar para obtener URLs completas para casos donde no usamos la instancia de api
const getApiUrl = () => {
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL; // Ya incluye /api
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const API_URL = getApiUrl();

// Usar la instancia de API configurada en lugar de axios directamente cuando sea posible
export const fetchProductos = createAsyncThunk(
  'productos/fetchProductos',
  async () => {
    console.log('Fetching productos usando API configurada');
    try {
      const response = await api.get('/productos/');
      return response.data;
    } catch (error) {
      console.error('Error al cargar productos:', error);
      throw error;
    }
  }
);

export const syncFromLoyverse = createAsyncThunk(
  'productos/syncFromLoyverse',
  async (opciones = {}) => {
    try {
      // Configurar opciones por defecto
      const opcionesSincronizacion = {
        actualizar_precios: opciones.actualizar_precios !== undefined ? opciones.actualizar_precios : true,
        categorias: opciones.categorias || null,
        tipo_tasa: opciones.tipo_tasa || null,
        productos_ids: opciones.productos_ids || null,
        forzar_exportar: opciones.forzar_exportar || false,
        tamaño_lote: opciones.tamaño_lote || 10 // Tamaño de lote predeterminado
      };
      
      console.log(`Iniciando sincronización de productos desde Loyverse con opciones:`, opcionesSincronizacion);
      
      // Solicitar el inicio de la tarea asíncrona
      const adminToken = 'admin_secret_token_default'; // El mismo que usas en syncInventory
      
      const response = await axios.post(`${API_URL}/tareas/iniciar/`, {
        type: 'sync_prices',
        params: opcionesSincronizacion
      }, {
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': adminToken
        }
      });
      
      console.log('Respuesta de iniciar tarea de sincronización:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error en sincronización:', error.response?.data || error.message);
      throw error;
    }
  }
);

export const syncInventory = createAsyncThunk(
  'productos/syncInventory',
  async (opciones = {}, { rejectWithValue }) => {
    try {
      console.log(`Iniciando sincronización de inventario desde Loyverse con opciones:`, opciones);
      
      // Token de administrador - Usando el valor predeterminado que coincide con la configuración del backend
      const adminToken = 'admin_secret_token_default';
      
      // Usar el nuevo endpoint de tareas asíncronas
      const response = await axios.post(`${API_URL}/tareas/iniciar/`, {
        type: 'sync_inventory',
        params: {
          force: opciones.force !== undefined ? opciones.force : false
        }
      }, {
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': adminToken
        }
      });
      
      console.log('Respuesta de iniciar tarea de sincronización:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error en sincronización de inventario:', error);
      
      // Extraer mensaje de error detallado para mostrar al usuario
      let errorMessage = 'Error desconocido en la sincronización de inventario';
      
      if (error.response) {
        // Error con respuesta del servidor
        const responseData = error.response.data;
        
        if (responseData.error) {
          errorMessage = responseData.error;
        } else if (responseData.message) {
          errorMessage = responseData.message;
        } else if (responseData.traceback) {
          // Si hay un traceback, extraer la última línea que suele contener el mensaje de error
          const lastLine = responseData.traceback.split('\n').filter(Boolean).pop();
          errorMessage = lastLine || errorMessage;
        }
        
        console.error('Detalle del error:', responseData);
      } else if (error.message) {
        // Error sin respuesta del servidor (network error, timeout, etc.)
        errorMessage = error.message;
      }
      
      return rejectWithValue(errorMessage);
    }
  }
);

export const updateProductoTipoTasa = createAsyncThunk(
  'productos/updateProductoTipoTasa',
  async ({ productoId, tipoTasa }) => {
    try {
      const response = await axios.patch(`${API_URL}/productos/${productoId}/`, {
        tipo_tasa: tipoTasa
      });
      return response.data;
    } catch (error) {
      console.error('Error al actualizar tipo_tasa:', error.response?.data || error.message);
      throw error;
    }
  }
);

// Nueva función para actualizar datos completos de un producto
export const updateProducto = createAsyncThunk(
  'productos/updateProducto',
  async (productoData) => {
    try {
      console.log('Actualizando producto con datos:', productoData);
      const response = await axios.patch(`${API_URL}/productos/${productoData.id}/`, productoData);
      return response.data;
    } catch (error) {
      console.error('Error al actualizar producto:', error.response?.data || error.message);
      throw error;
    }
  }
);

export const testCorsConnection = createAsyncThunk(
  'productos/testCorsConnection',
  async (_, { rejectWithValue }) => {
    try {
      console.log('Probando conexión CORS con el backend...');
      
      // Token de administrador para probar los encabezados
      const adminToken = 'admin_secret_token_default';
      
      const response = await axios.get(`${API_URL}/test-cors/`, {
        headers: {
          'X-Admin-Token': adminToken
        }
      });
      
      console.log('Respuesta de prueba CORS:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error en prueba CORS:', error);
      return rejectWithValue(error.message || 'Error desconocido en la prueba CORS');
    }
  }
);

const productosSlice = createSlice({
  name: 'productos',
  initialState: {
    items: [],
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProductos.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchProductos.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchProductos.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(syncFromLoyverse.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(syncFromLoyverse.fulfilled, (state) => {
        state.status = 'succeeded';
      })
      .addCase(syncFromLoyverse.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(syncInventory.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(syncInventory.fulfilled, (state) => {
        state.status = 'succeeded';
      })
      .addCase(syncInventory.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(updateProductoTipoTasa.fulfilled, (state, action) => {
        const index = state.items.findIndex(producto => producto.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(updateProducto.fulfilled, (state, action) => {
        const index = state.items.findIndex(producto => producto.id === action.payload.id);
        if (index !== -1) {
          // Actualizar el producto en el estado con los nuevos datos
          state.items[index] = {...state.items[index], ...action.payload};
        }
      })
      .addCase(testCorsConnection.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(testCorsConnection.fulfilled, (state) => {
        state.status = 'succeeded';
      })
      .addCase(testCorsConnection.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || action.error.message;
      });
  },
});

export default productosSlice.reducer; 
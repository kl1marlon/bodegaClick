import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Usar la configuración dinámica si está disponible
const getApiUrl = () => {
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const API_URL = getApiUrl();

export const fetchProductos = createAsyncThunk(
  'productos/fetchProductos',
  async () => {
    console.log('Fetching productos from:', API_URL);
    const response = await axios.get(`${API_URL}/productos/`);
    return response.data;
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
        forzar_exportar: opciones.forzar_exportar || false
      };
      
      console.log(`Iniciando sincronización de productos desde Loyverse con opciones:`, opcionesSincronizacion);
      
      const response = await axios.post(`${API_URL}/productos/sync_from_loyverse/`, opcionesSincronizacion);
      console.log('Respuesta de sincronización:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error en sincronización:', error.response?.data || error.message);
      throw error;
    }
  }
);

export const syncInventory = createAsyncThunk(
  'productos/syncInventory',
  async (opciones = {}) => {
    try {
      console.log(`Iniciando sincronización de inventario desde Loyverse con opciones:`, opciones);
      
      const response = await axios.post(`${API_URL}/sincronizar_inventario/`, {
        force: opciones.force !== undefined ? opciones.force : false
      }, {
        headers: {
          'X-Admin-Token': process.env.REACT_APP_ADMIN_SECRET_TOKEN || 'secret-token-placeholder'
        }
      });
      
      console.log('Respuesta de sincronización de inventario:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error en sincronización de inventario:', error.response?.data || error.message);
      throw error;
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
      });
  },
});

export default productosSlice.reducer; 
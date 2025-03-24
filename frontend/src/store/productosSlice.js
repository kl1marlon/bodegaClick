import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const fetchProductos = createAsyncThunk(
  'productos/fetchProductos',
  async () => {
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
        tamaño_lote: opciones.tamaño_lote || 20,
        direccion_sync: opciones.direccion_sync || 'bidireccional'
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
      .addCase(updateProductoTipoTasa.fulfilled, (state, action) => {
        const index = state.items.findIndex(producto => producto.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      });
  },
});

export default productosSlice.reducer; 
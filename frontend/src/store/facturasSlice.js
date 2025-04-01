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

export const fetchFacturas = createAsyncThunk(
  'facturas/fetchFacturas',
  async () => {
    const response = await axios.get(`${API_URL}/facturas/`);
    return response.data;
  }
);

export const fetchFacturaDetalle = createAsyncThunk(
  'facturas/fetchFacturaDetalle',
  async (id) => {
    const response = await axios.get(`${API_URL}/facturas/${id}/`);
    return response.data;
  }
);

export const createFactura = createAsyncThunk(
  'facturas/createFactura',
  async (facturaData) => {
    const response = await axios.post(`${API_URL}/facturas/`, facturaData);
    return response.data;
  }
);

export const sincronizarFactura = createAsyncThunk(
  'facturas/sincronizarFactura',
  async (id) => {
    const response = await axios.post(`${API_URL}/facturas/${id}/sincronizar/`);
    return response.data;
  }
);

export const actualizarProductoFactura = createAsyncThunk(
  'facturas/actualizarProductoFactura',
  async ({ facturaId, productoId, campo, valor }) => {
    const response = await axios.patch(
      `${API_URL}/facturas/${facturaId}/productos/${productoId}/`, 
      { [campo]: valor }
    );
    return response.data;
  }
);

export const exportarFactura = createAsyncThunk(
  'facturas/exportarFactura',
  async ({ id, formato }) => {
    const response = await axios.get(
      `${API_URL}/facturas/${id}/exportar/?formato=${formato}`,
      { responseType: 'blob' }
    );
    
    // Crear una URL para el blob y descargar el archivo
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `factura-${id}.${formato}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return { id, formato };
  }
);

const facturasSlice = createSlice({
  name: 'facturas',
  initialState: {
    items: [],
    currentFactura: null,
    detalleActual: null,
    status: 'idle',
    exportStatus: 'idle',
    error: null,
  },
  reducers: {
    setCurrentFactura: (state, action) => {
      state.currentFactura = action.payload;
    },
    clearCurrentFactura: (state) => {
      state.currentFactura = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Obtener listado de facturas
      .addCase(fetchFacturas.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchFacturas.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchFacturas.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      
      // Crear factura
      .addCase(createFactura.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(createFactura.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items.unshift(action.payload);
        state.currentFactura = null;
      })
      .addCase(createFactura.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      
      // Obtener detalle de factura
      .addCase(fetchFacturaDetalle.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchFacturaDetalle.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.detalleActual = action.payload;
      })
      .addCase(fetchFacturaDetalle.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      
      // Sincronizar factura
      .addCase(sincronizarFactura.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(sincronizarFactura.fulfilled, (state, action) => {
        state.status = 'succeeded';
        
        // Actualizar en el detalle
        if (state.detalleActual && state.detalleActual.id === action.payload.id) {
          state.detalleActual = action.payload;
        }
        
        // Actualizar en el listado
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
      })
      .addCase(sincronizarFactura.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      
      // Actualizar producto de factura
      .addCase(actualizarProductoFactura.fulfilled, (state, action) => {
        if (state.detalleActual && state.detalleActual.detalles) {
          // Encontrar y actualizar el producto en el detalle actual
          const index = state.detalleActual.detalles.findIndex(
            detalle => detalle.id === action.payload.id
          );
          
          if (index !== -1) {
            state.detalleActual.detalles[index] = action.payload;
          }
        }
      })
      
      // Exportar factura
      .addCase(exportarFactura.pending, (state) => {
        state.exportStatus = 'loading';
      })
      .addCase(exportarFactura.fulfilled, (state) => {
        state.exportStatus = 'succeeded';
      })
      .addCase(exportarFactura.rejected, (state, action) => {
        state.exportStatus = 'failed';
        state.error = action.error.message;
      });
  },
});

export const { setCurrentFactura, clearCurrentFactura } = facturasSlice.actions;
export default facturasSlice.reducer; 
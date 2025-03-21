import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const fetchFacturas = createAsyncThunk(
  'facturas/fetchFacturas',
  async () => {
    const response = await axios.get(`${API_URL}/facturas/`);
    return response.data;
  }
);

export const fetchFacturaById = createAsyncThunk(
  'facturas/fetchFacturaById',
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

const facturasSlice = createSlice({
  name: 'facturas',
  initialState: {
    items: [],
    currentFactura: null,
    status: 'idle',
    detailStatus: 'idle',
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
      .addCase(createFactura.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
        state.currentFactura = null;
      })
      .addCase(fetchFacturaById.pending, (state) => {
        state.detailStatus = 'loading';
      })
      .addCase(fetchFacturaById.fulfilled, (state, action) => {
        state.detailStatus = 'succeeded';
        state.currentFactura = action.payload;
      })
      .addCase(fetchFacturaById.rejected, (state, action) => {
        state.detailStatus = 'failed';
        state.error = action.error.message;
      });
  },
});

export const { setCurrentFactura, clearCurrentFactura } = facturasSlice.actions;
export default facturasSlice.reducer; 
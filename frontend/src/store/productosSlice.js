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
  async () => {
    const response = await axios.post(`${API_URL}/productos/sync_from_loyverse/`);
    return response.data;
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
      });
  },
});

export default productosSlice.reducer; 
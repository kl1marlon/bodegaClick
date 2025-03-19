import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const fetchTasasCambio = createAsyncThunk(
  'tasasCambio/fetchTasasCambio',
  async () => {
    const response = await axios.get(`${API_URL}/tasas-cambio/`);
    return response.data;
  }
);

export const fetchLatestTasa = createAsyncThunk(
  'tasasCambio/fetchLatestTasa',
  async (tipo) => {
    const response = await axios.get(`${API_URL}/tasas-cambio/latest/?tipo=${tipo}`);
    return response.data;
  }
);

export const createTasaCambio = createAsyncThunk(
  'tasasCambio/createTasaCambio',
  async (tasaData) => {
    const response = await axios.post(`${API_URL}/tasas-cambio/`, tasaData);
    return response.data;
  }
);

const tasasCambioSlice = createSlice({
  name: 'tasasCambio',
  initialState: {
    items: [],
    latestTasa: null,
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchTasasCambio.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchTasasCambio.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchTasasCambio.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(fetchLatestTasa.fulfilled, (state, action) => {
        state.latestTasa = action.payload;
      })
      .addCase(createTasaCambio.fulfilled, (state, action) => {
        state.items.unshift(action.payload);
      });
  },
});

export default tasasCambioSlice.reducer; 
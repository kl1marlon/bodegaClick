import { configureStore } from '@reduxjs/toolkit';
import productosReducer from './productosSlice';
import tasasCambioReducer from './tasasCambioSlice';
import facturasReducer from './facturasSlice';

const store = configureStore({
  reducer: {
    productos: productosReducer,
    tasasCambio: tasasCambioReducer,
    facturas: facturasReducer,
  },
});

export default store; 
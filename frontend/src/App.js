import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { esES } from '@mui/material/locale';
import Layout from './components/Layout';
import ListadoFacturas from './pages/ListadoFacturas';
import DetalleFactura from './pages/DetalleFactura';
import ListadoProductos from './pages/ListadoProductos';
import NuevaFactura from './pages/NuevaFactura';
import ListaDeFacturas from './pages/ListaDeFacturas';
import BusquedaProductoHistorial from './pages/BusquedaProductoHistorial';
import CrearProducto from './pages/CrearProducto';
import Login from './pages/Login';
import LoyverseDashboard from './pages/LoyverseDashboard';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
// Importar otros componentes según sea necesario

// Crear tema personalizado
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif'
    ].join(','),
  },
}, esES); // Configuración regional para español

function App() {
  return (
    <AuthProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Routes>
          {/* Ruta de login */}
          <Route path="/login" element={<Login />} />
          
          {/* Rutas protegidas */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout>
                <Navigate to="/lista-facturas" replace />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Rutas de Facturas - Versión Optimizada (predeterminada) */}
          <Route path="/facturas" element={
            <ProtectedRoute>
              <Layout>
                <Navigate to="/lista-facturas" replace />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/lista-facturas" element={
            <ProtectedRoute>
              <Layout>
                <ListaDeFacturas />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Rutas de Facturas - Versión Antigua (mantener temporalmente) */}
          <Route path="/facturas-legacy" element={
            <ProtectedRoute>
              <Layout>
                <ListadoFacturas />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Rutas compartidas entre ambas implementaciones */}
          <Route path="/facturas/nueva" element={
            <ProtectedRoute>
              <Layout>
                <NuevaFactura />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/facturas/:id" element={
            <ProtectedRoute>
              <Layout>
                <DetalleFactura />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Rutas de Productos */}
          <Route path="/productos" element={
            <ProtectedRoute>
              <Layout>
                <ListadoProductos />
              </Layout>
            </ProtectedRoute>
          } />
          <Route path="/crear-producto" element={
            <ProtectedRoute>
              <Layout>
                <CrearProducto />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Nueva ruta de Historial de Productos */}
          <Route path="/buscar-producto-historial" element={
            <ProtectedRoute>
              <Layout>
                <BusquedaProductoHistorial />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Ruta de Integración con Loyverse */}
          <Route path="/loyverse-dashboard" element={
            <ProtectedRoute>
              <Layout>
                <LoyverseDashboard />
              </Layout>
            </ProtectedRoute>
          } />
          
          {/* Ruta 404 - No encontrado */}
          <Route path="*" element={
            <ProtectedRoute>
              <Layout>
                <div style={{ padding: '2rem', textAlign: 'center' }}>
                  <h2>Página no encontrada</h2>
                  <p>La página que estás buscando no existe o ha sido movida.</p>
                </div>
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
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
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout>
        <Routes>
          {/* Ruta principal redirige a la implementación optimizada de facturas */}
          <Route path="/" element={<Navigate to="/lista-facturas" replace />} />
          
          {/* Rutas de Facturas - Versión Optimizada (predeterminada) */}
          <Route path="/facturas" element={<Navigate to="/lista-facturas" replace />} />
          <Route path="/lista-facturas" element={<ListaDeFacturas />} />
          
          {/* Rutas de Facturas - Versión Antigua (mantener temporalmente) */}
          <Route path="/facturas-legacy" element={<ListadoFacturas />} />
          
          {/* Rutas compartidas entre ambas implementaciones */}
          <Route path="/facturas/nueva" element={<NuevaFactura />} />
          <Route path="/facturas/:id" element={<DetalleFactura />} />
          
          {/* Rutas de Productos */}
          <Route path="/productos" element={<ListadoProductos />} />
          <Route path="/crear-producto" element={<CrearProducto />} />
          
          {/* Nueva ruta de Historial de Productos */}
          <Route path="/buscar-producto-historial" element={<BusquedaProductoHistorial />} />
          
          {/* Ruta 404 - No encontrado */}
          <Route path="*" element={
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <h2>Página no encontrada</h2>
              <p>La página que estás buscando no existe o ha sido movida.</p>
            </div>
          } />
        </Routes>
      </Layout>
    </ThemeProvider>
  );
}

export default App;
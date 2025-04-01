import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { esES } from '@mui/material/locale';
import Layout from './components/Layout';
import ListadoFacturas from './pages/ListadoFacturas';
import DetalleFactura from './pages/DetalleFactura';
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
          {/* Ruta principal redirige a facturas */}
          <Route path="/" element={<Navigate to="/facturas" replace />} />
          
          {/* Rutas de Facturas */}
          <Route path="/facturas" element={<ListadoFacturas />} />
          <Route path="/facturas/:id" element={<DetalleFactura />} />
          
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
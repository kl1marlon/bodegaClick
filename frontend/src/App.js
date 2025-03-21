import React from 'react';
import { Box, Container } from '@mui/material';
import { Routes, Route, Link } from 'react-router-dom';
import ListadoProductos from './pages/ListadoProductos';
import NuevaFactura from './pages/NuevaFactura';
import NotificacionInventario from './components/NotificacionInventario';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import InventoryIcon from '@mui/icons-material/Inventory';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ mb: 2 }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            BodegaClick
          </Typography>
          <Button 
            component={Link} 
            to="/" 
            color="inherit" 
            startIcon={<InventoryIcon />}
            sx={{ mr: 2 }}
          >
            Inventario
          </Button>
          <Button 
            component={Link} 
            to="/factura" 
            color="inherit"
            startIcon={<ShoppingCartIcon />}
          >
            Nueva Factura
          </Button>
        </Toolbar>
      </AppBar>
      
      <Container component="main" sx={{ mt: 2, mb: 4, flex: 1 }}>
        <Routes>
          <Route path="/" element={<ListadoProductos />} />
          <Route path="/factura" element={<NuevaFactura />} />
        </Routes>
      </Container>
      
      <NotificacionInventario />
    </Box>
  );
}

export default App; 
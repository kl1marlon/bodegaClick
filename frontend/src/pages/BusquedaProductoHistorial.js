import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Paper, 
  Box, 
  Grid, 
  CircularProgress, 
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Button,
  Alert,
  AlertTitle,
  Chip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DescriptionIcon from '@mui/icons-material/Description';
import moment from 'moment';
import 'moment/locale/es';
import axios from 'axios';
import BuscadorProductos from '../components/factura/BuscadorProductos';

moment.locale('es');

// Función para obtener la URL de la API (similar a facturasSlice.js)
const getApiUrl = async () => {
  // Si ya tenemos una URL que sabemos que funciona, usarla (en una implementación real, esto vendría de una función compartida)
  
  // Fallback a métodos anteriores
  if (window.ENV && window.ENV.API_URL) {
    return window.ENV.API_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
};

const BusquedaProductoHistorial = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  // Estados
  const [productosLista, setProductosLista] = useState([]);
  const [productoSeleccionado, setProductoSeleccionado] = useState(null);
  const [cantidad, setCantidad] = useState(1);
  const [cargandoProductos, setCargandoProductos] = useState(false);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [historialCompras, setHistorialCompras] = useState([]);
  const [error, setError] = useState(null);
  
  // Cargar productos al inicializar
  useEffect(() => {
    const cargarProductos = async () => {
      setCargandoProductos(true);
      try {
        const API_URL = await getApiUrl();
        const response = await axios.get(`${API_URL}/productos/`);
        setProductosLista(response.data);
      } catch (error) {
        console.error("Error al cargar productos:", error);
        setError("No se pudieron cargar los productos. Verifica tu conexión a internet.");
      } finally {
        setCargandoProductos(false);
      }
    };
    
    cargarProductos();
  }, []);
  
  // Función para buscar el historial de compras de un producto
  const buscarHistorialCompras = async (productoId) => {
    setCargandoHistorial(true);
    setError(null);
    try {
      const API_URL = await getApiUrl();
      const response = await axios.get(`${API_URL}/facturas/buscar-por-producto/${productoId}/`);
      
      // Convertir y ordenar resultados por fecha (más reciente primero)
      const historialOrdenado = response.data.sort((a, b) => 
        new Date(b.fecha) - new Date(a.fecha)
      );
      
      setHistorialCompras(historialOrdenado);
      
      if (historialOrdenado.length === 0) {
        setError("No se encontró historial de compras para este producto.");
      }
    } catch (error) {
      console.error("Error al buscar historial de compras:", error);
      setError("No se pudo obtener el historial de compras. Verifica tu conexión a internet.");
      setHistorialCompras([]);
    } finally {
      setCargandoHistorial(false);
    }
  };
  
  // Manejar selección de producto
  const handleProductoSelect = (producto) => {
    setProductoSeleccionado(producto);
    buscarHistorialCompras(producto.id);
  };
  
  // Función para ver detalle de una factura
  const verDetalleFactura = (facturaId) => {
    navigate(`/facturas/${facturaId}`);
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      {/* Encabezado */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Box display="flex" alignItems="center" mb={1}>
            <Button 
              startIcon={<ArrowBackIcon />} 
              onClick={() => navigate('/facturas')}
              sx={{ mr: 2 }}
            >
              Volver
            </Button>
            <Typography variant="h4">
              Historial de Compras por Producto
            </Typography>
          </Box>
          <Divider sx={{ mb: 2 }} />
        </Grid>
      </Grid>
      
      {/* Buscador de productos */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Buscar Producto
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          Selecciona un producto para ver su historial de compras
        </Typography>
        
        {cargandoProductos ? (
          <Box display="flex" justifyContent="center" my={3}>
            <CircularProgress size={30} />
          </Box>
        ) : (
          <BuscadorProductos 
            productos={productosLista}
            onProductoSelect={handleProductoSelect}
            cantidad={cantidad}
            onCantidadChange={setCantidad}
          />
        )}
      </Paper>
      
      {/* Información del producto seleccionado */}
      {productoSeleccionado && (
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Producto Seleccionado
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="textSecondary">Nombre</Typography>
              <Typography variant="body1">{productoSeleccionado.nombre}</Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="textSecondary">Categoría</Typography>
              <Typography variant="body1">{productoSeleccionado.categoria || 'Sin categoría'}</Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" color="textSecondary">Precio Base</Typography>
              <Typography variant="body1">${parseFloat(productoSeleccionado.precio_base || 0).toFixed(2)}</Typography>
            </Grid>
          </Grid>
        </Paper>
      )}
      
      {/* Historial de compras */}
      {productoSeleccionado && (
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Historial de Compras
          </Typography>
          
          {error && (
            <Alert severity="info" sx={{ mb: 3 }}>
              <AlertTitle>Información</AlertTitle>
              {error}
            </Alert>
          )}
          
          {cargandoHistorial ? (
            <Box display="flex" justifyContent="center" my={4}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {historialCompras.length > 0 && (
                <Card sx={{ mb: 4, bgcolor: '#f9f9f9', border: '1px solid #e0e0e0' }}>
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Última Compra
                    </Typography>
                    <Typography variant="h5" color="primary" gutterBottom>
                      {moment(historialCompras[0].fecha).format('DD/MM/YYYY')}
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="textSecondary">Factura</Typography>
                        <Typography>{historialCompras[0].numero || `#${historialCompras[0].id}`}</Typography>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="textSecondary">Precio de Compra</Typography>
                        <Typography>${parseFloat(historialCompras[0].precio_unitario || 0).toFixed(2)}</Typography>
                      </Grid>
                      <Grid item xs={12} sx={{ mt: 1 }}>
                        <Button 
                          variant="outlined"
                          size="small"
                          startIcon={<DescriptionIcon />}
                          onClick={() => verDetalleFactura(historialCompras[0].factura_id)}
                        >
                          Ver Factura
                        </Button>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              )}
              
              <TableContainer>
                <Table sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Fecha</strong></TableCell>
                      <TableCell><strong>Factura</strong></TableCell>
                      <TableCell><strong>Cantidad</strong></TableCell>
                      <TableCell align="right"><strong>Precio Unit.</strong></TableCell>
                      <TableCell align="right"><strong>Total</strong></TableCell>
                      <TableCell align="center"><strong>Acciones</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {historialCompras.length > 0 ? (
                      historialCompras.map((compra) => (
                        <TableRow key={compra.id} hover>
                          <TableCell>{moment(compra.fecha).format('DD/MM/YYYY')}</TableCell>
                          <TableCell>{compra.numero || `#${compra.id}`}</TableCell>
                          <TableCell>{parseFloat(compra.cantidad || 0).toFixed(2)}</TableCell>
                          <TableCell align="right">${parseFloat(compra.precio_unitario || 0).toFixed(2)}</TableCell>
                          <TableCell align="right">${parseFloat(compra.total || 0).toFixed(2)}</TableCell>
                          <TableCell align="center">
                            <Button
                              variant="text"
                              size="small"
                              color="primary"
                              onClick={() => verDetalleFactura(compra.factura_id)}
                              startIcon={<DescriptionIcon />}
                            >
                              Ver
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          No hay registros de compra para este producto
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default BusquedaProductoHistorial; 
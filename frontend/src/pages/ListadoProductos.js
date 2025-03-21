import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  InputAdornment,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  Button,
  ButtonGroup,
  Menu,
  MenuItem,
  Tooltip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InventoryIcon from '@mui/icons-material/Inventory';
import CurrencyExchangeIcon from '@mui/icons-material/CurrencyExchange';
import InfoIcon from '@mui/icons-material/Info';
import UpdateIcon from '@mui/icons-material/Update';
import LoyaltyIcon from '@mui/icons-material/Loyalty';
import ReceiptIcon from '@mui/icons-material/Receipt';
import CalculateIcon from '@mui/icons-material/Calculate';
import { fetchProductos } from '../store/productosSlice';
import { fetchTasasCambio, fetchLatestTasa, createTasaCambio } from '../store/tasasCambioSlice';

const ListadoProductos = () => {
  const dispatch = useDispatch();
  const { items: productos, status } = useSelector((state) => state.productos);
  const { items: tasasCambio } = useSelector((state) => state.tasasCambio);
  
  // Estados para paginación
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  
  // Estado para tasas de cambio
  const [tasaBCV, setTasaBCV] = useState(null);
  const [tasaParalelo, setTasaParalelo] = useState(null);
  const [tasaSeleccionadaProducto, setTasaSeleccionadaProducto] = useState({});
  
  // Estado para diálogo informativo
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  
  // Estado para feedback
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // Cargar productos y tasas al montar el componente
  useEffect(() => {
    if (status !== 'succeeded') {
      dispatch(fetchProductos());
    }
    dispatch(fetchTasasCambio());
    dispatch(fetchLatestTasa('BCV')).then(action => {
      if (action.payload) {
        setTasaBCV(action.payload);
      }
    });
    dispatch(fetchLatestTasa('PARALELO')).then(action => {
      if (action.payload) {
        setTasaParalelo(action.payload);
      }
    });
  }, [dispatch, status]);
  
  // Inicializar tasas seleccionadas para cada producto
  useEffect(() => {
    if (productos.length > 0 && tasaParalelo) {
      const initialTasas = {};
      productos.forEach(producto => {
        initialTasas[producto.id] = 'PARALELO';
      });
      setTasaSeleccionadaProducto(initialTasas);
    }
  }, [productos, tasaParalelo]);
  
  // Filtrar productos cuando cambia el término de búsqueda o la lista de productos
  useEffect(() => {
    if (productos.length > 0) {
      if (searchTerm.trim() === '') {
        setProductosFiltrados(productos);
      } else {
        const filtered = productos.filter(producto => 
          producto.nombre.toLowerCase().includes(searchTerm.toLowerCase())
        );
        setProductosFiltrados(filtered);
      }
      setPage(0); // Resetear a la primera página cuando cambia el filtro
    }
  }, [searchTerm, productos]);
  
  // Manejadores para la paginación
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Función para cambiar la tasa de un producto
  const cambiarTasaProducto = (productoId, tipoTasa) => {
    setTasaSeleccionadaProducto({
      ...tasaSeleccionadaProducto,
      [productoId]: tipoTasa
    });
  };
  
  // Función para calcular el precio en USD desde BS
  const calcularPrecioUSD = (precioBs, productoId) => {
    if (!precioBs) return 0;
    
    // Convertir a número
    precioBs = Number(precioBs);
    
    // Obtener la tasa seleccionada para este producto
    const tipoTasa = tasaSeleccionadaProducto[productoId] || 'PARALELO';
    const tasa = tipoTasa === 'BCV' ? tasaBCV : tasaParalelo;
    
    if (!tasa || tasa.valor <= 0) return 0;
    
    // Calcular y devolver con 2 decimales
    return Number((precioBs / tasa.valor).toFixed(2));
  };
  
  // Obtener el valor actual de la tasa según el tipo
  const obtenerValorTasa = (tipo) => {
    if (tipo === 'BCV' && tasaBCV) {
      return tasaBCV.valor;
    } else if (tipo === 'PARALELO' && tasaParalelo) {
      return tasaParalelo.valor;
    }
    return 'N/A';
  };
  
  // Abrir el diálogo informativo
  const abrirInfoDialog = () => {
    setInfoDialogOpen(true);
  };
  
  // Cerrar el diálogo informativo
  const cerrarInfoDialog = () => {
    setInfoDialogOpen(false);
  };
  
  // Obtener el ícono para la fuente de actualización
  const getFuenteActualizacionIcon = (fuente) => {
    switch (fuente) {
      case 'loyverse':
        return <LoyaltyIcon fontSize="small" sx={{ color: '#3b82f6' }} />;
      case 'factura':
        return <ReceiptIcon fontSize="small" sx={{ color: '#10b981' }} />;
      case 'calculado':
        return <CalculateIcon fontSize="small" sx={{ color: '#f59e0b' }} />;
      default:
        return <UpdateIcon fontSize="small" sx={{ color: '#6b7280' }} />;
    }
  };
  
  // Obtener el texto para la fuente de actualización
  const getFuenteActualizacionText = (fuente) => {
    switch (fuente) {
      case 'loyverse':
        return 'Loyverse API';
      case 'factura':
        return 'Factura';
      case 'calculado':
        return 'Cálculo automático';
      default:
        return 'Desconocida';
    }
  };
  
  // Formatear fecha
  const formatDate = (dateString) => {
    if (!dateString) return 'No disponible';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  // Productos para la página actual
  const productosEnPagina = productosFiltrados.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  
  // Cerrar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };
  
  return (
    <Box sx={{ 
      maxWidth: 1200, 
      margin: '0 auto', 
      padding: 3, 
      backgroundColor: '#f8f9fa'
    }}>
      <Typography 
        variant="h4" 
        gutterBottom 
        sx={{ 
          fontSize: '2rem', 
          fontWeight: 600, 
          color: '#1e293b',
          mb: 4,
          borderBottom: '2px solid #e2e8f0',
          paddingBottom: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2
        }}
      >
        <InventoryIcon fontSize="large" />
        Inventario de Productos
        <Tooltip title="Información sobre tasas de cambio">
          <IconButton 
            onClick={abrirInfoDialog}
            size="small"
            sx={{ ml: 2 }}
          >
            <InfoIcon />
          </IconButton>
        </Tooltip>
      </Typography>
      
      {/* Panel de estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Total Productos
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {productos.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Tasa BCV Actual
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {tasaBCV ? tasaBCV.valor : 'N/A'} Bs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Tasa Paralelo Actual
              </Typography>
              <Typography variant="h3" component="div" color="secondary">
                {tasaParalelo ? tasaParalelo.valor : 'N/A'} Bs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Resultados búsqueda
              </Typography>
              <Typography variant="h3" component="div" color={searchTerm ? 'secondary' : 'primary'}>
                {productosFiltrados.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Buscador */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          backgroundColor: '#fff'
        }}
      >
        <TextField
          fullWidth
          label="Buscar Productos"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Escribe el nombre del producto..."
          variant="outlined"
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            sx: {
              borderRadius: 1
            }
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: '#cbd5e1',
              },
              '&:hover fieldset': {
                borderColor: '#94a3b8',
              }
            }
          }}
        />
      </Paper>
      
      {/* Tabla de productos */}
      <Paper 
        elevation={3} 
        sx={{ 
          borderRadius: 2,
          overflow: 'hidden'
        }}
      >
        {status === 'loading' ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TableContainer sx={{ maxHeight: 'calc(100vh - 350px)' }}>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Producto</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Código</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Precio USD</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Precio BS</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Tasa</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Categoría</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Stock</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Actualización</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {productosEnPagina.map((producto) => (
                    <TableRow 
                      key={producto.id}
                      sx={{
                        '&:hover': {
                          backgroundColor: '#f8fafc',
                        },
                        '&:nth-of-type(even)': {
                          backgroundColor: '#f9fafb',
                        },
                        transition: 'background-color 0.2s'
                      }}
                    >
                      <TableCell 
                        component="th" 
                        scope="row"
                        sx={{ 
                          color: '#334155', 
                          borderBottom: '1px solid #f1f5f9',
                          fontWeight: 500
                        }}
                      >
                        {producto.nombre}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.codigo || 'N/A'}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        ${calcularPrecioUSD(producto.precio_base, producto.id)}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9', fontWeight: 500 }}
                      >
                        {Number(producto.precio_base).toFixed(2)} Bs
                      </TableCell>
                      <TableCell
                        align="center"
                        sx={{ borderBottom: '1px solid #f1f5f9' }}
                      >
                        <ButtonGroup size="small" variant="outlined">
                          <Button 
                            color={tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'primary' : 'inherit'}
                            onClick={() => cambiarTasaProducto(producto.id, 'BCV')}
                            sx={{ 
                              borderRadius: '4px 0 0 4px',
                              fontWeight: tasaSeleccionadaProducto[producto.id] === 'BCV' ? 700 : 400,
                              backgroundColor: tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'rgba(25, 118, 210, 0.1)' : 'transparent'
                            }}
                          >
                            BCV
                          </Button>
                          <Button 
                            color={tasaSeleccionadaProducto[producto.id] === 'PARALELO' ? 'secondary' : 'inherit'}
                            onClick={() => cambiarTasaProducto(producto.id, 'PARALELO')}
                            sx={{ 
                              borderRadius: '0 4px 4px 0',
                              fontWeight: tasaSeleccionadaProducto[producto.id] === 'PARALELO' ? 700 : 400,
                              backgroundColor: tasaSeleccionadaProducto[producto.id] === 'PARALELO' ? 'rgba(220, 0, 78, 0.1)' : 'transparent'
                            }}
                          >
                            Paralelo
                          </Button>
                        </ButtonGroup>
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.categoria ? (
                          <Chip 
                            label={producto.categoria} 
                            size="small" 
                            sx={{ 
                              backgroundColor: '#e0f2fe',
                              color: '#0369a1',
                              fontWeight: 500
                            }} 
                          />
                        ) : 'Sin categoría'}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Chip 
                          label={producto.stock_actual || '0'} 
                          size="small"
                          color={producto.stock_actual > 10 ? 'success' : producto.stock_actual > 0 ? 'warning' : 'error'}
                          sx={{ fontWeight: 600 }}
                        />
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Tooltip 
                          title={
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                Fuente: {getFuenteActualizacionText(producto.fuente_actualizacion)}
                              </Typography>
                              <Typography variant="body2">
                                Fecha: {formatDate(producto.ultima_actualizacion_precio)}
                              </Typography>
                            </Box>
                          } 
                          arrow
                        >
                          <Box sx={{ display: 'inline-flex', alignItems: 'center' }}>
                            {getFuenteActualizacionIcon(producto.fuente_actualizacion)}
                          </Box>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                  {productosEnPagina.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={8} align="center" sx={{ py: 4, color: '#6b7280' }}>
                        {searchTerm 
                          ? 'No se encontraron productos con ese término de búsqueda' 
                          : 'No hay productos disponibles'}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            
            <Divider />
            
            <TablePagination
              rowsPerPageOptions={[5, 10, 25, 50, 100]}
              component="div"
              count={productosFiltrados.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              labelRowsPerPage="Filas por página:"
              labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
              sx={{
                backgroundColor: '#f8fafc',
                borderTop: '1px solid #e2e8f0',
                '& .MuiToolbar-root': {
                  minHeight: '56px',
                },
                '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                  color: '#64748b',
                }
              }}
            />
          </>
        )}
      </Paper>
      
      {/* Diálogo informativo */}
      <Dialog
        open={infoDialogOpen}
        onClose={cerrarInfoDialog}
        maxWidth="md"
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CurrencyExchangeIcon color="primary" />
            <Typography variant="h6">Información sobre Tasas de Cambio</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Tasas de cambio actuales:
            </Typography>
            <Box sx={{ display: 'flex', gap: 4, mb: 2 }}>
              <Box>
                <Typography variant="body1" color="primary" sx={{ fontWeight: 500 }}>
                  BCV: {tasaBCV ? tasaBCV.valor : 'No disponible'} Bs/USD
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Última actualización: {tasaBCV ? new Date(tasaBCV.fecha).toLocaleDateString() : 'N/A'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body1" color="secondary" sx={{ fontWeight: 500 }}>
                  Paralelo: {tasaParalelo ? tasaParalelo.valor : 'No disponible'} Bs/USD
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Última actualización: {tasaParalelo ? new Date(tasaParalelo.fecha).toLocaleDateString() : 'N/A'}
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="body1" gutterBottom>
              Los precios en USD son calculados a partir de los precios en Bolívares usando la tasa seleccionada para cada producto.
            </Typography>
            <Typography variant="body1" gutterBottom>
              Puede cambiar la tasa utilizada para cada producto haciendo clic en los botones "BCV" o "Paralelo" en la columna "Tasa".
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Fuentes de actualización:
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LoyaltyIcon sx={{ color: '#3b82f6' }} />
                <Typography variant="body1">
                  <strong>Loyverse API:</strong> Productos actualizados directamente desde la API de Loyverse.
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ReceiptIcon sx={{ color: '#10b981' }} />
                <Typography variant="body1">
                  <strong>Factura:</strong> Productos actualizados a través de la creación de facturas.
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CalculateIcon sx={{ color: '#f59e0b' }} />
                <Typography variant="body1">
                  <strong>Cálculo automático:</strong> Precios calculados automáticamente basados en porcentajes de ganancia.
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary', fontStyle: 'italic' }}>
              Nota: Los cambios en la selección de tasa se utilizan solo para visualización y no afectan los datos guardados.
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarInfoDialog} color="primary" variant="contained">
            Entendido
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar para notificaciones */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ListadoProductos; 
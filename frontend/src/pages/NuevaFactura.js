import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import axios from 'axios';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { fetchProductos } from '../store/productosSlice';
import { fetchLatestTasa } from '../store/tasasCambioSlice';
import { createFactura } from '../store/facturasSlice';

// Usar la misma URL base que en el resto de la aplicación
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const NuevaFactura = () => {
  const dispatch = useDispatch();
  const productos = useSelector((state) => state.productos.items);
  const tasaCambio = useSelector((state) => state.tasasCambio.latestTasa);
  
  const [moneda, setMoneda] = useState('');
  const [tipoTasa, setTipoTasa] = useState('');
  const [productoSearch, setProductoSearch] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  const [productosSeleccionados, setProductosSeleccionados] = useState([]);
  const [cantidad, setCantidad] = useState(1);
  const [showResults, setShowResults] = useState(false);
  
  // Nuevos estados para manejo de porcentaje de ganancia
  const [porcentajeGanancia, setPorcentajeGanancia] = useState(30);
  const [actualizarPrecios, setActualizarPrecios] = useState(true);
  const [editingProductIndex, setEditingProductIndex] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [productoEditando, setProductoEditando] = useState({
    porcentajeGanancia: null,
    cantidad: 0,
    aplicarIva: false
  });
  
  // Estado para feedback al usuario
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');

  useEffect(() => {
    console.log('Iniciando carga de productos...');
    dispatch(fetchProductos());
  }, [dispatch]);

  useEffect(() => {
    if (tipoTasa) {
      dispatch(fetchLatestTasa(tipoTasa));
    }
  }, [dispatch, tipoTasa]);

  // Filtrar productos basado en la búsqueda
  useEffect(() => {
    if (productoSearch.length > 0) {
      const searchTerm = productoSearch.toLowerCase();
      console.log('Término de búsqueda:', searchTerm);
      console.log('Productos disponibles:', productos);
      const filtrados = productos.filter(p =>
        p.nombre.toLowerCase().includes(searchTerm)
      ).slice(0, 10);
      console.log('Productos filtrados:', filtrados);
      setProductosFiltrados(filtrados);
      setShowResults(true);
    } else {
      setProductosFiltrados([]);
      setShowResults(false);
    }
  }, [productoSearch, productos]);

  const handleMonedaChange = (event) => {
    setMoneda(event.target.value);
    if (event.target.value === 'BS') {
      setTipoTasa('BCV');
    } else {
      setTipoTasa('');
    }
  };

  const handleProductoSelect = (producto) => {
    setDialogOpen(true);
    setProductoEditando({
      producto: producto,
      cantidad: cantidad,
      precio_compra_usd: 0,
      unidades_paquete: 1,
      porcentajeGanancia: porcentajeGanancia,
      aplicarIva: false
    });
  };

  const handleRemoveProducto = (index) => {
    setProductosSeleccionados(productosSeleccionados.filter((_, i) => i !== index));
  };

  const handleEditProducto = (index) => {
    const producto = productosSeleccionados[index];
    setProductoEditando({
      porcentajeGanancia: producto.porcentajeGanancia || porcentajeGanancia,
      cantidad: producto.cantidad,
      aplicarIva: producto.aplicarIva || false
    });
    setEditingProductIndex(index);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingProductIndex(null);
  };

  const calcularPrecioVenta = (precio_compra_usd, unidades_paquete, tasa_cambio_valor, porcentaje, aplicarIva = false) => {
    if (!precio_compra_usd || !unidades_paquete || !tasa_cambio_valor) return 0;
    
    // Aplicar la fórmula: (precio_compra × tasa_dolar_paralelo / unidades) × (1 + porcentaje_ganancia/100)
    const precio_base = (precio_compra_usd * tasa_cambio_valor) / unidades_paquete;
    const precio_con_ganancia = precio_base * (1 + (porcentaje / 100));
    
    // Aplicar IVA si está activado
    const precio_final = aplicarIva ? precio_con_ganancia * 1.16 : precio_con_ganancia;
    
    // Redondear a 2 decimales para evitar problemas de precisión
    return parseFloat(precio_final.toFixed(2));
  };

  const handleSaveProductEdit = () => {
    if (!productoEditando.precio_compra_usd || !productoEditando.unidades_paquete) {
      setSnackbarMessage('Por favor ingrese el precio de compra y las unidades por paquete');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }

    const precio_venta = calcularPrecioVenta(
      productoEditando.precio_compra_usd,
      productoEditando.unidades_paquete,
      tasaCambio?.valor || 1,
      productoEditando.porcentajeGanancia,
      productoEditando.aplicarIva
    );

    const nuevoProducto = {
      producto: productoEditando.producto,
      cantidad: productoEditando.cantidad,
      precio_compra_usd: productoEditando.precio_compra_usd,
      unidades_paquete: productoEditando.unidades_paquete,
      precio_unitario: precio_venta,
      total: precio_venta * productoEditando.cantidad,
      porcentajeGanancia: productoEditando.porcentajeGanancia,
      aplicarIva: productoEditando.aplicarIva
    };

    if (editingProductIndex !== null) {
      const updatedProductos = [...productosSeleccionados];
      updatedProductos[editingProductIndex] = nuevoProducto;
      setProductosSeleccionados(updatedProductos);
    } else {
      setProductosSeleccionados([...productosSeleccionados, nuevoProducto]);
    }
    
    setDialogOpen(false);
    setEditingProductIndex(null);
    setProductoSearch('');
    setCantidad(1);
  };

  const calcularTotal = () => {
    return productosSeleccionados.reduce((sum, item) => sum + item.total, 0);
  };

  const handleSubmit = () => {
    const facturaData = {
      moneda: moneda,
      tasa_cambio: tasaCambio?.id,
      porcentaje_ganancia: porcentajeGanancia,
      detalles: productosSeleccionados.map(item => ({
        producto: item.producto.id,
        cantidad: item.cantidad,
        precio_unitario: parseFloat(item.precio_unitario.toFixed(2)),
        porcentaje_ganancia: item.porcentajeGanancia || porcentajeGanancia,
        precio_compra_usd: parseFloat(item.precio_compra_usd.toFixed(2)),
        unidades_paquete: item.unidades_paquete,
        total: parseFloat((item.precio_unitario * item.cantidad).toFixed(2)),
        aplicarIva: item.aplicarIva || false
      }))
    };

    console.log('Enviando datos de factura:', facturaData); // Para depuración
    
    dispatch(createFactura(facturaData))
      .then(response => {
        // Mostrar mensaje de factura creada
        setSnackbarMessage('Factura creada correctamente');
        setSnackbarSeverity('success');
        setSnackbarOpen(true);
        
        // Si está habilitada la opción de actualizar precios, procesamos la factura
        if (actualizarPrecios && response.payload && response.payload.id) {
          // Realizar la llamada al endpoint para procesar la factura usando axios
          axios.post(`${API_URL}/facturas/${response.payload.id}/procesar_factura/`)
            .then(res => {
              console.log('Precios actualizados:', res.data);
              // Mostrar mensaje de éxito
              setSnackbarMessage('Precios actualizados en Loyverse correctamente');
              setSnackbarSeverity('success');
              setSnackbarOpen(true);
              
              // Limpiar el formulario
              setProductosSeleccionados([]);
            })
            .catch(error => {
              console.error('Error al actualizar precios:', error);
              // Mostrar mensaje de error
              setSnackbarMessage('Error al actualizar precios: ' + (error.response?.data?.error || error.message));
              setSnackbarSeverity('error');
              setSnackbarOpen(true);
            });
        } else {
          // Limpiar el formulario si no se van a actualizar precios
          setProductosSeleccionados([]);
        }
      })
      .catch(error => {
        console.error('Error al crear factura:', error);
        setSnackbarMessage('Error al crear factura: ' + (error.response?.data?.error || error.message));
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      });
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Nueva Factura
      </Typography>
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Moneda</InputLabel>
              <Select value={moneda} onChange={handleMonedaChange}>
                <MenuItem value="USD">Dólares (USD)</MenuItem>
                <MenuItem value="BS">Bolívares (BS)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {moneda === 'BS' && (
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Tasa</InputLabel>
                <Select value={tipoTasa} onChange={(e) => setTipoTasa(e.target.value)}>
                  <MenuItem value="BCV">Tasa BCV</MenuItem>
                  <MenuItem value="PARALELO">Tasa Paralelo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
          
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Porcentaje de Ganancia"
              type="number"
              value={porcentajeGanancia}
              onChange={(e) => setPorcentajeGanancia(Number(e.target.value))}
              inputProps={{ min: 0, max: 100, step: 1 }}
              helperText="Porcentaje global de ganancia"
            />
          </Grid>
        </Grid>
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={actualizarPrecios}
                  onChange={(e) => setActualizarPrecios(e.target.checked)}
                />
              }
              label="Actualizar precios en Loyverse automáticamente"
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={8}>
            <TextField
              fullWidth
              label="Buscar Producto"
              value={productoSearch}
              onChange={(e) => setProductoSearch(e.target.value)}
              placeholder="Escribe para buscar productos..."
            />
            {showResults && productosFiltrados.length > 0 && (
              <Paper 
                sx={{ 
                  mt: 1, 
                  maxHeight: 300, 
                  overflow: 'auto',
                  position: 'absolute',
                  zIndex: 1000,
                  width: '95%',
                  boxShadow: 3
                }}
              >
                <List>
                  {productosFiltrados.map(producto => (
                    <ListItem 
                      key={producto.id} 
                      button 
                      onClick={() => handleProductoSelect(producto)}
                      sx={{
                        '&:hover': {
                          backgroundColor: 'rgba(0, 0, 0, 0.04)',
                        },
                      }}
                    >
                      <ListItemText
                        primary={producto.nombre}
                        secondary={`Precio: $${Number(producto.precio_base).toFixed(2)}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </Paper>
            )}
          </Grid>
          <Grid item xs={4}>
            <TextField
              fullWidth
              type="number"
              label="Cantidad"
              value={cantidad}
              onChange={(e) => setCantidad(Number(e.target.value))}
              inputProps={{ min: 1 }}
            />
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Producto</TableCell>
              <TableCell align="right">Cantidad</TableCell>
              <TableCell align="right">Precio Unitario</TableCell>
              <TableCell align="right">Total</TableCell>
              <TableCell align="right">% Ganancia</TableCell>
              <TableCell align="center">IVA</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {productosSeleccionados.map((item, index) => (
              <TableRow key={index}>
                <TableCell>{item.producto.nombre}</TableCell>
                <TableCell align="right">{item.cantidad}</TableCell>
                <TableCell align="right">
                  {item.precio_unitario.toFixed(2)} {moneda}
                </TableCell>
                <TableCell align="right">
                  {item.total.toFixed(2)} {moneda}
                </TableCell>
                <TableCell align="right">
                  {item.porcentajeGanancia !== null ? `${item.porcentajeGanancia}%` : `${porcentajeGanancia}% (global)`}
                </TableCell>
                <TableCell align="center">
                  {item.aplicarIva ? "Sí (16%)" : "No"}
                </TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => handleEditProducto(index)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleRemoveProducto(index)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={3} align="right">
                <strong>Total:</strong>
              </TableCell>
              <TableCell align="right">
                <strong>{calcularTotal().toFixed(2)} {moneda}</strong>
              </TableCell>
              <TableCell colSpan={3} />
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={productosSeleccionados.length === 0 || !moneda}
        >
          {actualizarPrecios ? 'Guardar Factura y Actualizar Precios' : 'Guardar Factura'}
        </Button>
      </Box>
      
      {/* Diálogo para editar producto */}
      <Dialog open={dialogOpen} onClose={handleDialogClose}>
        <DialogTitle>
          {productoEditando.producto ? productoEditando.producto.nombre : 'Editar Producto'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Precio de Compra (USD)"
                type="number"
                value={productoEditando.precio_compra_usd}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  precio_compra_usd: Number(e.target.value)
                })}
                inputProps={{ min: 0, step: 0.01 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Unidades por Paquete"
                type="number"
                value={productoEditando.unidades_paquete}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  unidades_paquete: Number(e.target.value)
                })}
                inputProps={{ min: 1 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Cantidad a Facturar"
                type="number"
                value={productoEditando.cantidad}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  cantidad: Number(e.target.value)
                })}
                inputProps={{ min: 1 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Porcentaje de Ganancia"
                type="number"
                value={productoEditando.porcentajeGanancia}
                onChange={(e) => setProductoEditando({
                  ...productoEditando,
                  porcentajeGanancia: Number(e.target.value)
                })}
                inputProps={{ min: 0, max: 100, step: 1 }}
                helperText="Dejar vacío para usar el porcentaje global"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={productoEditando.aplicarIva || false}
                    onChange={(e) => setProductoEditando({
                      ...productoEditando,
                      aplicarIva: e.target.checked
                    })}
                    color="primary"
                  />
                }
                label="Aplicar IVA (16%)"
              />
            </Grid>
            {tasaCambio && (
              <Grid item xs={12}>
                <Typography variant="body2" color="textSecondary">
                  Precio de venta calculado: {moneda === 'BS' ? 'BS ' : '$ '}
                  {calcularPrecioVenta(
                    productoEditando.precio_compra_usd,
                    productoEditando.unidades_paquete,
                    tasaCambio.valor,
                    productoEditando.porcentajeGanancia,
                    productoEditando.aplicarIva
                  ).toFixed(2)}
                  {productoEditando.aplicarIva && ' (incluye IVA 16%)'}
                </Typography>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>Cancelar</Button>
          <Button onClick={handleSaveProductEdit} color="primary">
            Guardar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar para feedback */}
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={6000} 
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default NuevaFactura; 
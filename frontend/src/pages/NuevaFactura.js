import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
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
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { fetchProductos } from '../store/productosSlice';
import { fetchLatestTasa } from '../store/tasasCambioSlice';
import { createFactura } from '../store/facturasSlice';

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
    const precioBase = Number(producto.precio_base);
    const precio = moneda === 'BS' && tasaCambio
      ? precioBase * tasaCambio.valor
      : precioBase;

    setProductosSeleccionados([
      ...productosSeleccionados,
      {
        producto: producto,
        cantidad: cantidad,
        precio_unitario: precio,
        total: precio * cantidad
      }
    ]);
    setProductoSearch('');
    setCantidad(1);
    setShowResults(false);
  };

  const handleRemoveProducto = (index) => {
    setProductosSeleccionados(productosSeleccionados.filter((_, i) => i !== index));
  };

  const calcularTotal = () => {
    return productosSeleccionados.reduce((sum, item) => sum + item.total, 0);
  };

  const handleSubmit = () => {
    const facturaData = {
      moneda: moneda,
      tasa_cambio: tasaCambio?.id,
      detalles: productosSeleccionados.map(item => ({
        producto: item.producto.id,
        cantidad: item.cantidad,
        precio_unitario: item.precio_unitario
      }))
    };
    dispatch(createFactura(facturaData));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Nueva Factura
      </Typography>
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Moneda</InputLabel>
              <Select value={moneda} onChange={handleMonedaChange}>
                <MenuItem value="USD">Dólares (USD)</MenuItem>
                <MenuItem value="BS">Bolívares (BS)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {moneda === 'BS' && (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Tasa</InputLabel>
                <Select value={tipoTasa} onChange={(e) => setTipoTasa(e.target.value)}>
                  <MenuItem value="BCV">Tasa BCV</MenuItem>
                  <MenuItem value="PARALELO">Tasa Paralelo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
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
              <TableCell />
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
          Guardar Factura
        </Button>
      </Box>
    </Box>
  );
};

export default NuevaFactura; 
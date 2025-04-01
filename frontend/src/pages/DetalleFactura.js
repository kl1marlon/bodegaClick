import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFacturaDetalle, sincronizarFactura, actualizarProductoFactura } from '../store/facturasSlice';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  IconButton,
  Divider,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Tooltip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Sync as SyncIcon,
  GetApp as ExportIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts';
import moment from 'moment';
import 'moment/locale/es';

moment.locale('es');

const DetalleFactura = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { detalleActual: factura, status, error } = useSelector((state) => state.facturas);
  
  const [modoEdicion, setModoEdicion] = useState(false);
  const [dialogoSincronizacion, setDialogoSincronizacion] = useState(false);
  
  // Valores calculados
  const [resumenFinanciero, setResumenFinanciero] = useState({
    subtotal: 0,
    iva: 0,
    totalMonedaOriginal: 0,
    conversionUSD: 0,
    conversionBS: 0,
    valorEstimadoVenta: 0,
    gananciaProyectada: 0,
    porcentajeGananciaPromedio: 0
  });
  
  // Datos para gráfico
  const [datosCategoria, setDatosCategoria] = useState([]);
  
  useEffect(() => {
    if (id) {
      dispatch(fetchFacturaDetalle(id));
    }
  }, [id, dispatch]);
  
  useEffect(() => {
    if (factura && factura.detalles) {
      calcularResumenFinanciero();
      prepararDatosGrafico();
    }
  }, [factura]);
  
  const calcularResumenFinanciero = () => {
    if (!factura || !factura.detalles) return;
    
    const subtotal = factura.detalles.reduce((sum, detalle) => sum + detalle.total, 0);
    const detallesConIva = factura.detalles.filter(d => d.aplicarIva);
    const iva = detallesConIva.reduce((sum, detalle) => sum + (detalle.total * 0.16), 0);
    
    const totalMonedaOriginal = subtotal + iva;
    
    // Preparamos valores de conversión según la moneda original
    let conversionUSD = factura.total_usd;
    let conversionBS = factura.total_bs;
    
    // Cálculo de valor estimado de venta y ganancia
    const valorEstimadoVenta = factura.detalles.reduce((sum, detalle) => {
      const precioVenta = detalle.precio_base_usd || (detalle.precio_compra_usd * (1 + detalle.porcentaje_ganancia / 100));
      return sum + (precioVenta * detalle.cantidad * detalle.unidades_paquete);
    }, 0);
    
    const gananciaProyectada = valorEstimadoVenta - conversionUSD;
    
    // Porcentaje promedio de ganancia
    const porcentajeGananciaPromedio = factura.detalles.reduce((sum, detalle) => sum + (detalle.porcentaje_ganancia || 0), 0) / factura.detalles.length;
    
    setResumenFinanciero({
      subtotal,
      iva,
      totalMonedaOriginal,
      conversionUSD,
      conversionBS,
      valorEstimadoVenta,
      gananciaProyectada,
      porcentajeGananciaPromedio
    });
  };
  
  const prepararDatosGrafico = () => {
    if (!factura || !factura.detalles) return;
    
    // Agrupamos por categoría
    const categorias = factura.detalles.reduce((acc, detalle) => {
      const categoria = detalle.producto?.categoria || 'Sin categoría';
      if (!acc[categoria]) {
        acc[categoria] = {
          nombre: categoria,
          total: 0,
          cantidad: 0
        };
      }
      acc[categoria].total += detalle.total;
      acc[categoria].cantidad += detalle.cantidad;
      return acc;
    }, {});
    
    const datos = Object.values(categorias);
    setDatosCategoria(datos);
  };
  
  const handleEditarClick = () => {
    setModoEdicion(true);
  };
  
  const handleGuardarClick = () => {
    setModoEdicion(false);
    // Aquí implementaríamos la lógica para guardar cambios
  };
  
  const handleSincronizarClick = () => {
    setDialogoSincronizacion(true);
  };
  
  const confirmarSincronizacion = () => {
    dispatch(sincronizarFactura(id));
    setDialogoSincronizacion(false);
  };
  
  const handleExportarClick = (formato = 'pdf') => {
    // Implementar lógica de exportación
    console.log(`Exportando factura ${id} en formato ${formato}`);
  };
  
  const handleProductoChange = (productoId, campo, valor) => {
    dispatch(actualizarProductoFactura({
      facturaId: id,
      productoId,
      campo,
      valor
    }));
  };
  
  const formatoMoneda = (valor, moneda = 'USD') => {
    return moneda === 'USD' 
      ? `$${valor.toFixed(2)}` 
      : `Bs ${valor.toFixed(2)}`;
  };
  
  if (status === 'loading') {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }
  
  if (status === 'failed') {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography color="error" variant="h6">
          Error al cargar los detalles de la factura: {error}
        </Typography>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/facturas')}
          sx={{ mt: 2 }}
        >
          Volver al listado
        </Button>
      </Container>
    );
  }
  
  if (!factura) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h6">
          No se encontró la factura solicitada
        </Typography>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/facturas')}
          sx={{ mt: 2 }}
        >
          Volver al listado
        </Button>
      </Container>
    );
  }
  
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A569BD', '#5DADE2', '#48C9B0', '#F4D03F'];
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      {/* Botón de volver */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/facturas')}
        sx={{ mb: 3 }}
      >
        Volver al listado
      </Button>
      
      {/* Encabezado de Factura */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={2}>
          {/* Información principal */}
          <Grid item xs={12} md={8}>
            <Typography variant="h4" gutterBottom>
              Factura #{factura.numero}
            </Typography>
            <Typography variant="subtitle1" color="textSecondary">
              Fecha: {moment(factura.fecha).format('DD/MM/YYYY HH:mm')}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              <Typography variant="body1" sx={{ mr: 2 }}>
                <strong>Moneda:</strong> {factura.moneda === 'USD' ? 'Dólares' : 'Bolívares'}
              </Typography>
              <Typography variant="body1">
                <strong>Tasa de cambio:</strong> {factura.tasa_cambio?.valor || 'N/A'} 
                ({factura.tasa_cambio?.tipo || 'N/A'})
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mt: 1 }}>
              <strong>% Ganancia General:</strong> {factura.porcentaje_ganancia}%
            </Typography>
          </Grid>
          
          {/* Totales destacados */}
          <Grid item xs={12} md={4} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <Typography variant="h5" sx={{ mb: 1 }}>
              Total USD: {formatoMoneda(factura.total_usd)}
            </Typography>
            <Typography variant="h6" sx={{ mb: 1 }}>
              Total Bs: {formatoMoneda(factura.total_bs, 'BS')}
            </Typography>
            <Chip 
              label={factura.sincronizado_loyverse ? 'SINCRONIZADO' : 'PENDIENTE DE SINCRONIZACIÓN'}
              color={factura.sincronizado_loyverse ? 'success' : 'warning'}
              sx={{ mt: 1 }}
            />
          </Grid>
          
          {/* Acciones */}
          <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            {modoEdicion ? (
              <Button
                variant="contained"
                color="primary"
                startIcon={<SaveIcon />}
                onClick={handleGuardarClick}
                sx={{ ml: 1 }}
              >
                Guardar Cambios
              </Button>
            ) : (
              <>
                <Button
                  variant="outlined"
                  startIcon={<EditIcon />}
                  onClick={handleEditarClick}
                >
                  Editar
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<SyncIcon />}
                  onClick={handleSincronizarClick}
                  disabled={factura.sincronizado_loyverse}
                  sx={{ ml: 1 }}
                >
                  Sincronizar
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ExportIcon />}
                  onClick={() => handleExportarClick('pdf')}
                  sx={{ ml: 1 }}
                >
                  Exportar
                </Button>
              </>
            )}
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabla de productos */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Productos
        </Typography>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Producto</strong></TableCell>
                <TableCell><strong>Cantidad</strong></TableCell>
                <TableCell><strong>Unidades/Paquete</strong></TableCell>
                <TableCell><strong>Precio Unitario</strong></TableCell>
                <TableCell><strong>Total</strong></TableCell>
                <TableCell><strong>Precio USD</strong></TableCell>
                <TableCell><strong>% Ganancia</strong></TableCell>
                <TableCell><strong>Precio Venta</strong></TableCell>
                <TableCell><strong>IVA</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {factura.detalles && factura.detalles.map((detalle) => (
                <TableRow key={detalle.id} hover>
                  <TableCell>{detalle.producto?.nombre || 'Producto no encontrado'}</TableCell>
                  <TableCell>
                    {modoEdicion ? (
                      <TextField
                        type="number"
                        value={detalle.cantidad}
                        onChange={(e) => handleProductoChange(detalle.id, 'cantidad', e.target.value)}
                        size="small"
                        variant="outlined"
                        sx={{ width: '80px' }}
                      />
                    ) : (
                      detalle.cantidad
                    )}
                  </TableCell>
                  <TableCell>{detalle.unidades_paquete}</TableCell>
                  <TableCell>{formatoMoneda(detalle.precio_unitario, factura.moneda)}</TableCell>
                  <TableCell>{formatoMoneda(detalle.total, factura.moneda)}</TableCell>
                  <TableCell>{formatoMoneda(detalle.precio_compra_usd)}</TableCell>
                  <TableCell>
                    {modoEdicion ? (
                      <TextField
                        type="number"
                        value={detalle.porcentaje_ganancia}
                        onChange={(e) => handleProductoChange(detalle.id, 'porcentaje_ganancia', e.target.value)}
                        size="small"
                        variant="outlined"
                        InputProps={{
                          endAdornment: <InputAdornment position="end">%</InputAdornment>,
                        }}
                        sx={{ width: '100px' }}
                      />
                    ) : (
                      `${detalle.porcentaje_ganancia}%`
                    )}
                  </TableCell>
                  <TableCell>
                    {formatoMoneda(detalle.precio_base_usd || (detalle.precio_compra_usd * (1 + detalle.porcentaje_ganancia / 100)))}
                    {detalle.precio_base_usd ? (
                      <Tooltip title="Precio de venta ya establecido">
                        <CheckIcon fontSize="small" color="success" sx={{ ml: 1 }} />
                      </Tooltip>
                    ) : (
                      <Tooltip title="Precio calculado en base al % de ganancia">
                        <InfoIcon fontSize="small" color="info" sx={{ ml: 1 }} />
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell>
                    {detalle.aplicarIva ? (
                      <Chip label="Sí" size="small" color="primary" />
                    ) : (
                      <Chip label="No" size="small" variant="outlined" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {(!factura.detalles || factura.detalles.length === 0) && (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    No hay productos en esta factura
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
      
      {/* Resumen financiero y gráficos */}
      <Grid container spacing={3}>
        {/* Resumen financiero */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Resumen Financiero
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>Subtotal:</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body1" align="right">
                  {formatoMoneda(resumenFinanciero.subtotal, factura.moneda)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>IVA (16%):</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body1" align="right">
                  {formatoMoneda(resumenFinanciero.iva, factura.moneda)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>Total ({factura.moneda}):</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body1" align="right">
                  {formatoMoneda(resumenFinanciero.totalMonedaOriginal, factura.moneda)}
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>Total USD:</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body1" align="right">
                  {formatoMoneda(resumenFinanciero.conversionUSD)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>Total Bs:</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body1" align="right">
                  {formatoMoneda(resumenFinanciero.conversionBS, 'BS')}
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>Valor estimado de venta:</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body1" align="right">
                  {formatoMoneda(resumenFinanciero.valorEstimadoVenta)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>Ganancia proyectada:</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography 
                  variant="body1" 
                  align="right"
                  color={resumenFinanciero.gananciaProyectada > 0 ? "success.main" : "error.main"}
                >
                  {formatoMoneda(resumenFinanciero.gananciaProyectada)}
                </Typography>
              </Grid>
              
              <Grid item xs={6}>
                <Typography variant="body1">
                  <strong>% Ganancia promedio:</strong>
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography 
                  variant="body1" 
                  align="right"
                  color={resumenFinanciero.porcentajeGananciaPromedio < 20 ? "error.main" : 
                         resumenFinanciero.porcentajeGananciaPromedio > 40 ? "warning.main" : "success.main"}
                >
                  {resumenFinanciero.porcentajeGananciaPromedio.toFixed(2)}%
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* Gráfico por categorías */}
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h5" gutterBottom>
              Distribución por Categorías
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {datosCategoria.length > 0 ? (
              <Box sx={{ width: '100%', height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={datosCategoria}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="total"
                      nameKey="nombre"
                      label={(entry) => entry.nombre}
                    >
                      {datosCategoria.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <RechartsTooltip formatter={(value) => [`${formatoMoneda(value)}`, 'Total']} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                <Typography variant="body1" color="textSecondary">
                  No hay datos suficientes para mostrar el gráfico
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {/* Diálogo de confirmación de sincronización */}
      <Dialog
        open={dialogoSincronizacion}
        onClose={() => setDialogoSincronizacion(false)}
      >
        <DialogTitle>Sincronizar con Loyverse</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Esta acción actualizará los productos y precios en el sistema Loyverse.
            ¿Está seguro de que desea continuar?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogoSincronizacion(false)}>
            Cancelar
          </Button>
          <Button onClick={confirmarSincronizacion} variant="contained" color="primary">
            Sincronizar
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DetalleFactura; 
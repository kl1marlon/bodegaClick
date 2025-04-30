import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFacturaDetalle, sincronizarFactura } from '../store/facturasSlice';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Card,
  CardContent,
  Box,
  CircularProgress,
  IconButton,
  Tooltip,
  Alert,
  AlertTitle
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SyncIcon from '@mui/icons-material/Sync';
import GetAppIcon from '@mui/icons-material/GetApp';
import RefreshIcon from '@mui/icons-material/Refresh';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import moment from 'moment';
import 'moment/locale/es';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import { formatApiError, getSolutionSuggestion, isConnectivityError } from '../utils/errorHandler';

moment.locale('es');

// Colores para el gráfico
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const DetalleFactura = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const factura = useSelector((state) => state.facturas.detalleActual);
  const status = useSelector((state) => state.facturas.status);
  const error = useSelector((state) => state.facturas.error);
  const [sincronizando, setSincronizando] = useState(false);

  useEffect(() => {
    console.log(`Cargando detalle de factura ID: ${id}`);
    dispatch(fetchFacturaDetalle(id))
      .unwrap()
      .then(data => {
        console.log('Detalle de factura cargado exitosamente:', data);
      })
      .catch(error => {
        console.error('Error al cargar detalle de factura:', error);
      });
  }, [id, dispatch]);

  // Función para recargar los datos de la factura
  const recargarFactura = () => {
    console.log(`Recargando detalle de factura ID: ${id}`);
    dispatch(fetchFacturaDetalle(id))
      .unwrap()
      .then(data => {
        console.log('Detalle de factura recargado exitosamente:', data);
      })
      .catch(error => {
        console.error('Error al recargar detalle de factura:', error);
      });
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
    console.error('Error en estado de factura detalle:', error);
    
    // Formatear el error para mostrar información más útil
    const errorMessage = formatApiError(error, `No se pudo cargar el detalle de la factura ID: ${id}`);
    const solutionSuggestion = getSolutionSuggestion(error);
    const isConnectionError = isConnectivityError(error);
    
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <IconButton onClick={() => navigate('/facturas')} sx={{ mr: 2 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5">
            Error al cargar el detalle de factura
          </Typography>
        </Box>
        
        <Alert 
          severity="error" 
          variant="filled"
          sx={{ mb: 3 }}
          icon={<ErrorOutlineIcon fontSize="inherit" />}
        >
          <AlertTitle>Error</AlertTitle>
          {errorMessage}
        </Alert>
        
        {solutionSuggestion && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <AlertTitle>Sugerencia</AlertTitle>
            {solutionSuggestion}
          </Alert>
        )}
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button
            startIcon={<RefreshIcon />}
            variant="contained"
            color="primary"
            onClick={recargarFactura}
          >
            Reintentar
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/facturas')}
          >
            Volver al listado
          </Button>
        </Box>
      </Container>
    );
  }

  if (!factura) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography color="textSecondary" variant="h6">
          No se encontró la factura solicitada.
        </Typography>
        <Button 
          variant="contained" 
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/facturas')}
          sx={{ mt: 2 }}
        >
          Volver al listado
        </Button>
      </Container>
    );
  }

  // Calcular totales para el resumen
  const calcularResumen = () => {
    if (!factura.detalles || factura.detalles.length === 0) {
      return {
        subtotal: 0,
        iva: 0,
        total: 0,
        gananciaEstimada: 0,
        valorVenta: 0
      };
    }

    const subtotal = factura.detalles.reduce((sum, detalle) => sum + parseFloat(detalle.total || 0), 0);
    const productosConIva = factura.detalles.filter(d => d.aplicarIva);
    const iva = productosConIva.reduce((sum, detalle) => sum + (parseFloat(detalle.total || 0) * 0.16), 0);
    
    // Calcular ganancia estimada
    const gananciaEstimada = factura.detalles.reduce((sum, detalle) => {
      const porcentaje = parseFloat(detalle.porcentaje_ganancia || factura.porcentaje_ganancia || 30);
      return sum + (parseFloat(detalle.total || 0) * (porcentaje / 100));
    }, 0);

    const valorVenta = subtotal + gananciaEstimada;

    return {
      subtotal,
      iva,
      total: parseFloat(factura.total_usd || 0),
      gananciaEstimada,
      valorVenta
    };
  };

  // Preparar datos para el gráfico de distribución por categorías
  const prepararDatosGrafico = () => {
    if (!factura.detalles || factura.detalles.length === 0) {
      return [];
    }

    // Agrupar productos por categoría
    const categorias = {};
    factura.detalles.forEach(detalle => {
      const categoria = detalle.producto?.categoria || 'Sin categoría';
      if (!categorias[categoria]) {
        categorias[categoria] = 0;
      }
      categorias[categoria] += parseFloat(detalle.total || 0);
    });

    // Convertir a formato para el gráfico
    return Object.keys(categorias).map(key => ({
      name: key,
      value: categorias[key]
    }));
  };

  const resumen = calcularResumen();
  const datosGrafico = prepararDatosGrafico();

  const handleSincronizar = () => {
    setSincronizando(true);
    dispatch(sincronizarFactura(id))
      .unwrap()
      .then(result => {
        console.log('Factura sincronizada exitosamente:', result);
        // Recargar los datos de la factura para mostrar el estado actualizado
        dispatch(fetchFacturaDetalle(id));
      })
      .catch(error => {
        console.error('Error al sincronizar factura:', error);
      })
      .finally(() => {
        setSincronizando(false);
      });
  };

  const handleExportar = () => {
    // Lógica para exportar
    console.log('Exportando factura', id);
  };

  const handleVolver = () => {
    navigate('/facturas');
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      {/* Encabezado y acciones */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Box display="flex" alignItems="center" mb={1}>
            <IconButton onClick={handleVolver} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4">
              Factura #{factura.numero || 'Sin número'}
            </Typography>
            <IconButton 
              color="primary" 
              sx={{ ml: 2 }} 
              onClick={recargarFactura}
              title="Recargar datos"
            >
              <RefreshIcon />
            </IconButton>
          </Box>
          <Divider sx={{ mb: 2 }} />
        </Grid>
      </Grid>

      {/* Información general de la factura */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Fecha de Compra
                </Typography>
                <Typography variant="body1">
                  {factura.fecha ? moment(factura.fecha).format('DD/MM/YYYY HH:mm') : 'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Moneda
                </Typography>
                <Typography variant="body1">
                  {factura.moneda === 'USD' ? 'Dólares (USD)' : 'Bolívares (Bs)'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Tasa de Cambio
                </Typography>
                <Typography variant="body1">
                  {factura.tasa_cambio_valor ? 
                    `${parseFloat(factura.tasa_cambio_valor).toFixed(2)}` : 
                    'N/A'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Total USD
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  ${parseFloat(factura.total_usd || 0).toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  Total Bs
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  Bs.{parseFloat(factura.total_bs || 0).toFixed(2)}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Typography variant="subtitle2" color="textSecondary">
                  % Ganancia General
                </Typography>
                <Typography variant="body1">
                  {parseFloat(factura.porcentaje_ganancia || 30).toFixed(2)}%
                </Typography>
              </Grid>
            </Grid>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box display="flex" flexDirection="column" alignItems="flex-end">
              <Chip 
                label={factura.sincronizado_loyverse ? 'Sincronizado con Loyverse' : 'No sincronizado'} 
                color={factura.sincronizado_loyverse ? 'success' : 'warning'} 
                sx={{ mb: 2 }}
              />
              <Box sx={{ mt: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<GetAppIcon />}
                  onClick={handleExportar}
                  sx={{ mr: 1 }}
                >
                  Exportar
                </Button>
                {!factura.sincronizado_loyverse && (
                  <Button
                    variant="contained"
                    startIcon={<SyncIcon />}
                    onClick={handleSincronizar}
                    disabled={sincronizando}
                  >
                    {sincronizando ? 'Sincronizando...' : 'Sincronizar'}
                  </Button>
                )}
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Tabla de productos */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Productos Comprados
        </Typography>
        <TableContainer sx={{ mt: 2 }}>
          <Table aria-label="tabla de productos">
            <TableHead>
              <TableRow>
                <TableCell><strong>Producto</strong></TableCell>
                <TableCell align="right"><strong>Cantidad</strong></TableCell>
                <TableCell align="right"><strong>Unid/Paquete</strong></TableCell>
                <TableCell align="right"><strong>Precio Unit.</strong></TableCell>
                <TableCell align="right"><strong>Total</strong></TableCell>
                <TableCell align="right"><strong>Precio USD</strong></TableCell>
                <TableCell align="right"><strong>% Ganancia</strong></TableCell>
                <TableCell align="right"><strong>Precio Venta</strong></TableCell>
                <TableCell align="center"><strong>IVA</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {factura.detalles && factura.detalles.length > 0 ? (
                factura.detalles.map((detalle, index) => {
                  const porcentajeGanancia = parseFloat(detalle.porcentaje_ganancia || factura.porcentaje_ganancia || 30);
                  const precioUnitario = parseFloat(detalle.precio_unitario || 0);
                  const precioVenta = precioUnitario * (1 + (porcentajeGanancia / 100));
                  
                  return (
                    <TableRow key={index} hover>
                      <TableCell>{detalle.producto_nombre || 'Producto no disponible'}</TableCell>
                      <TableCell align="right">{parseFloat(detalle.cantidad || 0).toFixed(2)}</TableCell>
                      <TableCell align="right">{parseFloat(detalle.unidades_paquete || 1).toFixed(2)}</TableCell>
                      <TableCell align="right">${precioUnitario.toFixed(2)}</TableCell>
                      <TableCell align="right">${parseFloat(detalle.total || 0).toFixed(2)}</TableCell>
                      <TableCell align="right">${parseFloat(detalle.precio_compra_usd || 0).toFixed(2)}</TableCell>
                      <TableCell align="right">{porcentajeGanancia.toFixed(2)}%</TableCell>
                      <TableCell align="right">${precioVenta.toFixed(2)}</TableCell>
                      <TableCell align="center">
                        {detalle.aplicarIva ? 
                          <Chip label="Sí" color="primary" size="small" /> : 
                          <Chip label="No" variant="outlined" size="small" />
                        }
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
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

      {/* Resumen financiero y gráfico */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Resumen Financiero
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">Subtotal</Typography>
                <Typography variant="body1">${resumen.subtotal.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">IVA (16%)</Typography>
                <Typography variant="body1">${resumen.iva.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">Total Compra</Typography>
                <Typography variant="body1">${resumen.total.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="textSecondary">Ganancia Proyectada</Typography>
                <Typography variant="body1">${resumen.gananciaEstimada.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" fontWeight="bold">Valor de Venta Estimado</Typography>
                <Typography variant="h5" color="primary">${resumen.valorVenta.toFixed(2)}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Distribución de Compra por Categorías
            </Typography>
            {datosGrafico.length > 0 ? (
              <Box sx={{ height: 300, mt: 2 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={datosGrafico}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {datosGrafico.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Legend />
                    <RechartsTooltip formatter={(value) => `$${value.toFixed(2)}`} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            ) : (
              <Box display="flex" justifyContent="center" alignItems="center" sx={{ height: 300 }}>
                <Typography variant="body1" color="textSecondary">
                  No hay datos suficientes para mostrar el gráfico
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DetalleFactura;
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { fetchFacturas, sincronizarFactura } from '../store/facturasSlice';
import {
  Container,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Box,
  TablePagination,
  Chip,
  IconButton,
  Grid,
  Card,
  CardContent,
  Collapse,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { DateRangePicker } from '@mui/lab';
import DescriptionIcon from '@mui/icons-material/Description';
import SyncIcon from '@mui/icons-material/Sync';
import GetAppIcon from '@mui/icons-material/GetApp';
import FilterListIcon from '@mui/icons-material/FilterList';
import CloseIcon from '@mui/icons-material/Close';
import moment from 'moment';
import 'moment/locale/es';

moment.locale('es');

const ListadoFacturas = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const facturas = useSelector((state) => state.facturas.items);
  const status = useSelector((state) => state.facturas.status);
  const error = useSelector((state) => state.facturas.error);
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);
  const [filtros, setFiltros] = useState({
    fechaInicio: null,
    fechaFin: null,
    montoMinUSD: '',
    montoMaxUSD: '',
    sincronizado: 'todos',
    tipoTasa: 'todos'
  });
  
  // Estadísticas resumen
  const [stats, setStats] = useState({
    totalFacturas: 0,
    gastoTotalUSD: 0,
    gastoTotalBS: 0
  });

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchFacturas());
    }
    
    // Si tenemos facturas, calculamos estadísticas
    if (facturas.length > 0) {
      const totalUSD = facturas.reduce((sum, factura) => sum + factura.total_usd, 0);
      const totalBS = facturas.reduce((sum, factura) => sum + factura.total_bs, 0);
      
      setStats({
        totalFacturas: facturas.length,
        gastoTotalUSD: totalUSD,
        gastoTotalBS: totalBS
      });
    }
  }, [status, dispatch, facturas]);

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleFiltroChange = (campo, valor) => {
    setFiltros({
      ...filtros,
      [campo]: valor
    });
  };

  const aplicarFiltros = () => {
    // Aquí implementaremos la lógica para filtrar facturas
    // Por ahora, simplemente cerramos el panel de filtros
    setFiltrosAbiertos(false);
  };

  const resetFiltros = () => {
    setFiltros({
      fechaInicio: null,
      fechaFin: null,
      montoMinUSD: '',
      montoMaxUSD: '',
      sincronizado: 'todos',
      tipoTasa: 'todos'
    });
  };

  const viewFacturaDetail = (facturaId) => {
    navigate(`/facturas/${facturaId}`);
  };
  
  const sincronizarConLoyverse = (facturaId) => {
    dispatch(sincronizarFactura(facturaId));
  };
  
  const exportarFactura = (facturaId, formato = 'pdf') => {
    // Implementar lógica de exportación
    console.log(`Exportando factura ${facturaId} en formato ${formato}`);
  };

  const getSincronizadoChip = (sincronizado) => {
    const color = sincronizado ? 'success' : 'warning';
    const label = sincronizado ? 'SINCRONIZADO' : 'PENDIENTE';
    return <Chip label={label} color={color} size="small" />;
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
          Error al cargar las facturas: {error}
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Header con título y estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Typography variant="h4" gutterBottom>
            Facturas de Compra
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Registro de compras e inventario
          </Typography>
        </Grid>
        
        {/* Tarjetas de estadísticas */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Facturas
              </Typography>
              <Typography variant="h4">
                {stats.totalFacturas}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Gasto Total USD
              </Typography>
              <Typography variant="h4">
                ${stats.gastoTotalUSD.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Gasto Total Bs
              </Typography>
              <Typography variant="h4">
                Bs {stats.gastoTotalBS.toFixed(2)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Panel de filtros */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Button 
            startIcon={<FilterListIcon />}
            onClick={() => setFiltrosAbiertos(!filtrosAbiertos)}
          >
            {filtrosAbiertos ? 'Ocultar Filtros' : 'Mostrar Filtros'}
          </Button>
          
          <Box>
            <Button 
              variant="contained" 
              color="primary"
              onClick={() => navigate('/facturas/nueva')}
              sx={{ mr: 1 }}
            >
              Nueva Factura
            </Button>
          </Box>
        </Box>
        
        <Collapse in={filtrosAbiertos}>
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Monto Mínimo (USD)"
                type="number"
                value={filtros.montoMinUSD}
                onChange={(e) => handleFiltroChange('montoMinUSD', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Monto Máximo (USD)"
                type="number"
                value={filtros.montoMaxUSD}
                onChange={(e) => handleFiltroChange('montoMaxUSD', e.target.value)}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Estado Sincronización</InputLabel>
                <Select
                  value={filtros.sincronizado}
                  label="Estado Sincronización"
                  onChange={(e) => handleFiltroChange('sincronizado', e.target.value)}
                >
                  <MenuItem value="todos">Todos</MenuItem>
                  <MenuItem value="sincronizado">Sincronizados</MenuItem>
                  <MenuItem value="pendiente">Pendientes</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Tasa</InputLabel>
                <Select
                  value={filtros.tipoTasa}
                  label="Tipo de Tasa"
                  onChange={(e) => handleFiltroChange('tipoTasa', e.target.value)}
                >
                  <MenuItem value="todos">Todos</MenuItem>
                  <MenuItem value="BCV">Tasa BCV</MenuItem>
                  <MenuItem value="PARALELO">Tasa Paralelo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button 
                variant="outlined" 
                color="secondary" 
                onClick={resetFiltros}
                sx={{ mr: 1 }}
              >
                Resetear
              </Button>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={aplicarFiltros}
              >
                Aplicar Filtros
              </Button>
            </Grid>
          </Grid>
        </Collapse>
      </Paper>
      
      {/* Tabla de facturas */}
      <Paper elevation={3} sx={{ p: 2, mb: 4 }}>
        <TableContainer>
          <Table aria-label="tabla de facturas">
            <TableHead>
              <TableRow>
                <TableCell><strong>Número</strong></TableCell>
                <TableCell><strong>Fecha</strong></TableCell>
                <TableCell><strong>Total USD</strong></TableCell>
                <TableCell><strong>Total Bs</strong></TableCell>
                <TableCell><strong>% Ganancia</strong></TableCell>
                <TableCell><strong>Sincronizado</strong></TableCell>
                <TableCell><strong>Cant. Productos</strong></TableCell>
                <TableCell><strong>Acciones</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(rowsPerPage > 0
                ? facturas.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                : facturas
              ).map((factura) => (
                <TableRow key={factura.id} hover>
                  <TableCell>{factura.numero}</TableCell>
                  <TableCell>{moment(factura.fecha).format('DD/MM/YYYY HH:mm')}</TableCell>
                  <TableCell>${factura.total_usd.toFixed(2)}</TableCell>
                  <TableCell>Bs {factura.total_bs.toFixed(2)}</TableCell>
                  <TableCell>{factura.porcentaje_ganancia}%</TableCell>
                  <TableCell>{getSincronizadoChip(factura.sincronizado_loyverse)}</TableCell>
                  <TableCell>{factura.detalles?.length || 0}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex' }}>
                      <IconButton 
                        size="small" 
                        color="primary" 
                        onClick={() => viewFacturaDetail(factura.id)}
                        title="Ver detalle"
                      >
                        <DescriptionIcon />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="secondary" 
                        onClick={() => sincronizarConLoyverse(factura.id)}
                        title="Sincronizar con Loyverse"
                        disabled={factura.sincronizado_loyverse}
                      >
                        <SyncIcon />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="default" 
                        onClick={() => exportarFactura(factura.id)}
                        title="Exportar factura"
                      >
                        <GetAppIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
              {facturas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No hay facturas disponibles
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, { label: 'Todas', value: -1 }]}
          component="div"
          count={facturas.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Filas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
    </Container>
  );
};

export default ListadoFacturas; 
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { fetchFacturas } from '../store/facturasSlice';
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
  Grid,
  IconButton,
  Collapse,
  TextField,
  MenuItem,
  InputAdornment,
  Alert,
  AlertTitle,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { es } from 'date-fns/locale';
import DescriptionIcon from '@mui/icons-material/Description';
import SyncIcon from '@mui/icons-material/Sync';
import GetAppIcon from '@mui/icons-material/GetApp';
import FilterListIcon from '@mui/icons-material/FilterList';
import CloseIcon from '@mui/icons-material/Close';
import RefreshIcon from '@mui/icons-material/Refresh';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import TodayIcon from '@mui/icons-material/Today';
import DateRangeIcon from '@mui/icons-material/DateRange';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import ClearIcon from '@mui/icons-material/Clear';
import moment from 'moment';
import 'moment/locale/es';
import { formatApiError, getSolutionSuggestion, isConnectivityError } from '../utils/errorHandler';
import ConexionAPI from '../components/diagnostico/ConexionAPI';

moment.locale('es');

const ListadoFacturas = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const facturas = useSelector((state) => state.facturas.items) || [];
  const status = useSelector((state) => state.facturas.status);
  const error = useSelector((state) => state.facturas.error);
  
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);
  const [filtros, setFiltros] = useState({
    fechaDesde: null,
    fechaHasta: null,
    montoMinUSD: '',
    montoMaxUSD: '',
    sincronizado: 'todos',
    tipoTasa: 'todos'
  });
  const [filtroRapido, setFiltroRapido] = useState('');

  // Estadísticas básicas
  const stats = {
    totalFacturas: facturas.length,
    gastoTotalUSD: facturas.reduce((sum, factura) => sum + (parseFloat(factura.total_usd) || 0), 0),
    gastoTotalBS: facturas.reduce((sum, factura) => sum + (parseFloat(factura.total_bs) || 0), 0)
  };

  useEffect(() => {
    if (status === 'idle') {
      console.log('Iniciando carga de facturas...');
      dispatch(fetchFacturas())
        .unwrap()
        .then(result => {
          console.log('Facturas cargadas exitosamente:', result);
        })
        .catch(error => {
          console.error('Error capturado al cargar facturas:', error);
        });
    }
  }, [status, dispatch]);

  // Función para recargar facturas
  const recargarFacturas = () => {
    console.log('Recargando facturas...');
    dispatch(fetchFacturas())
      .unwrap()
      .then(result => {
        console.log('Facturas recargadas exitosamente:', result);
      })
      .catch(error => {
        console.error('Error al recargar facturas:', error);
      });
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const viewFacturaDetail = (facturaId) => {
    navigate(`/facturas/${facturaId}`);
  };

  const handleFiltroChange = (event) => {
    // Si no es un evento de DatePicker
    if (event && event.target) {
      setFiltros({
        ...filtros,
        [event.target.name]: event.target.value
      });
    }
  };
  
  const handleFechaDesdeChange = (newDate) => {
    setFiltroRapido('');
    setFiltros({
      ...filtros,
      fechaDesde: newDate
    });
  };

  const handleFechaHastaChange = (newDate) => {
    setFiltroRapido('');
    setFiltros({
      ...filtros,
      fechaHasta: newDate
    });
  };
  
  // Funciones para filtros rápidos de fecha
  const aplicarFiltroHoy = () => {
    const hoy = new Date();
    const nuevosFiltros = {
      ...filtros,
      fechaDesde: hoy,
      fechaHasta: hoy
    };
    setFiltros(nuevosFiltros);
    setFiltroRapido('hoy');
    aplicarFiltros(nuevosFiltros);
  };

  const aplicarFiltroSemanaActual = () => {
    const hoy = new Date();
    const inicioSemana = new Date(hoy);
    inicioSemana.setDate(hoy.getDate() - hoy.getDay());
    const finSemana = new Date(inicioSemana);
    finSemana.setDate(inicioSemana.getDate() + 6);
    
    const nuevosFiltros = {
      ...filtros,
      fechaDesde: inicioSemana,
      fechaHasta: finSemana
    };
    setFiltros(nuevosFiltros);
    setFiltroRapido('semana');
    aplicarFiltros(nuevosFiltros);
  };

  const aplicarFiltroMesActual = () => {
    const hoy = new Date();
    const inicioMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
    const finMes = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 0);
    
    const nuevosFiltros = {
      ...filtros,
      fechaDesde: inicioMes,
      fechaHasta: finMes
    };
    setFiltros(nuevosFiltros);
    setFiltroRapido('mes');
    aplicarFiltros(nuevosFiltros);
  };

  const limpiarFiltrosFechas = () => {
    const nuevosFiltros = {
      ...filtros,
      fechaDesde: null,
      fechaHasta: null
    };
    setFiltros(nuevosFiltros);
    setFiltroRapido('');
    aplicarFiltros(nuevosFiltros);
  };
  
  const handleFiltroRapidoChange = (event, newValue) => {
    if (newValue === null) return;
    
    switch(newValue) {
      case 'hoy':
        aplicarFiltroHoy();
        break;
      case 'semana':
        aplicarFiltroSemanaActual();
        break;
      case 'mes':
        aplicarFiltroMesActual();
        break;
      default:
        limpiarFiltrosFechas();
    }
  };
  
  const aplicarFiltros = (filtrosAplicar) => {
    console.log('Aplicando filtros:', filtrosAplicar);
    dispatch(fetchFacturas(filtrosAplicar))
      .unwrap()
      .then(result => {
        console.log('Filtros aplicados, facturas cargadas:', result);
      })
      .catch(error => {
        console.error('Error al aplicar filtros:', error);
      });
  };

  const resetearFiltros = () => {
    setFiltros({
      fechaDesde: null,
      fechaHasta: null,
      montoMinUSD: '',
      montoMaxUSD: '',
      sincronizado: 'todos',
      tipoTasa: 'todos'
    });
    setFiltroRapido('');
    dispatch(fetchFacturas());
  };

  const handleSincronizar = (facturaId) => {
    // Lógica para sincronizar con Loyverse
    console.log(`Sincronizando factura ${facturaId}`);
  };

  const handleExportar = (facturaId) => {
    // Lógica para exportar
    console.log(`Exportando factura ${facturaId}`);
  };

  const getSincronizadoChip = (sincronizado) => {
    return (
      <Chip 
        label={sincronizado ? 'Sincronizado' : 'Pendiente'} 
        color={sincronizado ? 'success' : 'warning'} 
        size="small" 
      />
    );
  };

  // Verificar si hay facturas disponibles
  const hayFacturas = Array.isArray(facturas) && facturas.length > 0;

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
    console.error('Error en estado de facturas:', error);
    
    // Formatear el error para mostrar información más útil
    const errorMessage = formatApiError(error, 'No se pudieron cargar las facturas');
    const solutionSuggestion = getSolutionSuggestion(error);
    const isConnectionError = isConnectivityError(error);
    
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert 
          severity="error" 
          variant="filled"
          sx={{ mb: 3 }}
          icon={<ErrorOutlineIcon fontSize="inherit" />}
        >
          <AlertTitle>Error al cargar las facturas</AlertTitle>
          {errorMessage}
        </Alert>
        
        {solutionSuggestion && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <AlertTitle>Sugerencia</AlertTitle>
            {solutionSuggestion}
          </Alert>
        )}
        
        {/* Mostrar herramienta de diagnóstico si parece un problema de conexión */}
        {isConnectionError && <ConexionAPI />}
        
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Detalles técnicos
          </Typography>
          <Typography variant="body2" sx={{ 
            fontFamily: 'monospace', 
            backgroundColor: '#f5f5f5', 
            p: 2, 
            borderRadius: 1,
            overflowX: 'auto'
          }}>
            {typeof error === 'object' ? JSON.stringify(error, null, 2) : error}
          </Typography>
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
            <Button
              startIcon={<RefreshIcon />}
              variant="contained"
              color="primary"
              onClick={() => dispatch(fetchFacturas())}
            >
              Reintentar
            </Button>
            
            <Button
              variant="outlined"
              onClick={() => window.location.reload()}
            >
              Recargar página
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      {/* Encabezado con título y estadísticas */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Typography variant="h4" gutterBottom>
            Facturas de Compra
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Registro de facturas de compra para BodegaClick
          </Typography>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper elevation={2} sx={{ p: 2, bgcolor: 'background.paper' }}>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="body2" color="textSecondary">Total Facturas</Typography>
                <Typography variant="h6">{stats.totalFacturas}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2" color="textSecondary">Total USD</Typography>
                <Typography variant="h6">${stats.gastoTotalUSD.toFixed(2)}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2" color="textSecondary">Total Bs</Typography>
                <Typography variant="h6">Bs.{stats.gastoTotalBS.toFixed(2)}</Typography>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
      
      {/* Panel de filtros */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Filtros
          </Typography>
          <IconButton onClick={() => setFiltrosAbiertos(!filtrosAbiertos)}>
            {filtrosAbiertos ? <CloseIcon /> : <FilterListIcon />}
          </IconButton>
        </Box>
        
        <Collapse in={filtrosAbiertos}>
          {/* Filtros de fecha rápidos */}
          <Box mb={3}>
            <Typography variant="subtitle2" gutterBottom>
              Filtros rápidos de fecha:
            </Typography>
            <ToggleButtonGroup
              value={filtroRapido}
              exclusive
              onChange={handleFiltroRapidoChange}
              aria-label="filtros rápidos de fecha"
              size="small"
            >
              <ToggleButton value="hoy" aria-label="hoy">
                <TodayIcon fontSize="small" sx={{ mr: 0.5 }} />
                Hoy
              </ToggleButton>
              <ToggleButton value="semana" aria-label="semana actual">
                <DateRangeIcon fontSize="small" sx={{ mr: 0.5 }} />
                Semana Actual
              </ToggleButton>
              <ToggleButton value="mes" aria-label="mes actual">
                <CalendarMonthIcon fontSize="small" sx={{ mr: 0.5 }} />
                Mes Actual
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
          
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="Fecha desde"
                value={filtros.fechaDesde}
                onChange={handleFechaDesdeChange}
                slotProps={{ textField: { size: 'small', fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <DatePicker
                label="Fecha hasta"
                value={filtros.fechaHasta}
                onChange={handleFechaHastaChange}
                slotProps={{ textField: { size: 'small', fullWidth: true } }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Monto mínimo (USD)"
                type="number"
                name="montoMinUSD"
                value={filtros.montoMinUSD}
                onChange={handleFiltroChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Monto máximo (USD)"
                type="number"
                name="montoMaxUSD"
                value={filtros.montoMaxUSD}
                onChange={handleFiltroChange}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Sincronizado"
                name="sincronizado"
                value={filtros.sincronizado}
                onChange={handleFiltroChange}
                variant="outlined"
                size="small"
              >
                <MenuItem value="todos">Todos</MenuItem>
                <MenuItem value="si">Sincronizados</MenuItem>
                <MenuItem value="no">No sincronizados</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                select
                label="Tipo de Tasa"
                name="tipoTasa"
                value={filtros.tipoTasa}
                onChange={handleFiltroChange}
                variant="outlined"
                size="small"
              >
                <MenuItem value="todos">Todos</MenuItem>
                <MenuItem value="BCV">BCV</MenuItem>
                <MenuItem value="PARALELO">Paralelo</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box display="flex" justifyContent="flex-end" gap={1}>
                <Button 
                  variant="outlined" 
                  onClick={resetearFiltros}
                >
                  Resetear
                </Button>
                <Button 
                  variant="contained" 
                  onClick={() => aplicarFiltros(filtros)}
                >
                  Aplicar filtros
                </Button>
              </Box>
            </Grid>
          </Grid>
        </Collapse>
      </Paper>
      
      {/* Botón para recargar facturas */}
      <Box display="flex" justifyContent="flex-end" mb={2}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={recargarFacturas}
        >
          Recargar facturas
        </Button>
      </Box>
      
      {/* Tabla principal de facturas */}
      <Paper elevation={3} sx={{ p: 2, mb: 4 }}>
        <TableContainer>
          <Table aria-label="tabla de facturas">
            <TableHead>
              <TableRow>
                <TableCell><strong>Número</strong></TableCell>
                <TableCell><strong>Fecha de Compra</strong></TableCell>
                <TableCell><strong>Total USD</strong></TableCell>
                <TableCell><strong>Total Bs</strong></TableCell>
                <TableCell><strong>Tasa</strong></TableCell>
                <TableCell><strong>% Ganancia</strong></TableCell>
                <TableCell><strong>Sincronizado</strong></TableCell>
                <TableCell><strong>Acciones</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {hayFacturas ? (
                (rowsPerPage > 0
                  ? facturas.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  : facturas
                ).map((factura) => (
                  <TableRow key={factura.id} hover>
                    <TableCell>{factura.numero || 'N/A'}</TableCell>
                    <TableCell>{moment(factura.fecha).format('DD/MM/YYYY HH:mm')}</TableCell>
                    <TableCell>${parseFloat(factura.total_usd).toFixed(2)}</TableCell>
                    <TableCell>Bs.{parseFloat(factura.total_bs).toFixed(2)}</TableCell>
                    <TableCell>
                      {factura.tasa_cambio ? 
                        `${parseFloat(factura.tasa_cambio.valor).toFixed(2)} (${factura.tasa_cambio.tipo})` : 
                        'N/A'}
                    </TableCell>
                    <TableCell>{parseFloat(factura.porcentaje_ganancia).toFixed(2)}%</TableCell>
                    <TableCell>{getSincronizadoChip(factura.sincronizado_loyverse)}</TableCell>
                    <TableCell>
                      <Box sx={{ '& > button': { mr: 1 } }}>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<DescriptionIcon />}
                          onClick={() => viewFacturaDetail(factura.id)}
                        >
                          Ver
                        </Button>
                        {!factura.sincronizado_loyverse && (
                          <IconButton
                            color="primary"
                            size="small"
                            onClick={() => handleSincronizar(factura.id)}
                            title="Sincronizar con Loyverse"
                          >
                            <SyncIcon />
                          </IconButton>
                        )}
                        <IconButton
                          color="secondary"
                          size="small"
                          onClick={() => handleExportar(factura.id)}
                          title="Exportar factura"
                        >
                          <GetAppIcon />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No hay facturas disponibles
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        {hayFacturas && (
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
        )}
      </Paper>
    </Container>
  );
};

export default ListadoFacturas;
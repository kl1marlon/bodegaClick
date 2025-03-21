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
  Chip
} from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
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

  useEffect(() => {
    if (status === 'idle') {
      dispatch(fetchFacturas());
    }
  }, [status, dispatch]);

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

  const getEstadoChip = (estado) => {
    let color = 'default';
    switch (estado) {
      case 'pendiente':
        color = 'warning';
        break;
      case 'pagada':
        color = 'success';
        break;
      case 'anulada':
        color = 'error';
        break;
      default:
        color = 'default';
    }
    return <Chip label={estado.toUpperCase()} color={color} size="small" />;
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
      <Typography variant="h4" gutterBottom>
        Listado de Facturas
      </Typography>
      
      <Paper elevation={3} sx={{ p: 2, mb: 4 }}>
        <TableContainer>
          <Table aria-label="tabla de facturas">
            <TableHead>
              <TableRow>
                <TableCell><strong>Número</strong></TableCell>
                <TableCell><strong>Fecha</strong></TableCell>
                <TableCell><strong>Cliente</strong></TableCell>
                <TableCell><strong>Total</strong></TableCell>
                <TableCell><strong>Estado</strong></TableCell>
                <TableCell><strong>Acciones</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(rowsPerPage > 0
                ? facturas.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                : facturas
              ).map((factura) => (
                <TableRow key={factura.id} hover>
                  <TableCell>{factura.numero_factura || 'N/A'}</TableCell>
                  <TableCell>{moment(factura.fecha_emision).format('DD/MM/YYYY HH:mm')}</TableCell>
                  <TableCell>{factura.cliente?.nombre || 'Cliente no registrado'}</TableCell>
                  <TableCell>${factura.total.toFixed(2)}</TableCell>
                  <TableCell>{getEstadoChip(factura.estado)}</TableCell>
                  <TableCell>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DescriptionIcon />}
                      onClick={() => viewFacturaDetail(factura.id)}
                    >
                      Ver Detalle
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {facturas.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
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
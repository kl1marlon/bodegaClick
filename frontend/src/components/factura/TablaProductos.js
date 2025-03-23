import React from 'react';
import {
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  IconButton,
  Typography,
  Box
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { aplicarRedondeoEspecial, calcularPrecioBs } from '../../utils/calculosPrecios';

/**
 * Componente para mostrar la tabla de productos seleccionados
 * 
 * @param {Object} props - Propiedades del componente
 * @param {Array} props.productos - Lista de productos seleccionados
 * @param {function} props.onEdit - Función para editar un producto
 * @param {function} props.onRemove - Función para eliminar un producto
 * @param {string} props.moneda - Moneda seleccionada ('USD' o 'BS')
 * @param {Object} props.tasaCambio - Objeto con la información de la tasa de cambio
 * @returns {JSX.Element} - Componente de tabla de productos
 */
const TablaProductos = ({ productos, onEdit, onRemove, moneda, tasaCambio }) => {
  // Calcular el total de la factura
  const calcularTotal = () => {
    return productos.reduce((sum, item) => sum + item.total, 0);
  };

  // Mostrar el precio en bolívares según corresponda
  const mostrarPrecioEnBs = (precio_usd) => {
    if (!tasaCambio || !precio_usd) return 0;
    return calcularPrecioBs(precio_usd, tasaCambio.valor);
  };

  return (
    <TableContainer 
      component={Paper} 
      elevation={3}
      sx={{ 
        borderRadius: 2,
        overflow: 'hidden',
        mb: 3
      }}
    >
      <Table>
        <TableHead sx={{ backgroundColor: '#f1f5f9' }}>
          <TableRow>
            <TableCell sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Producto</TableCell>
            <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Cantidad</TableCell>
            <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Precio Unitario</TableCell>
            <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Total</TableCell>
            <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>% Ganancia</TableCell>
            <TableCell align="center" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>IVA</TableCell>
            <TableCell align="right" sx={{ fontWeight: 600, color: '#475569', py: 2 }}>Acciones</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {productos.map((item, index) => (
            <TableRow 
              key={index} 
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
              <TableCell sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>{item.producto.nombre}</TableCell>
              <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>{item.cantidad}</TableCell>
              <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                {moneda === 'BS' ? 
                  `${aplicarRedondeoEspecial(item.precio_unitario).toFixed(2)} ${moneda}` : 
                  `${item.precio_unitario.toFixed(2)} ${moneda} (${mostrarPrecioEnBs(item.precio_unitario).toFixed(2)} BS)`
                }
              </TableCell>
              <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                {moneda === 'BS' ? 
                  `${aplicarRedondeoEspecial(item.total).toFixed(2)} ${moneda}` : 
                  `${item.total.toFixed(2)} ${moneda} (${mostrarPrecioEnBs(item.total).toFixed(2)} BS)`
                }
              </TableCell>
              <TableCell align="right" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                {item.porcentajeGanancia !== null ? `${item.porcentajeGanancia}%` : `(global)`}
              </TableCell>
              <TableCell align="center" sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}>
                {item.aplicarIva ? 
                  <Typography sx={{ color: '#059669' }}>Sí (16%)</Typography> : 
                  <Typography sx={{ color: '#6b7280' }}>No</Typography>
                }
              </TableCell>
              <TableCell align="right" sx={{ borderBottom: '1px solid #f1f5f9' }}>
                <IconButton 
                  onClick={() => onEdit(index)} 
                  size="small"
                  sx={{ 
                    color: '#3b82f6',
                    backgroundColor: '#eff6ff',
                    mr: 1,
                    '&:hover': {
                      backgroundColor: '#dbeafe'
                    }
                  }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton 
                  onClick={() => onRemove(index)} 
                  size="small"
                  sx={{ 
                    color: '#ef4444',
                    backgroundColor: '#fef2f2',
                    '&:hover': {
                      backgroundColor: '#fee2e2'
                    }
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
          {productos.length > 0 && (
            <TableRow sx={{ backgroundColor: '#f1f5f9' }}>
              <TableCell colSpan={3} align="right" sx={{ fontWeight: 700, color: '#1e293b', py: 2 }}>
                Total:
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 700, color: '#1e293b', py: 2 }}>
                {moneda === 'BS' ? 
                  `${aplicarRedondeoEspecial(calcularTotal()).toFixed(2)} ${moneda}` : 
                  `${calcularTotal().toFixed(2)} ${moneda} (${mostrarPrecioEnBs(calcularTotal()).toFixed(2)} BS)`
                }
              </TableCell>
              <TableCell colSpan={3} />
            </TableRow>
          )}
          {productos.length === 0 && (
            <TableRow>
              <TableCell colSpan={7} align="center" sx={{ py: 4, color: '#6b7280' }}>
                No hay productos en la factura. Busque y agregue productos usando el formulario superior.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default TablaProductos; 
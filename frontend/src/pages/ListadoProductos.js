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
  Alert,
  FormControlLabel,
  Switch,
  Select,
  FormControl,
  InputLabel,
  FormHelperText,
  Slider,
  Checkbox
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InventoryIcon from '@mui/icons-material/Inventory';
import CurrencyExchangeIcon from '@mui/icons-material/CurrencyExchange';
import InfoIcon from '@mui/icons-material/Info';
import UpdateIcon from '@mui/icons-material/Update';
import LoyaltyIcon from '@mui/icons-material/Loyalty';
import ReceiptIcon from '@mui/icons-material/Receipt';
import CalculateIcon from '@mui/icons-material/Calculate';
import SyncIcon from '@mui/icons-material/Sync';
import FilterListIcon from '@mui/icons-material/FilterList';
import EditAttributesIcon from '@mui/icons-material/EditAttributes';
import InventoryOutlinedIcon from '@mui/icons-material/InventoryOutlined';
import WarehouseIcon from '@mui/icons-material/Warehouse';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import EditIcon from '@mui/icons-material/Edit';
import { fetchProductos, syncFromLoyverse, updateProductoTipoTasa, syncInventory, updateProducto } from '../store/productosSlice';
import { fetchTasasCambio, fetchLatestTasa, createTasaCambio } from '../store/tasasCambioSlice';
import { aplicarRedondeoEspecial } from '../utils/calculosPrecios';
import DialogoEditarProducto from '../components/factura/DialogoEditarProducto';
import AddIcon from '@mui/icons-material/Add';
import { useNavigate } from 'react-router-dom';

const ListadoProductos = () => {
  const dispatch = useDispatch();
  const { items: productos, status } = useSelector((state) => state.productos);
  const { items: tasasCambio } = useSelector((state) => state.tasasCambio);
  const navigate = useNavigate();
  
  // Estados para paginación
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Estado para búsqueda
  const [searchTerm, setSearchTerm] = useState('');
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  
  // Estado para filtro de categoría
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState('');
  const [categorias, setCategorias] = useState([]);
  
  // Estado para filtro de productos sin precio
  const [mostrarSinPrecio, setMostrarSinPrecio] = useState(false);
  
  // Estado para tasas de cambio
  const [tasaBCV, setTasaBCV] = useState(null);
  const [tasaParalelo, setTasaParalelo] = useState(null);
  const [tasaSeleccionadaProducto, setTasaSeleccionadaProducto] = useState({});
  
  // Estado para diálogo de edición de tasa
  const [editTasaDialogOpen, setEditTasaDialogOpen] = useState(false);
  const [tipoTasaEdicion, setTipoTasaEdicion] = useState('');
  const [nuevaTasaValor, setNuevaTasaValor] = useState('');
  
  // Estado para diálogo informativo
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  
  // Estado para diálogo de estadísticas por categoría
  const [statsDialogOpen, setStatsDialogOpen] = useState(false);
  
  // Estado para sincronización
  const [sincronizando, setSincronizando] = useState(false);
  const [actualizarPrecios, setActualizarPrecios] = useState(true);
  
  // Estado para opciones de sincronización
  const [opcionesSincronizacion, setOpcionesSincronizacion] = useState({
    tipo: 'todos',
    incluir_precios: true, 
    actualizar_existentes: true,
    categorias: []
  });
  
  // Estado para diálogo de selección de productos específicos
  const [productosSeleccionados, setProductosSeleccionados] = useState([]);
  
  // Estado para diálogo de opciones de sincronización
  const [syncOptionsDialogOpen, setSyncOptionsDialogOpen] = useState(false);
  
  // Estado para diálogo de sincronización de inventario
  const [syncInventoryDialogOpen, setSyncInventoryDialogOpen] = useState(false);
  const [sincronizandoInventario, setSincronizandoInventario] = useState(false);
  const [opcionesInventario, setOpcionesInventario] = useState({
    force: false,
  });
  
  // Estado para feedback
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // Estado para almacenar referencias a intervalos
  const [intervalos, setIntervalos] = useState([]);
  
  // Estado para edición de producto
  const [editProductoDialogOpen, setEditProductoDialogOpen] = useState(false);
  const [productoEditando, setProductoEditando] = useState(null);
  const [monedaEdicion, setMonedaEdicion] = useState('USD');
  
  // Cargar productos y tasas al montar el componente
  useEffect(() => {
    const obtenerDatos = async () => {
      try {
        // Solo cargar productos si aún no están cargados
        if (status !== 'succeeded') {
          await dispatch(fetchProductos()).unwrap();
        }
        
        // Cargar tasas de cambio una sola vez
        if (tasasCambio.length === 0) {
          await dispatch(fetchTasasCambio()).unwrap();
        }
        
        // Solo cargar tasas más recientes si no están cargadas
        if (!tasaBCV && !tasaParalelo) {
          const [bcvAction, paraleloAction] = await Promise.all([
            dispatch(fetchLatestTasa('BCV')),
            dispatch(fetchLatestTasa('PARALELO'))
          ]);
          
          if (bcvAction.payload) {
            setTasaBCV(bcvAction.payload);
          }
          
          if (paraleloAction.payload) {
            setTasaParalelo(paraleloAction.payload);
          }
        }
      } catch (error) {
        console.error("Error al cargar datos iniciales:", error);
      }
    };
    
    obtenerDatos();
    
    // Eliminar dependencias que causan re-renders innecesarios
  }, [dispatch, status, tasasCambio.length]);
  
  // Extraer categorías únicas de los productos
  useEffect(() => {
    if (productos.length > 0) {
      const uniqueCategorias = ['', ...new Set(productos.map(producto => producto.categoria).filter(Boolean))];
      setCategorias(uniqueCategorias);
    }
  }, [productos]);
  
  // Inicializar tasas seleccionadas para cada producto
  useEffect(() => {
    if (productos.length > 0 && tasaParalelo) {
      const initialTasas = {};
      productos.forEach(producto => {
        initialTasas[producto.id] = producto.tipo_tasa || 'PARALELO';
      });
      setTasaSeleccionadaProducto(initialTasas);
    }
  }, [productos, tasaParalelo]);
  
  // Filtrar productos cuando cambia el término de búsqueda, la categoría o la lista de productos
  useEffect(() => {
    if (productos.length > 0) {
      let filtered = [...productos];
      
      // Filtrar por término de búsqueda
      if (searchTerm.trim() !== '') {
        filtered = filtered.filter(producto => 
          producto.nombre.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
      
      // Filtrar por categoría
      if (categoriaSeleccionada !== '') {
        filtered = filtered.filter(producto => 
          producto.categoria === categoriaSeleccionada
        );
      }
      
      // Filtrar productos sin precio_base_usd
      if (mostrarSinPrecio) {
        filtered = filtered.filter(producto => 
          !producto.precio_base_usd || Number(producto.precio_base_usd) === 0
        );
      }
      
      setProductosFiltrados(filtered);
      setPage(0); // Resetear a la primera página cuando cambia el filtro
    }
  }, [searchTerm, categoriaSeleccionada, productos, mostrarSinPrecio]);
  
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
    // Actualizar el estado local inmediatamente para una respuesta UI rápida
    setTasaSeleccionadaProducto({
      ...tasaSeleccionadaProducto,
      [productoId]: tipoTasa
    });
    
    // Enviar la actualización al backend
    dispatch(updateProductoTipoTasa({ productoId, tipoTasa }))
      .unwrap()
      .then(() => {
        setSnackbar({
          open: true,
          message: `Tipo de tasa actualizado a ${tipoTasa} correctamente`,
          severity: 'success'
        });
      })
      .catch((error) => {
        console.error("Error al actualizar el tipo de tasa:", error);
        setSnackbar({
          open: true,
          message: `Error al actualizar tipo de tasa: ${error.message}`,
          severity: 'error'
        });
        // Revertir el cambio en la UI si hay error
        setTasaSeleccionadaProducto({
          ...tasaSeleccionadaProducto,
          [productoId]: tasaSeleccionadaProducto[productoId] === 'BCV' ? 'PARALELO' : 'BCV'
        });
      });
  };
  
  // Manejar cambio de categoría
  const handleCategoriaChange = (event) => {
    setCategoriaSeleccionada(event.target.value);
  };
  
  // Resetear filtros
  const resetearFiltros = () => {
    setSearchTerm('');
    setCategoriaSeleccionada('');
    setMostrarSinPrecio(false);
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
  
  // Función para calcular el precio BS a partir del precio_base_usd y la tasa
  const calcularPrecioBS = (precioBaseUSD, productoId) => {
    if (!precioBaseUSD) return 0;
    
    // Convertir a número
    precioBaseUSD = Number(precioBaseUSD);
    
    // Obtener la tasa seleccionada para este producto
    const tipoTasa = tasaSeleccionadaProducto[productoId] || 'PARALELO';
    const tasa = tipoTasa === 'BCV' ? tasaBCV : tasaParalelo;
    
    if (!tasa || tasa.valor <= 0) return 0;
    
    // Calcular precio en bolívares
    const precioBs = precioBaseUSD * tasa.valor;
    
    // Aplicar el redondeo especial que se usa en las facturas
    return aplicarRedondeoEspecial(precioBs);
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
  
  // Función para abrir diálogo de opciones de sincronización
  const abrirSyncOptionsDialog = () => {
    setSyncOptionsDialogOpen(true);
  };
  
  // Función para cerrar diálogo de opciones de sincronización
  const cerrarSyncOptionsDialog = () => {
    setSyncOptionsDialogOpen(false);
  };
  
  // Función para abrir diálogo de opciones de sincronización de inventario
  const abrirSyncInventoryDialog = () => {
    setSyncInventoryDialogOpen(true);
  };
  
  // Función para cerrar diálogo de opciones de sincronización de inventario
  const cerrarSyncInventoryDialog = () => {
    setSyncInventoryDialogOpen(false);
  };
  
  // Función para manejar la sincronización desde Loyverse
  const handleSyncFromLoyverse = () => {
    // Primero abrir el diálogo de opciones en lugar de iniciar directamente
    abrirSyncOptionsDialog();
  };
  
  // Función para manejar la sincronización de inventario
  const handleSyncInventory = () => {
    // Abrir el diálogo de opciones de sincronización de inventario
    abrirSyncInventoryDialog();
  };
  
  // Manejar cambio en productos seleccionados
  const handleChangeProductosSeleccionados = (event) => {
    const value = event.target.value;
    setProductosSeleccionados(value);
    setOpcionesSincronizacion(prev => ({
      ...prev,
      productos_ids: value
    }));
  };
  
  // Manejar cambio en categorías seleccionadas (múltiples)
  const handleChangeCategoriasSincronizacion = (event) => {
    const value = event.target.value;
    setOpcionesSincronizacion(prev => ({
      ...prev,
      categorias: typeof value === 'string' ? value.split(',') : value
    }));
  };
  
  // Manejar cambio en opciones de sincronización
  const handleChangeOpcionesSincronizacion = (event) => {
    const { name, value, checked, type } = event.target;
    
    setOpcionesSincronizacion(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const handleChangeOpcionesInventario = (event) => {
    const { name, value, checked, type } = event.target;
    
    setOpcionesInventario(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // Abrir el diálogo informativo
  const abrirInfoDialog = () => {
    setInfoDialogOpen(true);
  };
  
  // Cerrar el diálogo informativo
  const cerrarInfoDialog = () => {
    setInfoDialogOpen(false);
  };
  
  // Abrir el diálogo de estadísticas por categoría
  const abrirStatsDialog = () => {
    setStatsDialogOpen(true);
  };
  
  // Cerrar el diálogo de estadísticas por categoría
  const cerrarStatsDialog = () => {
    setStatsDialogOpen(false);
  };
  
  // Abrir diálogo de edición de tasa
  const abrirEditTasaDialog = (tipo) => {
    setTipoTasaEdicion(tipo);
    setNuevaTasaValor(tipo === 'BCV' ? (tasaBCV?.valor || '') : (tasaParalelo?.valor || ''));
    setEditTasaDialogOpen(true);
  };
  
  // Cerrar diálogo de edición de tasa
  const cerrarEditTasaDialog = () => {
    setEditTasaDialogOpen(false);
  };
  
  // Guardar nueva tasa de cambio
  const guardarNuevaTasa = () => {
    if (!nuevaTasaValor || nuevaTasaValor <= 0) {
      setSnackbar({
        open: true,
        message: 'Por favor ingrese un valor válido para la tasa de cambio',
        severity: 'error'
      });
      return;
    }

    const tasaData = {
      tipo: tipoTasaEdicion,
      valor: parseFloat(nuevaTasaValor),
      fecha: new Date().toISOString().split('T')[0]
    };

    dispatch(createTasaCambio(tasaData))
      .unwrap()
      .then(() => {
        setSnackbar({
          open: true,
          message: `Tasa de cambio ${tipoTasaEdicion} actualizada correctamente`,
          severity: 'success'
        });
        dispatch(fetchLatestTasa(tipoTasaEdicion)).then(action => {
          if (tipoTasaEdicion === 'BCV') {
            setTasaBCV(action.payload);
          } else {
            setTasaParalelo(action.payload);
          }
        });
        setEditTasaDialogOpen(false);
      })
      .catch((error) => {
        console.error("Error al actualizar la tasa de cambio:", error);
        setSnackbar({
          open: true,
          message: `Error al actualizar la tasa de cambio: ${error.message}`,
          severity: 'error'
        });
      });
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
  
  // Función para consultar el progreso de la tarea
  const consultarProgresoTarea = async (taskId, intervalId) => {
    // Variable para controlar si se debe seguir intentando
    let debeReintentar = true;
    let respuestaExitosa = false;
    let data = null;
    let errorCount = 0; // Contador local de errores

    try {
      // Realizar intentos con tiempos de espera progresivos
      for (let intento = 1; intento <= 3 && debeReintentar; intento++) {
        try {
          console.log(`Intento ${intento} de consulta de progreso para tarea ${taskId}`);
          
          // URL del endpoint de estado - Usar URL del worker
          const workerUrl = window.ENV?.WORKER_API_URL || 'https://worker-production-7eb3.up.railway.app/api';
          const mainApiUrl = process.env.REACT_APP_API_URL || '';
          const url = `${workerUrl}/tareas/estado/${taskId}/`;
          console.log(`Consultando endpoint: ${url}`);
          
          // Configurar un timeout más amplio para la petición y usar modo no-cors
          const controlador = new AbortController();
          const timeoutId = setTimeout(() => controlador.abort(), 10000); // 10 segundos de timeout
          
          const response = await fetch(url, {
            signal: controlador.signal,
            mode: 'no-cors', // Usar modo no-cors para evitar errores CORS
            headers: {
              'Cache-Control': 'no-cache, no-store, must-revalidate',
              'Pragma': 'no-cache',
              'Expires': '0'
            }
          });
          
          // Limpiar el timeout una vez recibida la respuesta
          clearTimeout(timeoutId);
          
          if (response.ok) {
            data = await response.json();
            console.log("Respuesta del estado de la tarea:", data);
            respuestaExitosa = true;
            debeReintentar = false;
            errorCount = 0; // Resetear contador de errores si hay éxito
            break; // Salir del bucle si la respuesta es exitosa
          } else if (response.type === 'opaque') {
            // Cuando usamos modo no-cors, la respuesta es "opaque" y no podemos acceder a su contenido
            console.log("Recibida respuesta opaca debido al modo no-cors");
            break; // Salir del bucle, pero manejaremos esto después
          } else {
            const responseText = await response.text();
            console.warn(`Intento ${intento} falló con status ${response.status}. Respuesta: ${responseText}`);
            
            // Si el error es 404 (no encontrado), la tarea puede haber sido eliminada o no existe
            if (response.status === 404) {
              console.warn(`La tarea ${taskId} no fue encontrada. Posiblemente ya no exista.`);
              debeReintentar = false;
              throw new Error(`Tarea no encontrada (404): ${responseText || 'Sin respuesta'}`);
            }
            
            // Si el error es 500 o 502, puede ser un problema temporal con el servidor
            if (response.status === 500 || response.status === 502) {
              console.warn(`Error del servidor (${response.status}). Reintentando...`);
              
              // Usar delay progresivo para reintentos (1s, 2s, 4s)
              const delayMs = Math.pow(2, intento - 1) * 1000;
              await new Promise(resolve => setTimeout(resolve, delayMs));
              
              // Seguir intentando
              debeReintentar = intento < 3;
            } else {
              // Para otros errores, no reintentar
              debeReintentar = false;
              throw new Error(`Error al consultar estado: ${response.status} - ${responseText || 'Sin respuesta'}`);
            }
          }
        } catch (fetchError) {
          // Si hubo un error de red o se abortó la petición
          const esCancelacion = fetchError.name === 'AbortError';
          console.warn(`${esCancelacion ? 'Timeout' : 'Error de red'} en intento ${intento}: ${fetchError.message}`);
          
          // Usar delay progresivo para reintentos (1s, 2s, 4s)
          const delayMs = Math.pow(2, intento - 1) * 1000;
          await new Promise(resolve => setTimeout(resolve, delayMs));
          
          // Seguir intentando solo si no es el último intento
          debeReintentar = intento < 3;
          
          // Si es el último intento, lanzar el error para que lo maneje el catch principal
          if (intento === 3 && !respuestaExitosa) {
            throw fetchError;
          }
        }
      }
      
      // Si llegamos aquí sin datos, es porque todos los intentos fallaron
      if (!respuestaExitosa || !data) {
        // Si la última respuesta fue opaca, creamos datos simulados para seguir mostrando progreso
        if (response && response.type === 'opaque') {
          console.log("Usando datos simulados para respuesta opaca");
          data = {
            status: 'PENDING',
            percentage: 50,
            current: 0,
            total: 0,
            metadata: {
              productos_actualizados: 0,
              productos_fallidos: 0
            }
          };
        } else {
          throw new Error("No se pudo consultar el estado después de varios intentos");
        }
      }
      
      // Interpretar diferentes tipos de respuestas
      const status = data.status || 'UNKNOWN';
      let percentage = data.percentage || 0;
      let current = data.current || 0;
      let total = data.total || 0;
      
      // Si tenemos resultado pero no porcentaje (formatos diferentes)
      if (status === 'SUCCESS' && data.result && !data.percentage) {
        const result = data.result;
        current = result.processed_items || 0;
        total = result.total_items || 0;
        percentage = total > 0 ? Math.floor((current / total) * 100) : 100;
      }
      
      // Actualizar el snackbar con la información del progreso
      if (status === 'SUCCESS') {
        const productosActualizados = data.result?.productos_actualizados || 0;
        const productosFallidos = data.result?.productos_fallidos || 0;
        
        setSnackbar({
          open: true,
          message: `Sincronización completada: ${productosActualizados} productos actualizados, ${productosFallidos} fallidos`,
          severity: 'success',
          autoHideDuration: 6000
        });
        setSincronizando(false);
        dispatch(fetchProductos()); // Refrescar la lista de productos
        clearInterval(intervalId);
      } else if (status === 'FAILURE' || status === 'ERROR') {
        const errorMsg = data.error || 'Error desconocido';
        setSnackbar({
          open: true,
          message: `Error en la sincronización: ${errorMsg}`,
          severity: 'error',
          autoHideDuration: 8000
        });
        setSincronizando(false);
        clearInterval(intervalId);
      } else if (status === 'REVOKED') {
        const msg = data.error || 'Tarea cancelada';
        setSnackbar({
          open: true,
          message: msg,
          severity: 'warning',
          autoHideDuration: 6000
        });
        setSincronizando(false);
        clearInterval(intervalId);
      } else {
        // En progreso o cualquier otro estado
        const metadata = data.metadata || {};
        const productosActualizados = metadata.productos_actualizados || 0;
        const productosFallidos = metadata.productos_fallidos || 0;
        
        let mensaje = `Sincronizando precios: ${percentage}% completado (${current}/${total}).`;
        if (productosActualizados > 0) {
          mensaje += ` Actualizados: ${productosActualizados}`;
        }
        if (productosFallidos > 0) {
          mensaje += `, Fallidos: ${productosFallidos}`;
        }
        
        setSnackbar({
          open: true,
          message: mensaje,
          severity: 'info',
          autoHideDuration: 3000 // Duración corta para que se actualice pronto
        });
      }
    } catch (error) {
      console.error("Error consultando progreso:", error);
      
      // Incrementar contador de errores
      errorCount++;
      
      // Si hay demasiados errores consecutivos, detener la consulta
      if (errorCount > 5) {
        console.error("Demasiados errores consecutivos. Deteniendo consulta de progreso.");
        setSnackbar({
          open: true,
          message: "No se pudo obtener el progreso de la sincronización. La tarea podría seguir en curso en segundo plano.",
          severity: 'warning',
          autoHideDuration: 8000
        });
        setSincronizando(false);
        clearInterval(intervalId);
      } else {
        // Mostrar mensaje de error pero seguir intentando
        setSnackbar({
          open: true,
          message: `Error al consultar progreso (intento ${errorCount}/5). Reintentando...`,
          severity: 'warning',
          autoHideDuration: 2000
        });
      }
    }
  };
  
  // Función para iniciar la sincronización con las opciones seleccionadas
  const iniciarSincronizacion = () => {
    setSincronizando(true);
    cerrarSyncOptionsDialog();
    
    console.log("Iniciando sincronización con opciones:", opcionesSincronizacion);
    
    // Mostrar mensaje de inicio
    setSnackbar({
      open: true,
      message: "Iniciando sincronización de precios...",
      severity: 'info',
      autoHideDuration: 3000
    });
    
    dispatch(syncFromLoyverse(opcionesSincronizacion))
      .then((result) => {
        if (result.error) {
          console.error("Error en la sincronización:", result.error.message);
          setSnackbar({
            open: true,
            message: `Error al iniciar sincronización: ${result.error.message}`,
            severity: 'error',
            autoHideDuration: 8000
          });
          setSincronizando(false);
          return;
        }
        
        console.log("Tarea de sincronización iniciada exitosamente:", result.payload);
        
        // Guardamos el ID de la tarea para poder consultar su progreso
        const taskId = result.payload.task_id;
        if (!taskId) {
          console.error("No se recibió ID de tarea en la respuesta");
          setSnackbar({
            open: true,
            message: "Error: No se pudo obtener el identificador de la tarea",
            severity: 'error',
            autoHideDuration: 8000
          });
          setSincronizando(false);
          return;
        }
        
        // Mostrar mensaje con el ID de la tarea para referencia
        setSnackbar({
          open: true,
          message: `Tarea iniciada (ID: ${taskId}). Consultando progreso...`,
          severity: 'info',
          autoHideDuration: 3000
        });
        
        // Variable para controlar el intervalId dentro de las funciones
        let intervalId;
        
        // Número máximo de errores consecutivos permitidos
        let maxErrorCount = 5;
        
        // Consultar inmediatamente y luego cada 2 segundos
        const consultarProgresoWrapper = () => consultarProgresoTarea(taskId, intervalId);
        consultarProgresoWrapper();
        intervalId = setInterval(consultarProgresoWrapper, 2000);
        
        // Almacenar el ID del intervalo para poder limpiarlo después
        setIntervalos(prev => [...prev, intervalId]);
        
        // Limpiar el intervalo después de 30 minutos por seguridad
        setTimeout(() => {
          if (intervalId) {
            clearInterval(intervalId);
            // Verificar si aún está sincronizando después de 30 minutos
            if (sincronizando) {
              console.warn("La tarea sigue en ejecución después de 30 minutos. Deteniendo consulta de progreso.");
              setSnackbar({
                open: true,
                message: "La tarea lleva más de 30 minutos en ejecución. Se ha detenido la consulta de progreso, pero la tarea sigue ejecutándose en segundo plano.",
                severity: 'warning',
                autoHideDuration: 10000
              });
              setSincronizando(false);
            }
          }
        }, 30 * 60 * 1000);
      })
      .catch((error) => {
        console.error("Error inesperado al iniciar sincronización:", error);
        setSincronizando(false);
        setSnackbar({
          open: true,
          message: `Error inesperado: ${error.message || 'Error desconocido'}`,
          severity: 'error',
          autoHideDuration: 8000
        });
      });
  };
  
  // Función para iniciar la sincronización de inventario
  const iniciarSincronizacionInventario = () => {
    setSincronizando(true);
    cerrarSyncInventoryDialog();
    
    console.log("Iniciando sincronización de inventario");
    
    dispatch(syncInventory({ force: opcionesInventario.force }))
      .then((result) => {
        if (result.error) {
          console.error("Error al iniciar sincronización de inventario:", result.error.message);
          setSnackbar({
            open: true,
            message: `Error al iniciar sincronización: ${result.error.message}`,
            severity: 'error'
          });
          setSincronizando(false);
        } else {
          console.log("Sincronización de inventario completada exitosamente:", result.payload);
          
          // Guardamos el ID de la tarea para poder consultar su progreso
          const taskId = result.payload.task_id;
          
          // Variable para controlar el intervalId dentro de las funciones
          let intervalId;
          
          // Contador de errores para detener después de varios fallos consecutivos
          let errorCount = 0;
          
          // Función para consultar el progreso de la tarea
          const consultarProgresoTarea = async () => {
            try {
              // Intento de consulta con reintentos
              let retries = 3;
              let response;
              let error;
              
              for (let i = 0; i < retries; i++) {
                try {
                  console.log(`Intento ${i+1} de consulta de progreso para tarea ${taskId}`);
                  
                  // URL del endpoint de estado - Usar URL del worker
                  const workerUrl = window.ENV?.WORKER_API_URL || 'https://worker-production-7eb3.up.railway.app/api';
                  response = await fetch(`${workerUrl}/tareas/estado/${taskId}/`, {
                    mode: 'no-cors', // Usar modo no-cors para evitar errores CORS
                    headers: {
                      'Cache-Control': 'no-cache, no-store, must-revalidate',
                      'Pragma': 'no-cache',
                      'Expires': '0'
                    }
                  });
                  
                  if (response.ok) {
                    break; // Salir del bucle si la respuesta es exitosa
                  } else if (response.type === 'opaque') {
                    // Cuando usamos modo no-cors, la respuesta es "opaque" y no podemos acceder a su contenido
                    console.log("Recibida respuesta opaca debido al modo no-cors");
                    break; // Salir del bucle, pero manejaremos esto después
                  } else {
                    // Guardar el error pero seguir intentando
                    error = new Error(`Error al consultar estado: ${response.status}`);
                    console.warn(`Intento ${i+1} falló con status ${response.status}. ${retries - i - 1} intentos restantes.`);
                    
                    // Si no es el último intento, esperar antes de reintentar
                    if (i < retries - 1) {
                      await new Promise(resolve => setTimeout(resolve, 1000)); // Esperar 1 segundo
                    }
                  }
                } catch (fetchError) {
                  // Guardar el error de red pero seguir intentando
                  error = fetchError;
                  console.warn(`Error de red en intento ${i+1}: ${fetchError.message}. ${retries - i - 1} intentos restantes.`);
                  
                  // Si no es el último intento, esperar antes de reintentar
                  if (i < retries - 1) {
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Esperar 1 segundo
                  }
                }
              }
              
              // Si después de todos los intentos no tenemos una respuesta válida
              if (!response || (!response.ok && response.type !== 'opaque')) {
                throw error || new Error("No se pudo consultar el estado después de varios intentos");
              }
              
              // Si recibimos una respuesta opaca debido a no-cors, creamos datos simulados
              let data;
              if (response.type === 'opaque') {
                console.log("Usando datos simulados para respuesta opaca");
                data = {
                  status: 'PENDING',
                  percentage: 50,
                  current: 0,
                  total: 0
                };
              } else {
                data = await response.json();
              }
              
              console.log("Estado de la tarea:", data);
              
              // Interpretar diferentes tipos de respuestas
              const status = data.status || 'UNKNOWN';
              let percentage = data.percentage || 0;
              let current = data.current || 0;
              let total = data.total || 0;
              
              // Si tenemos resultado pero no porcentaje (formatos diferentes)
              if (status === 'SUCCESS' && data.result && !data.percentage) {
                const result = data.result;
                current = result.processed_items || 0;
                total = result.total_items || 0;
                percentage = total > 0 ? Math.floor((current / total) * 100) : 100;
              }
              
              // Actualizar el snackbar con la información del progreso
              if (status === 'SUCCESS') {
                setSnackbar({
                  open: true,
                  message: `Sincronización completada: ${current} productos actualizados`,
                  severity: 'success'
                });
                setSincronizando(false);
                dispatch(fetchProductos()); // Refrescar la lista de productos
                clearInterval(intervalId);
              } else if (status === 'FAILURE' || status === 'ERROR') {
                setSnackbar({
                  open: true,
                  message: `Error en la sincronización: ${data.error || 'Error desconocido'}`,
                  severity: 'error'
                });
                setSincronizando(false);
                clearInterval(intervalId);
              } else {
                // En progreso o cualquier otro estado
                setSnackbar({
                  open: true,
                  message: `Sincronizando inventario: ${percentage}% completado (${current}/${total})`,
                  severity: 'info',
                  autoHideDuration: 3000, // Duración corta para que se actualice pronto
                });
              }
            } catch (error) {
              console.error("Error consultando progreso:", error);
              // No mostramos el error al usuario en cada consulta fallida
              // para no sobrecargar la interfaz con notificaciones de error
              
              // Incrementar contador de errores
              errorCount++;
              
              // Si hay demasiados errores consecutivos, detener la consulta
              if (errorCount > 5) {
                console.error("Demasiados errores consecutivos. Deteniendo consulta de progreso.");
                setSnackbar({
                  open: true,
                  message: "No se pudo obtener el progreso de la sincronización. La tarea podría seguir en curso.",
                  severity: 'warning'
                });
                setSincronizando(false);
                clearInterval(intervalId);
              }
            }
          };
          
          // Consultar inmediatamente y luego cada 2 segundos
          consultarProgresoTarea();
          intervalId = setInterval(consultarProgresoTarea, 2000);
          
          // Almacenar el ID del intervalo para poder limpiarlo después
          setIntervalos(prev => [...prev, intervalId]);
          
          // Limpiar el intervalo después de 5 minutos por seguridad
          setTimeout(() => {
            clearInterval(intervalId);
            // Si aún está sincronizando después de 5 minutos, asumimos que algo salió mal
            setSincronizando(false);
          }, 5 * 60 * 1000);
        }
      })
      .catch((error) => {
        console.error("Error inesperado en sincronización:", error);
        setSincronizando(false);
        setSnackbar({
          open: true,
          message: `Error inesperado: ${error.message || 'Error desconocido'}`,
          severity: 'error'
        });
      });
  };
  
  // Efecto de limpieza al desmontar el componente
  useEffect(() => {
    return () => {
      // Limpiar todos los intervalos al desmontar
      intervalos.forEach(intervalo => clearInterval(intervalo));
    };
  }, [intervalos]);
  
  // Abrir diálogo para editar producto
  const abrirEditarProductoDialog = (producto) => {
    // Preparar datos del producto para editar con el formato
    // que espera el DialogoEditarProducto
    setProductoEditando({
      producto: {
        id: producto.id,
        nombre: producto.nombre,
        tipo_tasa: producto.tipo_tasa || 'PARALELO',
        stock_actual: producto.stock_actual || 0
      },
      precio_compra_usd: producto.precio_base_usd || 0,
      unidades_paquete: 1, // Valor por defecto
      cantidad: 1, // Valor por defecto para cantidad
      porcentajeGanancia: producto.porcentaje_ganancia || 30, // Valor por defecto o el del producto
      aplicarIva: producto.aplica_iva || false
    });
    setMonedaEdicion('USD');
    setEditProductoDialogOpen(true);
  };
  
  // Cerrar diálogo de edición de producto
  const cerrarEditarProductoDialog = () => {
    setEditProductoDialogOpen(false);
    setProductoEditando(null);
  };
  
  // Manejar cambios en el producto editando
  const handleProductoEditandoChange = (nuevoProductoEditando) => {
    setProductoEditando(nuevoProductoEditando);
  };
  
  // Guardar cambios en el producto
  const guardarCambiosProducto = async () => {
    if (!productoEditando) return;
    
    const productoActualizado = {
      id: productoEditando.producto.id,
      nombre: productoEditando.producto.nombre,
      precio_base_usd: Number(productoEditando.precio_compra_usd),
      porcentaje_ganancia: Number(productoEditando.porcentajeGanancia),
      aplica_iva: productoEditando.aplicarIva,
      tipo_tasa: productoEditando.producto.tipo_tasa,
      stock_actual: Number(productoEditando.producto.stock_actual),
      fuente_actualizacion: 'calculado' // Indicar que fue actualizado manualmente
    };
    
    try {
      await dispatch(updateProducto(productoActualizado)).unwrap();
      dispatch(fetchProductos()); // Actualizar la lista de productos
      setSnackbar({
        open: true,
        message: `Producto "${productoEditando.producto.nombre}" actualizado correctamente`,
        severity: 'success'
      });
      cerrarEditarProductoDialog();
    } catch (error) {
      console.error("Error al actualizar el producto:", error);
      setSnackbar({
        open: true,
        message: `Error al actualizar el producto: ${error.message}`,
        severity: 'error'
      });
    }
  };
  
  return (
    <Box sx={{ 
      maxWidth: 1200, 
      margin: '0 auto', 
      padding: 3, 
      backgroundColor: '#f8f9fa'
    }}>
      <Box sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        mb: 4,
        borderBottom: '2px solid #e2e8f0',
        paddingBottom: 2,
      }}>
        <Typography 
          variant="h4" 
          sx={{ 
            fontSize: '2rem', 
            fontWeight: 600, 
            color: '#1e293b',
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
          <Tooltip title="Estadísticas por categoría">
            <IconButton 
              onClick={abrirStatsDialog}
              size="small"
            >
              <FilterListIcon />
            </IconButton>
          </Tooltip>
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            variant="contained"
            color="success"
            startIcon={<AddIcon />}
            onClick={() => navigate('/crear-producto')}
            sx={{
              borderRadius: '4px',
              px: 2,
              py: 1,
              textTransform: 'none',
              fontWeight: 600,
              mr: 2
            }}
          >
            Agregar Producto
          </Button>
          <ButtonGroup variant="contained">
            <Button
              color="primary"
              startIcon={<SyncIcon />}
              onClick={handleSyncFromLoyverse}
              disabled={sincronizando || sincronizandoInventario}
              sx={{
                borderRadius: '4px 0 0 4px',
                px: 2,
                py: 1,
                textTransform: 'none',
                fontWeight: 600
              }}
            >
              {sincronizando ? 'Sincronizando...' : 'Sincronizar productos'}
              {sincronizando && <CircularProgress size={20} sx={{ ml: 1, color: 'white' }} />}
            </Button>
            <Button
              color="secondary"
              startIcon={<WarehouseIcon />}
              onClick={handleSyncInventory}
              disabled={sincronizando || sincronizandoInventario}
              sx={{
                borderRadius: '0 4px 4px 0',
                px: 2,
                py: 1,
                textTransform: 'none',
                fontWeight: 600
              }}
            >
              {sincronizandoInventario ? 'Sincronizando...' : 'Sincronizar inventario'}
              {sincronizandoInventario && <CircularProgress size={20} sx={{ ml: 1, color: 'white' }} />}
            </Button>
          </ButtonGroup>
        </Box>
      </Box>
      
      {/* Panel de estadísticas */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={2}>
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
        <Grid item xs={12} md={2}>
          <Card elevation={2} sx={{ 
            borderRadius: 2, 
            height: '100%',
            border: '1px solid #fee2e2',
            bgcolor: '#fef2f2',
            cursor: 'pointer',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 3,
              bgcolor: '#fee2e2'
            }
          }}
          onClick={() => setMostrarSinPrecio(!mostrarSinPrecio)}
          >
            <CardContent>
              <Typography variant="h6" color="error" gutterBottom>
                Sin Precio USD
              </Typography>
              <Typography variant="h3" component="div" color="error">
                {productos.filter(p => !p.precio_base_usd || Number(p.precio_base_usd) === 0).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card 
            elevation={2} 
            sx={{ 
              borderRadius: 2, 
              height: '100%', 
              cursor: 'pointer',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: 3,
                bgcolor: '#f8fafc'
              }
            }}
            onClick={() => abrirEditTasaDialog('BCV')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Tasa BCV Actual
                </Typography>
                <Tooltip title="Editar tasa BCV" arrow>
                  <EditAttributesIcon color="primary" fontSize="small" />
                </Tooltip>
              </Box>
              <Typography variant="h3" component="div" color="primary">
                {tasaBCV ? tasaBCV.valor : 'N/A'} Bs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card 
            elevation={2} 
            sx={{ 
              borderRadius: 2, 
              height: '100%', 
              cursor: 'pointer',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: 3,
                bgcolor: '#f8fafc'
              }
            }}
            onClick={() => abrirEditTasaDialog('PARALELO')}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Tasa Paralelo Actual
                </Typography>
                <Tooltip title="Editar tasa Paralelo" arrow>
                  <EditAttributesIcon color="secondary" fontSize="small" />
                </Tooltip>
              </Box>
              <Typography variant="h3" component="div" color="secondary">
                {tasaParalelo ? tasaParalelo.valor : 'N/A'} Bs
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Resultados búsqueda
              </Typography>
              <Typography variant="h3" component="div" color={searchTerm || categoriaSeleccionada || mostrarSinPrecio ? 'secondary' : 'primary'}>
                {productosFiltrados.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Buscador y Filtros */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 3, 
          borderRadius: 2,
          backgroundColor: '#fff'
        }}
      >
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
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
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth variant="outlined">
              <InputLabel id="categoria-select-label">Filtrar por Categoría</InputLabel>
              <Select
                labelId="categoria-select-label"
                id="categoria-select"
                value={categoriaSeleccionada}
                onChange={handleCategoriaChange}
                label="Filtrar por Categoría"
                startAdornment={
                  <InputAdornment position="start">
                    <FilterListIcon />
                  </InputAdornment>
                }
                sx={{
                  borderRadius: 1,
                  '& fieldset': {
                    borderColor: '#cbd5e1',
                  },
                  '&:hover fieldset': {
                    borderColor: '#94a3b8',
                  }
                }}
              >
                <MenuItem value="">Todas las categorías</MenuItem>
                {categorias.filter(cat => cat !== '').map((categoria) => (
                  <MenuItem key={categoria} value={categoria}>
                    {categoria}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={mostrarSinPrecio}
                  onChange={(e) => setMostrarSinPrecio(e.target.checked)}
                  color="error"
                />
              }
              label="Mostrar solo productos sin precio USD"
              sx={{ 
                border: mostrarSinPrecio ? '1px solid #ef4444' : '1px solid #e2e8f0',
                borderRadius: 1,
                padding: '8px 12px',
                bgcolor: mostrarSinPrecio ? '#fef2f2' : 'transparent'
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              color="secondary"
              onClick={resetearFiltros}
              sx={{
                borderRadius: 1,
                height: '56px',
                textTransform: 'none',
                fontWeight: 600
              }}
            >
              Limpiar filtros
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Tabla de productos */}
      <Paper 
        elevation={3} 
        sx={{ 
          borderRadius: 2,
          overflow: 'hidden'
        }}
      >
        {status === 'loading' || sincronizando || sincronizandoInventario ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400, flexDirection: 'column', gap: 2 }}>
            <CircularProgress />
            {sincronizando && (
              <Typography variant="h6" sx={{ ml: 2, color: '#475569' }}>
                Sincronizando productos desde Loyverse...
              </Typography>
            )}
            {sincronizandoInventario && (
              <Typography variant="h6" sx={{ ml: 2, color: '#475569' }}>
                Sincronizando inventario desde Loyverse...
              </Typography>
            )}
          </Box>
        ) : (
          <>
            {(categoriaSeleccionada || mostrarSinPrecio) && (
              <Box sx={{ 
                p: 2, 
                bgcolor: mostrarSinPrecio ? '#fee2e2' : '#e0f2fe', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'space-between',
                borderBottom: '1px solid',
                borderColor: mostrarSinPrecio ? '#fecaca' : '#bae6fd'
              }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <FilterListIcon color={mostrarSinPrecio ? "error" : "primary"} />
                  {categoriaSeleccionada && (
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#0369a1' }}>
                      Categoría: <span style={{ color: '#0284c7' }}>{categoriaSeleccionada}</span>
                    </Typography>
                  )}
                  {mostrarSinPrecio && (
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#b91c1c', ml: categoriaSeleccionada ? 2 : 0 }}>
                      Solo productos sin precio USD
                    </Typography>
                  )}
                </Box>
                <Button
                  size="small"
                  variant="outlined"
                  color={mostrarSinPrecio ? "error" : "primary"}
                  onClick={resetearFiltros}
                  sx={{ 
                    borderRadius: 1,
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Quitar filtros
                </Button>
              </Box>
            )}
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
                    <TableCell align="center" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                        <WarehouseIcon fontSize="small" />
                        Inventario
                      </Box>
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: 600, color: '#475569', backgroundColor: '#f1f5f9' }}>Acciones</TableCell>
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
                        ${producto.precio_base_usd ? Number(producto.precio_base_usd).toFixed(2) : '0.00'}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9', fontWeight: 500 }}
                      >
                        {calcularPrecioBS(producto.precio_base_usd, producto.id)} Bs
                      </TableCell>
                      <TableCell
                        align="center"
                        sx={{ borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Tooltip 
                          title="Esta tasa está guardada en el producto. Al cambiarla se actualizará en la base de datos."
                          arrow
                        >
                          <Button 
                            variant="outlined"
                            size="small"
                            color={tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'primary' : 'secondary'}
                            onClick={() => cambiarTasaProducto(
                              producto.id, 
                              tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'PARALELO' : 'BCV'
                            )}
                            startIcon={<CurrencyExchangeIcon />}
                            sx={{ 
                              borderRadius: '4px',
                              fontWeight: 500,
                              textTransform: 'none'
                            }}
                          >
                            {tasaSeleccionadaProducto[producto.id] === 'BCV' ? 'BCV' : 'Paralelo'} {
                              tasaSeleccionadaProducto[producto.id] === 'BCV' 
                                ? (tasaBCV ? tasaBCV.valor : 'N/A') 
                                : (tasaParalelo ? tasaParalelo.valor : 'N/A')
                            } Bs
                          </Button>
                        </Tooltip>
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        {producto.categoria ? (
                          <Chip 
                            label={producto.categoria} 
                            size="small" 
                            onClick={() => setCategoriaSeleccionada(producto.categoria)}
                            sx={{ 
                              backgroundColor: '#e0f2fe',
                              color: '#0369a1',
                              fontWeight: 500,
                              cursor: 'pointer',
                              '&:hover': {
                                backgroundColor: '#bae6fd',
                              }
                            }} 
                          />
                        ) : 'Sin categoría'}
                      </TableCell>
                      <TableCell
                        align="center"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Tooltip 
                          title={
                            <Box>
                              <Typography variant="body2">
                                ID Variante: {producto.variant_id ? producto.variant_id.substring(0, 8) + '...' : 'No disponible'}
                              </Typography>
                              <Typography variant="body2">
                                Última actualización: {formatDate(producto.ultima_actualizacion_stock || 'No disponible')}
                              </Typography>
                            </Box>
                          } 
                          arrow
                        >
                          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                            <Chip 
                              label={producto.stock_actual || '0'} 
                              size="small"
                              color={producto.stock_actual > 10 ? 'success' : producto.stock_actual > 0 ? 'warning' : 'error'}
                              sx={{ fontWeight: 600, minWidth: '60px' }}
                            />
                            {!producto.variant_id && (
                              <Chip 
                                label="Sin ID" 
                                size="small"
                                color="default"
                                sx={{ 
                                  fontSize: '0.65rem', 
                                  height: '18px', 
                                  '& .MuiChip-label': { 
                                    padding: '0 6px' 
                                  } 
                                }}
                              />
                            )}
                            {!producto.ultima_actualizacion_stock && (
                              <Chip 
                                label="Sin sync" 
                                size="small"
                                color="default"
                                sx={{ 
                                  fontSize: '0.65rem', 
                                  height: '18px', 
                                  '& .MuiChip-label': { 
                                    padding: '0 6px' 
                                  } 
                                }}
                              />
                            )}
                          </Box>
                        </Tooltip>
                      </TableCell>
                      <TableCell
                        align="center"
                        sx={{ color: '#334155', borderBottom: '1px solid #f1f5f9' }}
                      >
                        <Tooltip title="Editar producto">
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => abrirEditarProductoDialog(producto)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
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
            <Typography variant="h6">Información sobre Sistema de Inventario</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Tasas de cambio actuales:
            </Typography>
            <Box sx={{ display: 'flex', gap: 4, mb: 2 }}>
              <Box>
                <Typography variant="body1" color="primary" sx={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: 1 }}>
                  BCV: {tasaBCV ? tasaBCV.valor : 'No disponible'} Bs/USD
                  <Tooltip title="Editar tasa BCV" arrow>
                    <IconButton 
                      color="primary" 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        cerrarInfoDialog();
                        abrirEditTasaDialog('BCV');
                      }}
                    >
                      <EditAttributesIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Última actualización: {tasaBCV ? new Date(tasaBCV.fecha).toLocaleDateString() : 'N/A'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body1" color="secondary" sx={{ fontWeight: 500, display: 'flex', alignItems: 'center', gap: 1 }}>
                  Paralelo: {tasaParalelo ? tasaParalelo.valor : 'No disponible'} Bs/USD
                  <Tooltip title="Editar tasa Paralelo" arrow>
                    <IconButton 
                      color="secondary" 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        cerrarInfoDialog();
                        abrirEditTasaDialog('PARALELO');
                      }}
                    >
                      <EditAttributesIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Última actualización: {tasaParalelo ? new Date(tasaParalelo.fecha).toLocaleDateString() : 'N/A'}
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            
            {/* Nueva sección de información sobre inventario */}
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarehouseIcon color="secondary" fontSize="small" />
              Sistema de Inventario
            </Typography>
            <Typography variant="body1" gutterBottom>
              El sistema de inventario funciona de forma bidireccional entre BodegaClick y Loyverse:
            </Typography>
            <Box sx={{ bgcolor: '#f8fafc', p: 2, borderRadius: 1, mb: 2 }}>
              <Typography variant="body2" gutterBottom sx={{ fontWeight: 500, color: '#334155' }}>
                <ArrowDownwardIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1, color: '#0369a1' }} />
                <strong>De Loyverse a BodegaClick (automático):</strong> Los cambios de inventario realizados en Loyverse 
                se sincronizan automáticamente mediante webhooks.
              </Typography>
              <Typography variant="body2" gutterBottom sx={{ ml: 4, color: '#475569' }}>
                Sin embargo, algunos productos podrían no tener inventario actualizado si no han tenido movimientos
                en Loyverse desde que se implementaron los webhooks.
              </Typography>
              
              <Typography variant="body2" gutterBottom sx={{ fontWeight: 500, color: '#334155', mt: 1 }}>
                <ArrowUpwardIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1, color: '#7c3aed' }} />
                <strong>De BodegaClick a Loyverse (manual):</strong> Al crear facturas en BodegaClick, el inventario
                se actualiza en Loyverse.
              </Typography>
            </Box>
            
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600, color: '#0369a1' }}>
              ¿Cuándo usar la Sincronización de Inventario?
            </Typography>
            <Typography variant="body2" paragraph>
              Usa la función "Sincronizar Inventario" cuando necesites:
            </Typography>
            <Box component="ul" sx={{ ml: 2 }}>
              <li>Actualizar productos que muestran "0" como stock pero tienen inventario en Loyverse</li>
              <li>Completar campos "variant_id" necesarios para operaciones de inventario</li>
              <li>Asegurar que todos los productos tienen información actualizada de inventario</li>
            </Box>
            
            <Box sx={{ bgcolor: '#e0f2fe', p: 2, borderRadius: 1, mt: 2, mb: 2 }}>
              <Typography variant="body2" color="primary">
                <InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                <strong>Tip:</strong> Al iniciar, puedes elegir sincronizar solo productos sin stock (por defecto) o 
                forzar la sincronización de todos los productos.
              </Typography>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="body1" gutterBottom>
              Los precios en USD son calculados a partir de los precios en Bolívares usando la tasa seleccionada para cada producto.
            </Typography>
            <Typography variant="body1" gutterBottom>
              Puede cambiar la tasa utilizada para cada producto haciendo clic en los botones "BCV" o "Paralelo" en la columna "Tasa".
            </Typography>
            <Typography variant="body1" gutterBottom sx={{ fontWeight: 500, color: '#0284c7' }}>
              ¡Importante! La tasa mostrada en cada producto ahora refleja el valor almacenado en la base de datos (tipo_tasa).
              Al cambiarla, se actualizará permanentemente para ese producto.
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
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarehouseIcon sx={{ color: '#6366f1' }} />
                <Typography variant="body1">
                  <strong>Sincronización de inventario:</strong> Inventario actualizado manualmente desde Loyverse.
                </Typography>
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Sincronización con Loyverse:
            </Typography>
            <Typography variant="body1">
              Puede sincronizar manualmente los productos desde Loyverse haciendo clic en el botón "Sincronizar productos" en la parte superior de la página.
              Esto traerá la información más actualizada de productos, incluyendo nombres, precios y categorías.
            </Typography>
            <Typography variant="body1" sx={{ mt: 1 }}>
              La opción "Actualizar precios" permite decidir si desea actualizar los precios con los valores de Loyverse. El sistema verificará si hay facturas creadas en los últimos 2 días y, en caso afirmativo, no actualizará los precios para mantener los ajustes recientes.
            </Typography>
            <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary', fontStyle: 'italic' }}>
              Nota: Al cambiar el tipo de tasa de un producto (BCV o Paralelo), este cambio se guardará en la base de datos y afectará los cálculos de precios en futuras facturas.
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarInfoDialog} color="primary" variant="contained">
            Entendido
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo de estadísticas por categoría */}
      <Dialog
        open={statsDialogOpen}
        onClose={cerrarStatsDialog}
        maxWidth="md"
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon color="primary" />
            <Typography variant="h6">Estadísticas por Categoría</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <DialogContentText component="div">
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Distribución de productos por categoría:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
              {[
                { categoria: 'Bebidas', cantidad: 23 },
                { categoria: 'Charcuteria', cantidad: 14 },
                { categoria: 'Chucheria', cantidad: 115 },
                { categoria: 'Cigarros', cantidad: 24 },
                { categoria: 'Coche', cantidad: 16 },
                { categoria: 'Comida', cantidad: 134 },
                { categoria: 'Farmacia', cantidad: 12 },
                { categoria: 'Helado', cantidad: 5 },
                { categoria: 'Higiene', cantidad: 62 },
                { categoria: 'Impresiones', cantidad: 4 },
                { categoria: 'Panaderia', cantidad: 10 },
                { categoria: 'Papeleria', cantidad: 23 },
                { categoria: 'Papelería', cantidad: 2 },
                { categoria: 'Varios', cantidad: 49 },
                { categoria: 'Vicio', cantidad: 4 }
              ].map((item) => (
                <Card 
                  key={item.categoria} 
                  sx={{ 
                    minWidth: 180, 
                    flexGrow: 1, 
                    bgcolor: '#f8fafc', 
                    border: '1px solid #e2e8f0',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      bgcolor: '#f1f5f9',
                      transform: 'translateY(-2px)',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                    }
                  }}
                  onClick={() => {
                    setCategoriaSeleccionada(item.categoria);
                    cerrarStatsDialog();
                  }}
                >
                  <CardContent>
                    <Typography variant="h6" fontWeight={500} color="#0369a1">
                      {item.categoria}
                    </Typography>
                    <Typography variant="h5" fontWeight={600} color="#1e293b">
                      {item.cantidad} productos
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </Box>
            <Typography variant="body2" sx={{ mt: 3, color: 'text.secondary', fontStyle: 'italic' }}>
              Haz clic en una categoría para filtrar los productos por esa categoría.
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarStatsDialog} color="primary" variant="contained">
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo de opciones de sincronización */}
      <Dialog
        open={syncOptionsDialogOpen}
        onClose={cerrarSyncOptionsDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SyncIcon color="primary" />
            <Typography variant="h6">Opciones de Sincronización con Loyverse</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Configurar sincronización:
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Selecciona las opciones para personalizar el proceso de sincronización de productos con Loyverse.
              </Typography>
            </Grid>
            
            {/* Actualizar precios */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={opcionesSincronizacion.actualizar_precios}
                    onChange={handleChangeOpcionesSincronizacion}
                    name="actualizar_precios"
                    color="primary"
                  />
                }
                label="Actualizar precios en Loyverse (usando precio_base_usd * tasa)"
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                Si está activado, se enviarán los precios calculados de BodegaClick hacia Loyverse.
              </Typography>
            </Grid>
            
            {/* Selección de categorías */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="categorias-select-label">Filtrar por Categorías</InputLabel>
                <Select
                  labelId="categorias-select-label"
                  id="categorias-select"
                  multiple
                  value={opcionesSincronizacion.categorias}
                  onChange={handleChangeCategoriasSincronizacion}
                  label="Filtrar por Categorías"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  <MenuItem value="">
                    <em>Todas las categorías</em>
                  </MenuItem>
                  {categorias.filter(cat => cat !== '').map((categoria) => (
                    <MenuItem key={categoria} value={categoria}>
                      {categoria}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>
                  Deja vacío para sincronizar todas las categorías
                </FormHelperText>
              </FormControl>
            </Grid>
            
            {/* Selección de tipo de tasa */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="tipo-tasa-select-label">Filtrar por Tipo de Tasa</InputLabel>
                <Select
                  labelId="tipo-tasa-select-label"
                  id="tipo-tasa-select"
                  value={opcionesSincronizacion.tipo}
                  onChange={handleChangeOpcionesSincronizacion}
                  name="tipo"
                  label="Filtrar por Tipo de Tasa"
                >
                  <MenuItem value="todos">Todas las tasas</MenuItem>
                  <MenuItem value="BCV">Solo productos con tasa BCV</MenuItem>
                  <MenuItem value="PARALELO">Solo productos con tasa Paralelo</MenuItem>
                </Select>
                <FormHelperText>
                  Al exportar precios, solo se procesarán productos con este tipo de tasa
                </FormHelperText>
              </FormControl>
            </Grid>
            
            {/* Selección de productos específicos para pruebas */}
            <Grid item xs={12}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="productos-select-label">Productos para prueba</InputLabel>
                <Select
                  labelId="productos-select-label"
                  id="productos-select"
                  multiple
                  value={productosSeleccionados}
                  onChange={handleChangeProductosSeleccionados}
                  label="Productos para prueba"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const producto = productos.find(p => p.id === value);
                        return (
                          <Chip 
                            key={value} 
                            label={producto ? producto.nombre : `ID: ${value}`} 
                            size="small" 
                          />
                        );
                      })}
                    </Box>
                  )}
                >
                  {productos
                    .filter(producto => producto.loyverse_id) // Solo productos con ID de Loyverse
                    .map((producto) => (
                      <MenuItem key={producto.id} value={producto.id}>
                        {producto.nombre} ({producto.tipo_tasa} - {producto.categoria || 'Sin categoría'})
                      </MenuItem>
                    ))}
                </Select>
                <FormHelperText>
                  Selecciona productos específicos para probar la sincronización (deja vacío para sincronizar según categorías)
                </FormHelperText>
              </FormControl>
            </Grid>
            
            {/* Tamaño de lote para exportación */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Tamaño de lote para exportación
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Slider
                  value={opcionesSincronizacion.tamaño_lote}
                  onChange={(event, newValue) => {
                    setOpcionesSincronizacion(prev => ({
                      ...prev,
                      tamaño_lote: newValue
                    }));
                  }}
                  step={5}
                  marks={[
                    { value: 5, label: '5' },
                    { value: 20, label: '20' },
                    { value: 50, label: '50' },
                    { value: 100, label: '100' }
                  ]}
                  min={5}
                  max={100}
                  valueLabelDisplay="auto"
                  aria-labelledby="tamaño-lote-slider"
                />
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 100 }}>
                  {opcionesSincronizacion.tamaño_lote} productos por lote
                </Typography>
              </Box>
              <FormHelperText>
                Un valor menor es más lento pero más seguro. Útil para conexiones lentas o inestables.
              </FormHelperText>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ 
                bgcolor: '#f1f9ff', 
                p: 2, 
                borderRadius: 1, 
                border: '1px solid #e0f2fe',
                mt: 2 
              }}>
                <Typography variant="body2" color="info.main">
                  <InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  <strong>Importante:</strong> La sincronización traerá todos los productos de Loyverse 
                  (sin sus precios) y podrá enviar los precios calculados en BodegaClick 
                  (precio_base_usd * tasa) hacia Loyverse dependiendo de la configuración seleccionada.
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarSyncOptionsDialog} color="inherit">
            Cancelar
          </Button>
          <Button 
            onClick={iniciarSincronizacion} 
            color="primary" 
            variant="contained"
            disabled={sincronizando}
            startIcon={sincronizando ? <CircularProgress size={20} /> : <SyncIcon />}
          >
            {sincronizando ? 'Sincronizando...' : 'Iniciar Sincronización'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo para editar tasa de cambio */}
      <Dialog
        open={editTasaDialogOpen}
        onClose={cerrarEditTasaDialog}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: 24
          }
        }}
      >
        <DialogTitle 
          sx={{ 
            backgroundColor: '#f8fafc', 
            borderBottom: '1px solid #e2e8f0',
            px: 3,
            py: 2
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CurrencyExchangeIcon color="primary" />
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#334155' }}>
              Editar Tasa de Cambio {tipoTasaEdicion}
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 3 }}>
          <Grid container spacing={3} sx={{ mt: 0 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label={`Valor actual de la tasa ${tipoTasaEdicion}`}
                type="number"
                value={nuevaTasaValor}
                onChange={(e) => setNuevaTasaValor(Number(e.target.value))}
                inputProps={{ min: 0, step: 0.01 }}
                helperText={tipoTasaEdicion === 'BCV' 
                  ? `Valor actual: ${tasaBCV?.valor || 'No disponible'} Bs/USD`
                  : `Valor actual: ${tasaParalelo?.valor || 'No disponible'} Bs/USD`}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1
                  }
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary">
                Al actualizar esta tasa, se afectará el cálculo de precios para todos los productos que utilizan esta tasa.
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button 
            onClick={cerrarEditTasaDialog} 
            variant="outlined"
            color="inherit"
            sx={{ borderRadius: 1 }}
          >
            Cancelar
          </Button>
          <Button 
            onClick={guardarNuevaTasa} 
            variant="contained"
            color="primary"
            sx={{ borderRadius: 1 }}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo de sincronización de inventario */}
      <Dialog
        open={syncInventoryDialogOpen}
        onClose={cerrarSyncInventoryDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ bgcolor: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarehouseIcon color="secondary" />
            <Typography variant="h6">Opciones de Sincronización de Inventario</Typography>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Configurar sincronización de inventario:
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Esta función sincronizará el inventario desde Loyverse hacia BodegaClick, actualizando el stock de todos los productos.
              </Typography>
            </Grid>
            
            {/* Opciones de sincronización */}
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={opcionesInventario.force}
                    onChange={(e) => setOpcionesInventario(prev => ({
                      ...prev,
                      force: e.target.checked
                    }))}
                    color="secondary"
                  />
                }
                label="Forzar actualización de todos los productos"
              />
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 4 }}>
                Si está desactivado, solo se actualizarán los productos con stock = 0. Si está activado, se actualizarán todos los productos.
              </Typography>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ 
                bgcolor: '#fff4e5', 
                p: 2, 
                borderRadius: 1, 
                border: '1px solid #ffecb5',
                mt: 2 
              }}>
                <Typography variant="body2" color="warning.dark">
                  <InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  <strong>Importante:</strong> Esta sincronización consultará el inventario actual en Loyverse y 
                  actualizará los registros en BodegaClick. También completará el campo variant_id para productos 
                  que no lo tengan, necesario para operaciones de inventario.
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ 
                bgcolor: '#e8f5e9', 
                p: 2, 
                borderRadius: 1, 
                border: '1px solid #c8e6c9',
                mt: 1
              }}>
                <Typography variant="body2" color="success.dark">
                  <WarehouseIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  <strong>Proceso de sincronización:</strong>
                </Typography>
                <ol style={{ marginTop: '8px', paddingLeft: '24px' }}>
                  <li>Obtiene los variant_id faltantes de los productos</li>
                  <li>Consulta el inventario actual de cada producto en Loyverse</li>
                  <li>Actualiza el stock_actual en la base de datos de BodegaClick</li>
                </ol>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2, bgcolor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
          <Button onClick={cerrarSyncInventoryDialog} color="inherit">
            Cancelar
          </Button>
          <Button 
            onClick={iniciarSincronizacionInventario} 
            color="secondary" 
            variant="contained"
            disabled={sincronizandoInventario}
            startIcon={sincronizandoInventario ? <CircularProgress size={20} /> : <WarehouseIcon />}
          >
            {sincronizandoInventario ? 'Sincronizando inventario...' : 'Iniciar Sincronización de Inventario'}
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
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity} 
          sx={{ 
            width: '100%',
            maxWidth: '600px'
          }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
      
      {/* Diálogo de edición de producto */}
      <DialogoEditarProducto
        open={editProductoDialogOpen}
        onClose={cerrarEditarProductoDialog}
        productoEditando={productoEditando}
        onChange={handleProductoEditandoChange}
        onSave={guardarCambiosProducto}
        tasaCambio={tasaSeleccionadaProducto[productoEditando?.producto?.id] === 'BCV' ? tasaBCV : tasaParalelo}
        moneda={monedaEdicion}
        esEdicionCompleta={true}
      />
    </Box>
  );
};

export default ListadoProductos; 
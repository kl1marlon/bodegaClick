// Función para manejar la sincronización del inventario
const handleSyncInventory = async (force = false) => {
  setLoading(true);
  setError(null);
  setSyncMessage('Iniciando sincronización del inventario...');

  try {
    const result = await dispatch(syncInventory({ force })).unwrap();
    
    if (result.success) {
      setSyncMessage(`Tarea de sincronización iniciada correctamente. ID: ${result.task_id}`);
      
      // Refrescar los productos después de 3 segundos
      setTimeout(() => {
        dispatch(fetchProductos());
        setSyncMessage('Productos actualizados desde el servidor.');
      }, 3000);
    } else {
      setSyncMessage('Error en la sincronización: ' + (result.error || 'Detalles no disponibles'));
      setError(result.error || 'Error desconocido en la sincronización');
    }
  } catch (err) {
    console.error('Error en la sincronización de inventario:', err);
    setSyncMessage('Error en la sincronización de inventario');
    setError(err);
  } finally {
    setLoading(false);
  }
}; 
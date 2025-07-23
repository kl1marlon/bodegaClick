import React, { useState, useEffect } from 'react';

const SyncPricesModal = ({ isOpen, onClose }) => {
    const [currentStep, setCurrentStep] = useState(1);
    const [tasas, setTasas] = useState({ bcv: '', paralelo: '' });
    const [taskStatus, setTaskStatus] = useState({
        step1: { taskId: null, status: 'idle', result: null },
        step2: { taskId: null, status: 'idle', result: null },
        step3: { taskId: null, status: 'idle', result: null },
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isOpen) {
            fetch('/api/facturacion/tasas-actuales/')
                .then(response => response.json())
                .then(data => setTasas(data))
                .catch(err => setError('Error al cargar las tasas actuales.'));
        }
    }, [isOpen]);

    const handleRecalculatePrices = () => {
        setIsLoading(true);
        setError('');
        fetch('/api/facturacion/recalcular-precios-base/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Añadir headers de autenticación si son necesarios
            },
            body: JSON.stringify(tasas),
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                setTaskStatus(prev => ({ ...prev, step1: { ...prev.step1, taskId: data.task_id, status: 'polling' } }));
            } else {
                setError(data.error || 'Error al iniciar la tarea.');
            }
        })
        .catch(err => setError('Error de red al recalcular precios.'))
        .finally(() => setIsLoading(false));
    };

    const handleCheckSync = () => {
        setIsLoading(true);
        setError('');
        fetch('/api/facturacion/loyverse/iniciar-sincronizacion/?check_only=true', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                setTaskStatus(prev => ({ ...prev, step2: { ...prev.step2, taskId: data.task_id, status: 'polling' } }));
            } else {
                setError(data.error || 'Error al iniciar la verificación.');
            }
        })
        .catch(err => setError('Error de red al verificar la sincronización.'))
        .finally(() => setIsLoading(false));
    };

    const handleRealSync = () => {
        setIsLoading(true);
        setError('');
        fetch('/api/facturacion/loyverse/iniciar-sincronizacion/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(response => response.json())
        .then(data => {
            if (data.task_id) {
                setTaskStatus(prev => ({ ...prev, step3: { ...prev.step3, taskId: data.task_id, status: 'polling' } }));
            } else {
                setError(data.error || 'Error al iniciar la sincronización real.');
            }
        })
        .catch(err => setError('Error de red al realizar la sincronización.'))
        .finally(() => setIsLoading(false));
    };

    useEffect(() => {
        const pollTask = (step) => {
            const interval = setInterval(() => {
                fetch(`/api/facturacion/tasks/status/${taskStatus[step].taskId}/`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'SUCCESS') {
                            clearInterval(interval);
                            setTaskStatus(prev => ({ ...prev, [step]: { ...prev[step], status: 'completed', result: data.result } }));
                            if (step === 'step1') setCurrentStep(2);
                            if (step === 'step2') setCurrentStep(3);
                        } else if (data.status === 'FAILURE') {
                            clearInterval(interval);
                            setError(`Error en la tarea del paso ${step.slice(-1)}: ${data.result}`);
                            setTaskStatus(prev => ({ ...prev, [step]: { ...prev[step], status: 'failed' } }));
                        }
                    })
                    .catch(err => {
                        clearInterval(interval);
                        setError('Error de red al consultar el estado de la tarea.');
                    });
            }, 4000);
            return () => clearInterval(interval);
        };

        if (taskStatus.step1.status === 'polling') pollTask('step1');
        if (taskStatus.step2.status === 'polling') pollTask('step2');
        if (taskStatus.step3.status === 'polling') pollTask('step3');

    }, [taskStatus]);

    if (!isOpen) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <h2>Sincronización de Precios</h2>
                {error && <p className="error">{error}</p>}

                {/* Paso 1 */}
                <div className={`step ${currentStep === 1 ? 'active' : ''}`}>
                    <h3>Paso 1: Actualizar Tasas en el Sistema</h3>
                    <input type="text" value={tasas.bcv} onChange={e => setTasas({ ...tasas, bcv: e.target.value })} placeholder="Tasa BCV" />
                    <input type="text" value={tasas.paralelo} onChange={e => setTasas({ ...tasas, paralelo: e.target.value })} placeholder="Tasa Paralelo" />
                    <button onClick={handleRecalculatePrices} disabled={isLoading || taskStatus.step1.status === 'polling'}>
                        {taskStatus.step1.status === 'polling' ? 'Recalculando...' : 'Recalcular Precios'}
                    </button>
                    {taskStatus.step1.status === 'completed' && <p>Recálculo completado: {JSON.stringify(taskStatus.step1.result)}</p>}
                </div>

                {/* Paso 2 */}
                <div className={`step ${currentStep === 2 ? 'active' : ''}`}>
                    <h3>Paso 2: Verificar Cambios con Loyverse (Modo Seguro)</h3>
                    <button onClick={handleCheckSync} disabled={isLoading || taskStatus.step2.status === 'polling' || currentStep !== 2}>
                        {taskStatus.step2.status === 'polling' ? 'Verificando...' : 'Iniciar Verificación'}
                    </button>
                    {taskStatus.step2.status === 'completed' && <p>Verificación completada: {JSON.stringify(taskStatus.step2.result)}</p>}
                </div>

                {/* Paso 3 */}
                <div className={`step ${currentStep === 3 ? 'active' : ''}`}>
                    <h3>Paso 3: Ejecutar Sincronización Real</h3>
                    <button onClick={handleRealSync} disabled={isLoading || taskStatus.step3.status === 'polling' || currentStep !== 3} className="danger-button">
                        {taskStatus.step3.status === 'polling' ? 'Sincronizando...' : 'Confirmar y Sincronizar'}
                    </button>
                    {taskStatus.step3.status === 'completed' && <p>Sincronización completada: {JSON.stringify(taskStatus.step3.result)}</p>}
                </div>

                <button onClick={onClose} className="close-button">Cerrar</button>
            </div>
        </div>
    );
};

export default SyncPricesModal;

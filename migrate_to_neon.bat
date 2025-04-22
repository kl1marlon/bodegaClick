@echo off
echo Migracion de datos de Railway a Neon
echo ===================================

REM Configurar variables de entorno
set PGPASSWORD=Bmw$2017
set RAILWAY_DB_URL=postgresql://postgres:Bmw$2017@db.ivwfdscqwzeszciiepll.supabase.co:5432/postgres
set NEON_DB_URL=postgresql://bodegaclicktest_owner:npg_prtXbWu34dPR@ep-floral-surf-a4m7e3ws-pooler.us-east-1.aws.neon.tech/bodegaclicktest?sslmode=require

REM Crear directorio para backups si no existe
if not exist "backups" mkdir backups

REM Generar nombre de archivo con timestamp
set timestamp=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
set BACKUP_FILE=backups\railway_backup_%timestamp%.sql

echo Exportando datos de Railway a %BACKUP_FILE%...
pg_dump -h db.ivwfdscqwzeszciiepll.supabase.co -U postgres -d postgres -f %BACKUP_FILE%

if %ERRORLEVEL% NEQ 0 (
    echo Error al exportar datos de Railway.
    exit /b %ERRORLEVEL%
)

echo Datos exportados exitosamente.
echo Importando datos a Neon...

psql %NEON_DB_URL% -f %BACKUP_FILE%

if %ERRORLEVEL% NEQ 0 (
    echo Error al importar datos a Neon.
    exit /b %ERRORLEVEL%
)

echo Migracion completada exitosamente!
echo El backup se guardo en: %BACKUP_FILE%

pause

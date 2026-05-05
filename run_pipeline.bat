@echo off
setlocal

REM Set project root
set PROJECT_DIR=C:\Leads automation\leads-automation

REM Go to project directory
cd /d "%PROJECT_DIR%"

REM Activate virtual environment
call "%PROJECT_DIR%\venv\Scripts\activate.bat"

REM Retry once if it fails
python -m master_pipeline.master_pipeline >> "%PROJECT_DIR%\logs\pipeline.log" 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Retrying... >> "%PROJECT_DIR%\logs\pipeline.log"
    python -m master_pipeline.master_pipeline >> "%PROJECT_DIR%\logs\pipeline.log" 2>&1
)

endlocal
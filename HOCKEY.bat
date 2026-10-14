@echo off
title HOCKEY DE AIRE
cd /d "%~dp0"

echo.
echo   ============================================
echo         H O C K E Y   D E   A I R E
echo   ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo   [X] No se encontro Python en este equipo.
    echo.
    echo   Descargalo de https://www.python.org/downloads/
    echo   During installation, tick "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

python -c "import pygame" >nul 2>nul
if errorlevel 1 (
    echo   Falta pygame. Instalando...
    echo.
    python -m pip install --disable-pip-version-check pygame-ce
    echo.
    python -c "import pygame" >nul 2>nul
    if errorlevel 1 (
        echo   [X] No se pudo instalar pygame.
        echo   Prueba a mano:  python -m pip install pygame-ce
        echo.
        pause
        exit /b 1
    )
)

python main_hockey.py %*

if errorlevel 1 (
    echo.
    echo   El juego se cerro con un error.
    echo.
    pause
)
endlocal

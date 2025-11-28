@echo off
echo Iniciando servicos do AutoFX...

:: Inicia o servidor backend
echo Iniciando npm run server...
start "AutoFX_Backend" /MIN cmd /c "npm run server > server.log 2>&1"

:: Inicia o servidor frontend (Vite)
echo Iniciando npm run dev...
start "AutoFX_Frontend" /MIN cmd /c "npm run dev > dev.log 2>&1"

echo -----------------------------------
echo Servicos rodando em background (janelas minimizadas).
echo Logs disponiveis em: server.log e dev.log
echo Para parar, execute: stop.bat
echo -----------------------------------

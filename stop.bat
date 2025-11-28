@echo off
echo Parando servicos do AutoFX...

:: Encerra processos pelo titulo da janela definido no start.bat
echo Encerrando Backend...
taskkill /FI "WINDOWTITLE eq AutoFX_Backend" /T /F >nul 2>&1

echo Encerrando Frontend...
taskkill /FI "WINDOWTITLE eq AutoFX_Frontend" /T /F >nul 2>&1

echo Servicos parados.

#!/bin/bash

echo "Iniciando serviços do AutoFX..."

# Inicia o servidor backend
echo "Iniciando npm run server..."
npm run server > server.log 2>&1 &
SERVER_PID=$!
echo "Server iniciado com PID: $SERVER_PID"

# Inicia o servidor frontend (Vite)
echo "Iniciando npm run dev..."
npm run dev > dev.log 2>&1 &
DEV_PID=$!
echo "Dev iniciado com PID: $DEV_PID"

# Salva os PIDs
echo "$SERVER_PID" > .pids
echo "$DEV_PID" >> .pids

echo "-----------------------------------"
echo "Serviços rodando em background."
echo "Logs disponíveis em: server.log e dev.log"
echo "Para parar, execute: ./stop.sh"
echo "-----------------------------------"

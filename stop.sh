#!/bin/bash

echo "Parando serviços do AutoFX..."

if [ -f .pids ]; then
    while read PID; do
        if [ -n "$PID" ]; then
            echo "Encerrando processo $PID..."
            # Envia sinal de terminação para o processo
            kill $PID 2>/dev/null
            
            # Tenta encerrar processos filhos imediatos (útil para npm scripts)
            pkill -P $PID 2>/dev/null
        fi
    done < .pids
    
    # Remove o arquivo de PIDs
    rm .pids
    echo "Processos encerrados via PID."
else
    echo "Arquivo .pids não encontrado."
fi

# Limpeza de segurança (Fallback)
# Garante que não sobraram processos órfãos comuns deste projeto
echo "Verificando processos remanescentes..."
pkill -f "node server.js" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo "Serviços parados."

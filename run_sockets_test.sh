#!/bin/bash
# Script para facilitar teste de sockets distribuído

echo ""
echo "================================================================================"
echo "INICIANDO SERVIDORES DE SOCKETS"
echo "================================================================================"
echo ""
echo "Abrindo 5 terminais para:"
echo "  - 1 Master"
echo "  - 4 Workers"
echo ""
read -p "Pressione Enter para começar..."

echo ""
echo "[1/5] Iniciando Master..."
python3 distribuido_sockets.py master &
sleep 2

echo "[2/5] Iniciando Worker 0..."
python3 distribuido_sockets.py worker 0 &
sleep 1

echo "[3/5] Iniciando Worker 1..."
python3 distribuido_sockets.py worker 1 &
sleep 1

echo "[4/5] Iniciando Worker 2..."
python3 distribuido_sockets.py worker 2 &
sleep 1

echo "[5/5] Iniciando Worker 3..."
python3 distribuido_sockets.py worker 3 &

echo ""
echo "================================================================================"
echo "Todos os processos foram iniciados!"
echo "================================================================================"
echo ""
read -p "Pressione Enter para sair..."

# Clean up background processes on exit
trap 'kill $(jobs -p) 2>/dev/null' EXIT
wait

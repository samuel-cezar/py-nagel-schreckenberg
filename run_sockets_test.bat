@echo off
REM Script para facilitar teste de sockets distribuído

setlocal

echo.
echo ================================================================================
echo INICIANDO SERVIDORES DE SOCKETS
echo ================================================================================
echo.
echo Abrindo 5 terminais para:
echo  - 1 Master
echo  - 4 Workers
echo.
echo Pressione Enter para começar...
pause

echo.
echo [1/5] Iniciando Master...
start cmd /k "python distribuido_sockets.py master"
timeout /t 2

echo [2/5] Iniciando Worker 0...
start cmd /k "python distribuido_sockets.py worker 0"
timeout /t 1

echo [3/5] Iniciando Worker 1...
start cmd /k "python distribuido_sockets.py worker 1"
timeout /t 1

echo [4/5] Iniciando Worker 2...
start cmd /k "python distribuido_sockets.py worker 2"
timeout /t 1

echo [5/5] Iniciando Worker 3...
start cmd /k "python distribuido_sockets.py worker 3"

echo.
echo ================================================================================
echo Todos os processos foram iniciados!
echo ================================================================================
echo.
pause

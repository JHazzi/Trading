#!/bin/bash
echo "[*] Levantando Ecosistema Quant..."

# Activar el entorno virtual
source venv/bin/activate

# Lanzar los procesos en segundo plano enviando el output a archivos .log
python daemon_precios.py > data/precios.log 2>&1 &
PID_PRECIOS=$!

python daemon_noticias.py > data/noticias.log 2>&1 &
PID_NOTICIAS=$!

python daemon_cerebro.py > data/cerebro.log 2>&1 &
PID_CEREBRO=$!

python daemon_paper_trading.py > data/trading.log 2>&1 &
PID_TRADING=$!
echo "Daemon Paper Trading iniciado con PID: $PID_TRADING"

python daemon_macro.py > data/macro.log 2>&1 &
PID_MACRO=$!
echo "Daemon Macro iniciado con PID: $PID_MACRO"

echo "[+] Daemons iniciados con PIDs: Precios($PID_PRECIOS), Noticias($PID_NOTICIAS), Cerebro($PID_CEREBRO)"
echo "[*] Usa 'tail -f data/*.log' para ver la actividad en tiempo real."
#!/usr/bin/env bash

# Patrón para identificar los procesos
PATTERN="daemon_"

echo "[*] Buscando daemons activos..."

# Obtener PIDs excluyendo el propio script
PIDS=$(pgrep -f "$PATTERN" | grep -v "$$")

if [ -z "$PIDS" ]; then
    echo "[!] No se encontraron procesos activos con el patron '$PATTERN'."
    exit 0
fi

echo "[*] Daemons detectados: $(echo $PIDS | tr '\n' ' ')"
echo "[*] Enviando senal de cierre limpio (SIGTERM)..."

kill $PIDS 2>/dev/null

# Esperar hasta 5 segundos para que liberen memoria VRAM y conexiones
for i in {1..5}; do
    REMAINING=$(pgrep -f "$PATTERN" | grep -v "$$")
    if [ -z "$REMAINING" ]; then
        break
    fi
    sleep 1
done

# Forzar cierre si queda algun proceso colgado
REMAINING=$(pgrep -f "$PATTERN" | grep -v "$$")
if [ -n "$REMAINING" ]; then
    echo "[!] Procesos persistentes detectados. Forzando cierre (SIGKILL)..."
    kill -9 $REMAINING 2>/dev/null
    sleep 1
fi

echo "[+] Todos los daemons fueron detenidos correctamente."

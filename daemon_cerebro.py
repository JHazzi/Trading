import time
import signal
import sys
import json
from datetime import datetime

# Módulos del ciclo cognitivo
from filtro_relevancia import procesar_relevancia
from agrupacion_eventos import agrupar_ecos_financieros
from extractor_relaciones import extraer_aristas_semanticas
from procesar_sentimiento import procesar_noticias_pendientes
from motor_inferencia import evaluar_impacto_noticias

CONFIG_PATH = "config.json"
ejecutando = True

def cargar_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def cierre_elegante(sig, frame):
    global ejecutando
    print("\n[!] Señal de apagado recibida. Preparando cierre del Cerebro...")
    ejecutando = False

signal.signal(signal.SIGINT, cierre_elegante)
signal.signal(signal.SIGTERM, cierre_elegante)

def ciclo_cognitivo():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo cognitivo maestro...")
    try:
        procesadas = procesar_relevancia()
        agrupar_ecos_financieros()
        extraer_aristas_semanticas()
        procesar_noticias_pendientes()
        evaluar_impacto_noticias()
    except Exception as e:
        print(f"[!] Error en el ciclo cognitivo: {e}")
        
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo cognitivo completado.")

if __name__ == "__main__":
    print("[*] Arrancando Sistema Nervioso Central (Daemon Cerebro)")
    
    while ejecutando:
        # 1. Leemos la configuración dinámicamente en cada ciclo
        config = cargar_config()
        intervalo = config["intervalos_segundos"]["cerebro"]
        
        # 2. Ejecutamos el ciclo
        ciclo_cognitivo()
        
        # 3. Esperamos el tiempo dictado por el JSON
        segundos_esperados = 0
        while segundos_esperados < intervalo and ejecutando:
            time.sleep(1)
            segundos_esperados += 1
            
    print("[*] Cerebro apagado de forma segura.")
    sys.exit(0)
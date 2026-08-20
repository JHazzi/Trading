import time
import signal
import sys
from datetime import datetime
from filtro_relevancia import procesar_relevancia
from procesar_sentimiento import procesar_noticias_pendientes
from motor_inferencia import evaluar_impacto_noticias

INTERVALO_ESPERA = 900  # 15 minutos en segundos
ejecutando = True

def cierre_elegante(sig, frame):
    global ejecutando
    print("\n[!] Señal de apagado recibida. Preparando cierre del Cerebro...")
    ejecutando = False

signal.signal(signal.SIGINT, cierre_elegante)
signal.signal(signal.SIGTERM, cierre_elegante)

def ciclo_cognitivo():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo cognitivo...")
    
    # FASE 0: Criba de Relevancia (Limpieza de Basura)
    try:
        procesadas_relevancia = procesar_relevancia()
        if procesadas_relevancia > 0:
            print(f"[*] Filtro Anti-Ruido: {procesadas_relevancia} noticias puntuadas (0.0 a 1.0).")
    except Exception as e:
        print(f"[!] Error en el filtro de relevancia: {e}")

    # FASE 1: NLP Pipeline (Sentimiento con FinBERT)
    try:
        procesar_noticias_pendientes()
    except Exception as e:
        print(f"[!] Error en el pipeline NLP: {e}")
        
    # FASE 2: Inferencia (Mapeo de Impacto y Grafo de Contagio)
    try:
        evaluar_impacto_noticias()
    except Exception as e:
        print(f"[!] Error en el motor de correlación: {e}")
        
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo cognitivo completado.")

if __name__ == "__main__":
    print("[*] Arrancando Motor de Inferencia (Daemon Cerebro) - Presiona Ctrl+C para detener")
    
    while ejecutando:
        ciclo_cognitivo()
        
        segundos_esperados = 0
        while segundos_esperados < INTERVALO_ESPERA and ejecutando:
            time.sleep(1)
            segundos_esperados += 1
            
    print("[*] Cerebro apagado de forma segura.")
    sys.exit(0)
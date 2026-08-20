import time
import signal
import sys
from datetime import datetime

# Módulos del ciclo cognitivo
from filtro_relevancia import procesar_relevancia
from agrupacion_eventos import agrupar_ecos_financieros
from extractor_relaciones import extraer_aristas_semanticas
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
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo cognitivo maestro...")
    
    # FASE 1: Criba de Relevancia (Zero-Shot Classification)
    try:
        print("  -> Fase 1: Puntuación de Relevancia (Zero-Shot)...")
        procesadas = procesar_relevancia()
    except Exception as e:
        print(f"[!] Error en Fase 1: {e}")

    # FASE 2: Clustering Temporal (Deduplicación Semántica)
    try:
        print("  -> Fase 2: Agrupación de Eventos y Decaimiento Temporal...")
        agrupar_ecos_financieros()
    except Exception as e:
        print(f"[!] Error en Fase 2: {e}")
        
    # FASE 3: Topología de Mercado (Extracción de Verbos para el Grafo)
    try:
        print("  -> Fase 3: Extracción de Relaciones Semánticas...")
        extraer_aristas_semanticas()
    except Exception as e:
        print(f"[!] Error en Fase 3: {e}")

    # FASE 4: NLP Pipeline (Sentimiento con FinBERT)
    try:
        print("  -> Fase 4: Análisis de Sentimiento Direccional...")
        procesar_noticias_pendientes()
    except Exception as e:
        print(f"[!] Error en Fase 4: {e}")
        
    # FASE 5: Inferencia (Mapeo de Impacto y Correlaciones)
    try:
        print("  -> Fase 5: Motor de Inferencia y Cálculo MFE...")
        evaluar_impacto_noticias()
    except Exception as e:
        print(f"[!] Error en Fase 5: {e}")
        
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo cognitivo completado exitosamente.")

if __name__ == "__main__":
    print("[*] Arrancando Sistema Nervioso Central (Daemon Cerebro) - Presiona Ctrl+C para detener")
    
    while ejecutando:
        ciclo_cognitivo()
        
        segundos_esperados = 0
        # Bucle de espera interrumpible
        while segundos_esperados < INTERVALO_ESPERA and ejecutando:
            time.sleep(1)
            segundos_esperados += 1
            
    print("[*] Cerebro apagado de forma segura.")
    sys.exit(0)
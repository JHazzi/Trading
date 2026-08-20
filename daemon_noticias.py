import hashlib
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
import yfinance as yf
import random

DB_PATH = "data/market_data.db"
INTERVALO_ESPERA = 900  # 15 minutos en segundos

ejecutando = True


def cierre_elegante(sig, frame):
    """Manejador de señales para un graceful shutdown."""
    global ejecutando
    print(
        "\n[!] Señal de apagado recibida (SIGINT/SIGTERM). Preparando cierre..."
    )
    ejecutando = False


signal.signal(signal.SIGINT, cierre_elegante)
signal.signal(signal.SIGTERM, cierre_elegante)


def obtener_tickers_activos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM universo_tickers WHERE activo = 1")
    tickers = [fila[0] for fila in cursor.fetchall()]
    conn.close()
    return tickers


def procesar_noticia_y_relaciones(n: dict, ticker_origen: str):
    """Actualizado para capturar co-ocurrencias orgánicas."""
    item = n.get("content", n)

    # 1. Extraer Link
    link = ""
    if "canonicalUrl" in item and isinstance(item["canonicalUrl"], dict):
        link = item["canonicalUrl"].get("url", "")
    elif "clickThroughUrl" in item and isinstance(
        item["clickThroughUrl"], dict
    ):
        link = item["clickThroughUrl"].get("url", "")
    else:
        link = item.get("link", "")

    if not link:
        return None

    # 2. Extraer Título
    titulo = item.get("title", "Sin título")

    # 3. Extraer Fuente
    if "provider" in item and isinstance(item["provider"], dict):
        fuente = item["provider"].get("displayName", "Desconocido")
    else:
        fuente = item.get("publisher", "Desconocido")

    resumen = item.get("summary", "")
    if not resumen:
        # Fallback por si la API usa otra llave temporalmente
        resumen = item.get("snippet", "")

    # 4. Extraer Fecha
    if "pubDate" in item:
        try:
            dt = datetime.fromisoformat(item["pubDate"].replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    elif "providerPublishTime" in item:
        dt = datetime.fromtimestamp(
            item["providerPublishTime"], tz=timezone.utc
        )
    else:
        dt = datetime.now(timezone.utc)

    id_noticia = hashlib.md5(link.encode()).hexdigest()
    # Extraemos relaciones orgánicas para el Grafo
    relacionados = item.get("relatedTickers", [])
    relaciones_validas = [t for t in relacionados if t != ticker_origen]

    # Devolvemos también el resumen
    return (id_noticia, dt.isoformat(), titulo, fuente, resumen, relaciones_validas)


def ciclo_ingesta():
    tickers = obtener_tickers_activos()
    if not tickers: return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    total_nuevas = 0
    
    LOTE_SIZE = 505 
    
    print(f"[*] Iniciando ingesta en lotes para {len(tickers)} activos...")
    
    for i in range(0, len(tickers), LOTE_SIZE):
        lote = tickers[i:i+LOTE_SIZE]
        
        for ticker in lote:
            try:
                noticias = yf.Ticker(ticker).news
                if not noticias: continue
                
                for n in noticias:
                    datos = procesar_noticia_y_relaciones(n, ticker)
                    if not datos: continue
                    id_noticia, dt_str, titulo, fuente, resumen, relaciones = datos
                    
                    try:
                        # Agregamos la columna resumen
                        cursor.execute('''INSERT INTO noticias (id, ticker, timestamp, titulo, fuente, resumen)
                                        VALUES (?, ?, ?, ?, ?, ?)''', 
                                    (id_noticia, ticker, dt_str, titulo, fuente, resumen))
                        total_nuevas += 1
                        
                        # Poblar el grafo orgánico (Upsert de relaciones)
                        for destino in relaciones:
                            cursor.execute('''
                                INSERT INTO relaciones_organicas (origen, destino, peso, ultima_actualizacion)
                                VALUES (?, ?, 1, ?)
                                ON CONFLICT(origen, destino) DO UPDATE SET 
                                peso = peso + 1, ultima_actualizacion = excluded.ultima_actualizacion
                            ''', (ticker, destino, dt_str))
                            
                    except sqlite3.IntegrityError:
                        pass # Ya procesada
                        
            except Exception as e:
                print(e)
                pass # Manejo silencioso para no romper el bucle
                
            # Throttling intra-lote: Pausa aleatoria entre 0.5 y 1.5 segundos por cada ticker
            time.sleep(random.uniform(0.01, 0.02))
            
        # Throttling inter-lote: Descanso de 10 segundos al terminar un lote
        print(f"    [+] Lote completado. Esperando para no saturar API...")
        conn.commit()
        time.sleep(1)

    conn.close()
    print(f"[*] Ciclo finalizado: {total_nuevas} noticias indexadas.")


if __name__ == "__main__":
    print("[*] Arrancando Daemon de Noticias (Presiona Ctrl+C para detener)")

    while ejecutando:
        ciclo_ingesta()

        segundos_esperados = 0
        while segundos_esperados < INTERVALO_ESPERA and ejecutando:
            time.sleep(1)
            segundos_esperados += 1

    print("[*] Daemon detenido de forma segura. Base de datos intacta.")
    sys.exit(0)
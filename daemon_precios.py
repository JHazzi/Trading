import sqlite3
import yfinance as yf
import signal
import sys
import time
import random
import pandas as pd
import json
from datetime import datetime, timedelta, timezone

DB_PATH = "data/market_data.db"
CONFIG_PATH = "config.json"
#INTERVALO_ESPERA = 30  # 5 minutos en segundos

ejecutando = True

def cargar_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def cierre_elegante(sig, frame):
    """Garantiza un Cierre Elegante sin corromper SQLite."""
    global ejecutando
    print("\n[!] Señal de apagado recibida (SIGINT/SIGTERM). Preparando cierre del daemon de precios...")
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

def obtener_ultimo_timestamp(ticker: str) -> datetime:
    """Implementa la lógica base para el Relleno de Huecos (Gap Filling)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(timestamp) FROM precios WHERE ticker = ?", (ticker,))
    resultado = cursor.fetchone()[0]
    conn.close()
    
    if resultado:
        return datetime.fromisoformat(resultado).replace(tzinfo=timezone.utc)
    else:
        return datetime.now(timezone.utc) - timedelta(days=7)

def ciclo_ingesta_precios():
    tickers = obtener_tickers_activos()
    if not tickers:
        return

    LOTE_SIZE = 505
    print(f"[*] Sincronizando precios intradiarios en lotes para {len(tickers)} activos...")
    
    conn = sqlite3.connect(DB_PATH)
    
    for i in range(0, len(tickers), LOTE_SIZE):
        lote = tickers[i:i+LOTE_SIZE]
        
        for ticker in lote:
            try:
                ultimo_registro = obtener_ultimo_timestamp(ticker)
                ahora = datetime.now(timezone.utc)
                
                # Si el último registro es de hace menos de 5 minutos, ignoramos
                if (ahora - ultimo_registro).total_seconds() < 300:
                    continue
                    
                activo = yf.Ticker(ticker)
                df = activo.history(start=ultimo_registro, interval="1m")
                
                if df.empty:
                    continue
                    
                df = df.reset_index()
                df = df.rename(columns={'Datetime': 'timestamp', 'Date': 'timestamp', 
                                        'Open': 'open', 'High': 'high', 'Low': 'low', 
                                        'Close': 'close', 'Volume': 'volume'})
                
                df['ticker'] = ticker
                
                if df['timestamp'].dt.tz is None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
                else:
                    df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
                
                df['timestamp'] = df['timestamp'].apply(lambda x: x.isoformat())
                
                df_final = df[['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                cursor = conn.cursor()
                filas = df_final.to_records(index=False).tolist()
                cursor.executemany(
                    """
                    INSERT OR IGNORE INTO precios (ticker, timestamp, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    filas
                )
                conn.commit()
                
            except sqlite3.IntegrityError:
                pass # Ignoramos duplicados
            except Exception as e:
                print(e)
                # Errores silenciosos para no frenar el lote (ej. ticker deslistado)
                pass 
                
            # Throttling intra-lote
            time.sleep(random.uniform(0.01, 0.02))
            
        print(f"    [+] Lote de precios completado. Descansando la API...")
        conn.commit()
        time.sleep(1) # Throttling inter-lote

    conn.close()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Ciclo de precios completado.")

if __name__ == "__main__":
    print("[*] Arrancando Daemon de Precios (Presiona Ctrl+C para detener)")
    
    while ejecutando:
        config = cargar_config()
        ciclo_ingesta_precios()
        
        intervalo = config["intervalos_segundos"]["precios"]
        segundos_esperados = 0
        while segundos_esperados < intervalo and ejecutando:
            time.sleep(1)
            segundos_esperados += 1
            
    print("[*] Daemon de precios detenido de forma segura.")
    sys.exit(0)
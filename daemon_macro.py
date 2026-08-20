import sqlite3
import yfinance as yf
import signal
import sys
import time
from datetime import datetime, timezone

DB_PATH = "data/market_data.db"
INTERVALO_ESPERA = 43200  # 12 horas en segundos (solo necesitamos 1 o 2 fotos al día)

ejecutando = True

def cierre_elegante(sig, frame):
    global ejecutando
    print("\n[!] Señal de apagado recibida. Deteniendo Daemon Macro...")
    ejecutando = False

signal.signal(signal.SIGINT, cierre_elegante)
signal.signal(signal.SIGTERM, cierre_elegante)

def inicializar_db():
    """Prepara la tabla para los datos macroeconómicos diarios."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS macro_diario (
            fecha TEXT PRIMARY KEY,
            vix REAL,
            tnx REAL,
            petroleo REAL,
            dolar REAL
        )
    ''')
    conn.commit()
    conn.close()

def ciclo_macro():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando escaneo macroeconómico (Gravedad Global)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tickers de los índices globales en Yahoo Finance
    tickers_macro = {
        'vix': '^VIX',       # Índice del Miedo (Volatilidad del S&P 500)
        'tnx': '^TNX',       # Rendimiento de los Bonos del Tesoro de EE.UU. a 10 años
        'petroleo': 'CL=F',  # Futuros del Crudo WTI (Conflictos geopolíticos/Ormuz)
        'dolar': 'DX-Y.NYB'  # Índice Dólar (Fuerza de la moneda)
    }
    
    valores_hoy = {}
    # Usamos solo Año-Mes-Día para tener un único registro diario
    fecha_hoy = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    try:
        for clave, simbolo in tickers_macro.items():
            activo = yf.Ticker(simbolo)
            # Bajamos los últimos 5 días para sortear fines de semana o feriados sin datos
            hist = activo.history(period="5d")
            
            if not hist.empty:
                # Tomamos el precio de cierre más reciente
                valores_hoy[clave] = round(hist['Close'].iloc[-1], 4)
            else:
                valores_hoy[clave] = None
                print(f"    [!] Advertencia: No se obtuvieron datos para {simbolo}")
        
        # Validar que al menos tengamos los datos críticos antes de guardar
        if valores_hoy.get('vix') and valores_hoy.get('tnx'):
            # Upsert: Si ya existe el día de hoy, lo actualiza con el cierre más reciente
            cursor.execute('''
                INSERT INTO macro_diario (fecha, vix, tnx, petroleo, dolar)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(fecha) DO UPDATE SET
                vix = excluded.vix,
                tnx = excluded.tnx,
                petroleo = excluded.petroleo,
                dolar = excluded.dolar
            ''', (
                fecha_hoy, 
                valores_hoy.get('vix'), 
                valores_hoy.get('tnx'), 
                valores_hoy.get('petroleo'), 
                valores_hoy.get('dolar')
            ))
            conn.commit()
            print(f"    [+] Temperatura Global guardada para {fecha_hoy}:")
            print(f"        VIX (Miedo): {valores_hoy.get('vix')} | TNX (Tasas): {valores_hoy.get('tnx')}%")
            print(f"        Crudo (Energía): ${valores_hoy.get('petroleo')} | Dólar (DXY): {valores_hoy.get('dolar')}")
        else:
            print("    [!] Error: Faltan datos macro críticos, no se guardó el registro.")
            
    except Exception as e:
        print(f"[!] Error en el ciclo macro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inicializar_db()
    print("[*] Arrancando Daemon Macro (Presiona Ctrl+C para detener)")
    
    while ejecutando:
        ciclo_macro()
        
        segundos = 0
        while segundos < INTERVALO_ESPERA and ejecutando:
            time.sleep(1)
            segundos += 1
            
    print("[*] Daemon Macro detenido de forma segura.")
    sys.exit(0)
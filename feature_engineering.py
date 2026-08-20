import sqlite3
import pandas as pd
import pandas_ta as ta
import numpy as np

DB_PATH = "data/market_data.db"
PERIODOS_RSI = 60       
PERIODOS_ATR = 60       
PERIODOS_MOMENTUM = 390 

def inicializar_tabla():
    """Crea la tabla desde cero si se perdió la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vectores_estado (
            id_noticia TEXT,
            ticker TEXT,
            rsi REAL,
            momentum_pct REAL,
            atr REAL,
            vix REAL,
            tnx REAL,
            petroleo REAL,
            dolar REAL,
            PRIMARY KEY (id_noticia, ticker)
        )
    ''')
    conn.commit()
    conn.close()

def cargar_contexto_macro(conn: sqlite3.Connection) -> pd.DataFrame:
    """Carga los datos diarios macro y rellena huecos (fines de semana)."""
    try:
        df_macro = pd.read_sql_query("SELECT * FROM macro_diario ORDER BY fecha ASC", conn)
        if df_macro.empty: return pd.DataFrame()
        
        # Convertir a datetime y establecer como índice
        df_macro['fecha'] = pd.to_datetime(df_macro['fecha'], utc=True)
        df_macro.set_index('fecha', inplace=True)
        
        # Re-muestrear a frecuencia diaria (D) y arrastrar el último valor válido (Forward Fill)
        # Esto soluciona el problema de leer noticias un domingo con datos macro del viernes.
        df_macro = df_macro.resample('D').ffill()
        return df_macro
    except Exception as e:
        print(f"[!] Aviso: No se pudo cargar macro_diario. {e}")
        return pd.DataFrame()

def preparar_vectores_estado():
    inicializar_tabla()
    conn = sqlite3.connect(DB_PATH)
    
    query_noticias = """
        SELECT c.id_noticia, c.ticker, n.timestamp
        FROM correlaciones c
        JOIN noticias n ON c.id_noticia = n.id
        LEFT JOIN vectores_estado v ON c.id_noticia = v.id_noticia AND c.ticker = v.ticker
        WHERE v.id_noticia IS NULL
    """
    noticias = pd.read_sql_query(query_noticias, conn)
    
    if noticias.empty:
        print("[!] No hay eventos nuevos para procesar. Corre el motor de inferencia primero.")
        conn.close()
        return

    df_macro = cargar_contexto_macro(conn)
    if df_macro.empty:
        print("[!] Advertencia: La tabla macro_diario está vacía. El vector se guardará con nulos.")

    print(f"[*] Ensamblando Vectores de Estado (Micro + Macro) para {len(noticias)} eventos...")
    
    tickers_unicos = noticias['ticker'].unique()
    resultados = []

    for ticker in tickers_unicos:
        # Cargar precios intradiarios
        df_precios = pd.read_sql_query(
            "SELECT timestamp, high, low, close FROM precios WHERE ticker = ? ORDER BY timestamp ASC",
            conn, params=(ticker,)
        )
        
        if df_precios.empty or len(df_precios) < PERIODOS_MOMENTUM:
            continue
            
        df_precios['timestamp'] = pd.to_datetime(df_precios['timestamp'], utc=True)
        df_precios.set_index('timestamp', inplace=True)
        
        # Matemática Algorítmica (Micro)
        df_precios['rsi'] = df_precios.ta.rsi(length=PERIODOS_RSI)
        df_precios['momentum'] = df_precios.ta.roc(length=PERIODOS_MOMENTUM)
        df_precios['atr'] = df_precios.ta.atr(length=PERIODOS_ATR)
        df_precios.dropna(inplace=True)
        
        eventos_ticker = noticias[noticias['ticker'] == ticker]
        
        for _, evento in eventos_ticker.iterrows():
            id_noticia = evento['id_noticia']
            dt_t0 = pd.to_datetime(evento['timestamp'], utc=True)
            
            # --- 1. Extraer Micro (Precio exacto) ---
            vela_t0 = df_precios.index[df_precios.index <= dt_t0]
            if vela_t0.empty: continue
            vector_micro = df_precios.loc[vela_t0[-1]]
            
            # --- 2. Extraer Macro (Gravedad Global) ---
            vix, tnx, petroleo, dolar = None, None, None, None
            if not df_macro.empty:
                # Truncar la hora para buscar el día exacto en la tabla macro
                dia_noticia = dt_t0.floor('D')
                if dia_noticia in df_macro.index:
                    vector_macro = df_macro.loc[dia_noticia]
                    vix = vector_macro.get('vix')
                    tnx = vector_macro.get('tnx')
                    petroleo = vector_macro.get('petroleo')
                    dolar = vector_macro.get('dolar')
                
            resultados.append((
                id_noticia, ticker, 
                round(vector_micro['rsi'], 2), 
                round(vector_micro['momentum'], 4), 
                round(vector_micro['atr'], 4),
                vix, tnx, petroleo, dolar
            ))

    if resultados:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO vectores_estado (id_noticia, ticker, rsi, momentum_pct, atr, vix, tnx, petroleo, dolar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', resultados)
        conn.commit()
        print(f"[+] Se ensamblaron y guardaron {len(resultados)} tensores híbridos en la base de datos.")

    conn.close()

if __name__ == "__main__":
    preparar_vectores_estado()
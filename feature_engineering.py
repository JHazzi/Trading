import sqlite3
import pandas as pd
import pandas_ta as ta
import numpy as np

DB_PATH = "data/market_data.db"

# Parámetros del algoritmo adaptados a velas de 1 minuto
PERIODOS_RSI = 60       # RSI de la última hora de trading
PERIODOS_ATR = 60       # Volatilidad de la última hora
PERIODOS_MOMENTUM = 390 # 390 minutos = 1 día completo de mercado abierto (NYSE)

def preparar_vectores_estado():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Traemos las noticias que están correlacionadas pero aún no tienen su vector
    query_noticias = """
        SELECT c.id_noticia, c.ticker, n.timestamp
        FROM correlaciones c
        JOIN noticias n ON c.id_noticia = n.id
        LEFT JOIN vectores_estado v ON c.id_noticia = v.id_noticia AND c.ticker = v.ticker
        WHERE v.id_noticia IS NULL
    """
    noticias = pd.read_sql_query(query_noticias, conn)
    
    if noticias.empty:
        print("[!] Todos los vectores de estado ya están calculados.")
        conn.close()
        return

    print(f"[*] Calculando matrices de características para {len(noticias)} eventos...")
    
    # Trabajamos agrupando por ticker para calcular el análisis técnico una sola vez por empresa
    tickers_unicos = noticias['ticker'].unique()
    resultados = []

    for ticker in tickers_unicos:
        print(f"    -> Procesando tensores técnicos para {ticker}...")
        
        # 2. Cargar todo el historial de precios del ticker
        df_precios = pd.read_sql_query(
            "SELECT timestamp, high, low, close FROM precios WHERE ticker = ? ORDER BY timestamp ASC",
            conn, params=(ticker,)
        )
        
        if df_precios.empty or len(df_precios) < PERIODOS_MOMENTUM:
            continue
            
        # Convertir timestamp y ordenarlo
        df_precios['timestamp'] = pd.to_datetime(df_precios['timestamp'], utc=True)
        df_precios.set_index('timestamp', inplace=True)
        
        # 3. Matemática Algorítmica (Cálculo Vectorizado)
        # RSI (Índice de Saturación)
        df_precios['rsi'] = df_precios.ta.rsi(length=PERIODOS_RSI)
        
        # Momentum (Rate of Change % a 24hs)
        df_precios['momentum'] = df_precios.ta.roc(length=PERIODOS_MOMENTUM)
        
        # Volatilidad Intrínseca (Average True Range)
        df_precios['atr'] = df_precios.ta.atr(length=PERIODOS_ATR)
        
        # Limpiamos los nulos generados por las ventanas móviles iniciales
        df_precios.dropna(inplace=True)
        
        # 4. Extracción de la "Foto" en T0
        eventos_ticker = noticias[noticias['ticker'] == ticker]
        
        for _, evento in eventos_ticker.iterrows():
            id_noticia = evento['id_noticia']
            dt_t0 = pd.to_datetime(evento['timestamp'], utc=True)
            
            # Buscar la vela exacta de la noticia, o la más cercana anterior (T0 o T-1)
            vela_t0 = df_precios.index[df_precios.index <= dt_t0]
            
            if not vela_t0.empty:
                idx_vela = vela_t0[-1]
                vector = df_precios.loc[idx_vela]
                
                resultados.append((
                    id_noticia, ticker, 
                    round(vector['rsi'], 2), 
                    round(vector['momentum'], 4), 
                    round(vector['atr'], 4)
                ))

    # 5. Persistencia del Vector
    if resultados:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO vectores_estado (id_noticia, ticker, rsi, momentum_pct, atr)
            VALUES (?, ?, ?, ?, ?)
        ''', resultados)
        conn.commit()
        print(f"[+] Se ensamblaron y guardaron {len(resultados)} vectores de estado.")

    conn.close()

if __name__ == "__main__":
    preparar_vectores_estado()
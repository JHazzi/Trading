import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "data/market_data.db"

def evaluar_impacto_noticias():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Traer noticias: Ahora pedimos 'importancia' y filtramos la basura directamente
    query_noticias = """
        SELECT n.id, n.ticker, n.timestamp, n.sentimiento, n.grado, n.importancia
        FROM noticias n
        WHERE n.sentimiento IS NOT NULL 
        AND n.importancia IS NOT NULL
        AND n.importancia > 0.0 -- Filtramos el clickbait
        AND n.id NOT IN (SELECT DISTINCT id_noticia FROM correlaciones)
    """
    noticias = pd.read_sql_query(query_noticias, conn)
    
    if noticias.empty:
        conn.close()
        return

    print(f"[*] Cerebro: Evaluando propagación y MFE para {len(noticias)} noticias de calidad...")
    
    cursor = conn.cursor()
    resultados = []
    tickers_necesarios = set(noticias['ticker'].unique())
    
    # 2. Mapear Contagios (El Grafo)
    mapa_contagios = {} 
    for _, noticia in noticias.iterrows():
        origen = noticia['ticker']
        cursor.execute("SELECT destino, peso FROM relaciones_organicas WHERE origen = ?", (origen,))
        relaciones = cursor.fetchall()
        
        contagios = []
        for destino, co_ocurrencias in relaciones:
            factor_transferencia = min(co_ocurrencias * 0.05, 0.80) 
            contagios.append((destino, factor_transferencia))
            tickers_necesarios.add(destino)
            
        mapa_contagios[noticia['id']] = contagios

    # 3. Descarga de Precios Masiva
    tickers_tupla = tuple(tickers_necesarios)
    query_precios = f"SELECT ticker, timestamp, open, high, low, close FROM precios WHERE ticker IN {tickers_tupla}"
    if len(tickers_tupla) == 1:
        query_precios = query_precios.replace(str(tickers_tupla), f"('{tickers_tupla[0]}')")
        
    precios = pd.read_sql_query(query_precios, conn)
    precios['timestamp'] = pd.to_datetime(precios['timestamp'], utc=True)
    
    # 4. Procesamiento de Ventanas Temporales
    for _, noticia in noticias.iterrows():
        id_noticia = noticia['id']
        ticker_base = noticia['ticker']
        
        # ADIÓS HARDCODING: Usamos la importancia calculada algorítmicamente
        importancia = noticia['importancia']
        sentimiento_str = noticia['sentimiento'] 
        val_dir = 1.0 if sentimiento_str == 'positive' else (-1.0 if sentimiento_str == 'negative' else 0.0)
        
        # La fuerza de la señal ahora es pura matemática basada en datos
        sentimiento_base = val_dir * noticia['grado'] * importancia
        
        dt_noticia = pd.to_datetime(noticia['timestamp'], utc=True)
        dt_previa = dt_noticia - timedelta(minutes=30)
        dt_futura = dt_noticia + timedelta(minutes=60)
        
        sujetos = [(ticker_base, sentimiento_base, 0)] 
        for destino, factor in mapa_contagios.get(id_noticia, []):
            sujetos.append((destino, sentimiento_base * factor, 1))
            
        for ticker_obj, sentimiento_obj, es_contagio in sujetos:
            if abs(sentimiento_obj) < 0.05: continue 
            
            precios_ticker = precios[precios['ticker'] == ticker_obj]
            if precios_ticker.empty: continue
            
            ventana_previa = precios_ticker[
                (precios_ticker['timestamp'] >= dt_previa) & 
                (precios_ticker['timestamp'] <= dt_noticia)
            ]
            ventana_futura = precios_ticker[
                (precios_ticker['timestamp'] >= dt_noticia) & 
                (precios_ticker['timestamp'] <= dt_futura)
            ]
            
            if not ventana_previa.empty and not ventana_futura.empty:
                precio_t0 = ventana_futura.iloc[0]['open']
                precio_t_menos_30 = ventana_previa.iloc[0]['open']
                
                div_previa_pct = ((precio_t0 - precio_t_menos_30) / precio_t_menos_30) * 100
                
                if sentimiento_obj > 0:
                    precio_mfe = ventana_futura['high'].max()
                elif sentimiento_obj < 0:
                    precio_mfe = ventana_futura['low'].min()
                else:
                    precio_mfe = ventana_futura.iloc[-1]['close'] 
                    
                mfe_60m_pct = ((precio_mfe - precio_t0) / precio_t0) * 100
                
                resultados.append((
                    id_noticia, ticker_obj, es_contagio, round(sentimiento_obj, 4), importancia, 
                    round(div_previa_pct, 4), precio_t0, precio_mfe, round(mfe_60m_pct, 4)
                ))

    # 5. Persistencia
    if resultados:
        cursor = conn.cursor()
        # Nota: Seguimos guardando la importancia en la columna 'fiabilidad_fuente' 
        # para no tener que romper la tabla en SQLite de nuevo. 
        cursor.executemany('''
            INSERT OR IGNORE INTO correlaciones (
                id_noticia, ticker, es_contagio, sentimiento, fiabilidad_fuente, 
                divergencia_previa_pct, precio_instante, precio_mfe_60m, impacto_mfe_60m_pct
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', resultados)
        conn.commit()
        
        directas = sum(1 for r in resultados if r[2] == 0)
        contagios = sum(1 for r in resultados if r[2] == 1)
        print(f"    [+] Generadas {directas} correlaciones directas y {contagios} por contagio (Grafo).")

    conn.close()

if __name__ == "__main__":
    evaluar_impacto_noticias()
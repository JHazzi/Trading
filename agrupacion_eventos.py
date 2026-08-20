import sqlite3
import pandas as pd
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from datetime import datetime, timezone

DB_PATH = "data/market_data.db"
# Umbral de distancia semántica (0.15 de distancia = 85% de similitud)
UMBRAL_DISTANCIA = 0.15 
# Tasa de decaimiento (Vida media de una noticia financiera ~ 6 horas = 360 minutos)
# Lambda = ln(2) / Vida Media
LAMBDA_DECAY = np.log(2) / 360.0 

def preparar_base_datos(conn: sqlite3.Connection):
    """Añade las columnas necesarias si no existen para registrar el clustering."""
    try:
        conn.execute("ALTER TABLE noticias ADD COLUMN id_evento TEXT")
        conn.execute("ALTER TABLE noticias ADD COLUMN desfase_minutos REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Las columnas ya existen
    conn.commit()

def agrupar_ecos_financieros():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Cargando modelo de Embeddings (SentenceTransformer) en {device}...")
    modelo_emb = SentenceTransformer('all-MiniLM-L6-v2', device=device)
    
    conn = sqlite3.connect(DB_PATH)
    preparar_base_datos(conn)
    
    # Traemos las noticias que tienen importancia válida (> 0) y aún no han sido agrupadas
    df = pd.read_sql_query("""
        SELECT id, ticker, timestamp, titulo, resumen, importancia 
        FROM noticias 
        WHERE importancia > 0.0 AND id_evento IS NULL AND fuente != 'SEC EDGAR'
    """, conn)
    
    if df.empty:
        print("[!] No hay noticias pendientes de agrupar.")
        conn.close()
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['texto_completo'] = df['titulo'] + ". " + df['resumen'].fillna('')
    
    tickers = df['ticker'].unique()
    print(f"[*] Analizando topología de eventos para {len(tickers)} empresas ({len(df)} noticias)...")
    
    actualizaciones = []
    
    for ticker in tickers:
        df_ticker = df[df['ticker'] == ticker].copy()
        
        # Si solo hay una noticia de la empresa, es su propio evento primario
        if len(df_ticker) == 1:
            row = df_ticker.iloc[0]
            actualizaciones.append((row['id'], 0.0, row['importancia'], row['id']))
            continue
            
        # 1. Generar vectores semánticos
        textos = df_ticker['texto_completo'].tolist()
        embeddings = modelo_emb.encode(textos, show_progress_bar=False)
        
        # 2. Clustering Aglomerativo basado en similitud semántica pura (sin límite de horas)
        clusterizador = AgglomerativeClustering(
            n_clusters=None, 
            distance_threshold=UMBRAL_DISTANCIA, 
            metric='cosine', 
            linkage='average'
        )
        etiquetas = clusterizador.fit_predict(embeddings)
        df_ticker['cluster_id'] = etiquetas
        
        # 3. Mapear el Minuto Cero (T0) y aplicar Decaimiento
        for cluster in df_ticker['cluster_id'].unique():
            df_cluster = df_ticker[df_ticker['cluster_id'] == cluster].sort_values('timestamp')
            
            # La noticia más antigua es el Evento Primario
            id_t0 = df_cluster.iloc[0]['id']
            tiempo_t0 = df_cluster.iloc[0]['timestamp']
            
            for _, row in df_cluster.iterrows():
                id_actual = row['id']
                tiempo_actual = row['timestamp']
                importancia_original = row['importancia']
                
                # Calcular el desfase en minutos
                desfase_min = (tiempo_actual - tiempo_t0).total_seconds() / 60.0
                
                # Aplicar la Matemática de Impacto (Decaimiento Exponencial)
                # Si es el T0, desfase = 0, exp(0) = 1 (mantiene su importancia intacta)
                factor_decaimiento = np.exp(-LAMBDA_DECAY * desfase_min)
                importancia_ajustada = round(importancia_original * factor_decaimiento, 4)
                
                actualizaciones.append((
                    id_t0, 
                    round(desfase_min, 2), 
                    importancia_ajustada, 
                    id_actual
                ))

    # 4. Actualización en Base de Datos
    if actualizaciones:
        cursor = conn.cursor()
        cursor.executemany("""
            UPDATE noticias 
            SET id_evento = ?, desfase_minutos = ?, importancia = ? 
            WHERE id = ?
        """, actualizaciones)
        conn.commit()
        print(f"[+] Se agruparon {len(actualizaciones)} noticias. Los ecos tardíos sufrieron penalización matemática.")
        
    conn.close()

if __name__ == "__main__":
    agrupar_ecos_financieros()
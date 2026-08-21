from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import math
import json
import os
import pandas_ta as ta
import joblib
import pandas as pd
import numpy as np
import random

app = FastAPI(title="Quant Market Bot API - Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "data/market_data.db"
CONFIG_PATH = "config.json"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Devuelve diccionarios en lugar de tuplas
    return conn

# --- 1. CONFIGURACIÓN (Lectura y Escritura) ---
@app.get("/api/config")
def obtener_configuracion():
    with open(CONFIG_PATH, 'r') as file:
        return json.load(file)

@app.post("/api/config")
def actualizar_configuracion(nueva_config: dict):
    with open(CONFIG_PATH, 'w') as file:
        json.dump(nueva_config, file, indent=4)
    return {"status": "success", "message": "Configuración actualizada. Los daemons la leerán en su próximo ciclo."}

# --- 2. DASHBOARD Y ESTADÍSTICAS ---
@app.get("/api/estadisticas")
def obtener_estadisticas_globales():
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {
        "noticias_totales": cursor.execute("SELECT COUNT(*) FROM noticias").fetchone()[0],
        "operaciones_paper": cursor.execute("SELECT COUNT(*) FROM paper_trading").fetchone()[0],
        "aristas_grafo": cursor.execute("SELECT COUNT(*) FROM relaciones_organicas").fetchone()[0],
        "tickers_activos": cursor.execute("SELECT COUNT(*) FROM universo_tickers WHERE activo = 1").fetchone()[0]
    }
    conn.close()
    return stats

# --- 3. DATOS DE PRECIOS (Para Gráficos de Velas / ECharts) ---
@app.get("/api/precios/{ticker}")
def obtener_precios(ticker: str, limite: int = 100):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp as time, open, high, low, close, volume 
        FROM precios 
        WHERE ticker = ? 
        ORDER BY timestamp DESC LIMIT ?
    """, (ticker.upper(), limite))
    filas = cursor.fetchall()
    conn.close()
    
    if not filas:
        raise HTTPException(status_code=404, detail="Ticker no encontrado o sin datos")
        
    # Invertimos para que el frontend reciba del más antiguo al más nuevo (ideal para gráficos)
    return [dict(fila) for fila in reversed(filas)]

# --- 4. TOPOLOGÍA (Para el Grafo Semántico con Vis.js) ---
# @app.get("/api/grafo")
# def obtener_topologia_mercado():
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Obtenemos los nodos (empresas)
#     cursor.execute("SELECT ticker, empresa, sector FROM universo_tickers WHERE activo = 1")
#     nodos = [{"id": f["ticker"], "label": f["ticker"], "title": f["empresa"], "group": f["sector"]} for f in cursor.fetchall()]
    
#     # SOLUCIÓN: Filtramos las relaciones irrelevantes en el backend para no saturar la RAM del navegador
#     cursor.execute("SELECT origen, destino, peso FROM relaciones_organicas WHERE abs(peso) >= 0.6")
#     aristas = [{"from": f["origen"], "to": f["destino"], "value": abs(f["peso"]), "color": "green" if f["peso"] > 0 else "red"} for f in cursor.fetchall()]
    
#     conn.close()
#     return {"nodes": nodos, "edges": aristas}

# --- 4. TOPOLOGÍA (Para el Grafo Semántico con Vis.js) ---
@app.get("/api/grafo")
def obtener_topologia_mercado():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Obtenemos SOLO las aristas con alto impacto (Filtro de Ruido)
    cursor.execute("SELECT origen, destino, peso FROM relaciones_organicas WHERE abs(peso) >= 0.4")
    aristas_db = cursor.fetchall()
    
    # Colores institucionales: Verde Bullish (#10B981) y Rojo Bearish (#EF4444)
    aristas = [{
        "from": f["origen"], 
        "to": f["destino"], 
        "value": abs(f["peso"]), 
        "color": "#10B981" if f["peso"] > 0 else "#EF4444"
    } for f in aristas_db]
    
    # 2. Extraemos los Tickers únicos que participan en estas aristas
    tickers_conectados = set()
    for f in aristas_db:
        tickers_conectados.add(f["origen"])
        tickers_conectados.add(f["destino"])
        
    # Si no hay contagios fuertes hoy, devolvemos un lienzo en blanco seguro
    if not tickers_conectados:
        conn.close()
        return {"nodes": [], "edges": []}
        
    # 3. Traemos SOLO los nodos que están interactuando, ignorando a los huérfanos
    placeholders = ','.join(['?'] * len(tickers_conectados))
    query_nodos = f"SELECT ticker, empresa, sector FROM universo_tickers WHERE activo = 1 AND ticker IN ({placeholders})"
    
    cursor.execute(query_nodos, tuple(tickers_conectados))
    nodos = [{
        "id": f["ticker"], 
        "label": f["ticker"], 
        "title": f["empresa"], 
        "group": f["sector"]
    } for f in cursor.fetchall()]
    
    conn.close()
    return {"nodes": nodos, "edges": aristas}

# --- 5. FLUJO DE NOTICIAS Y SENTIMIENTO ---
@app.get("/api/noticias")
def obtener_ultimas_noticias(limite: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, ticker, titulo, fuente, sentimiento, importancia 
        FROM noticias 
        ORDER BY timestamp DESC LIMIT ?
    """, (limite,))
    noticias = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return noticias

# --- 6. PAPER TRADING (Rendimiento del Bot) ---
@app.get("/api/operaciones")
def obtener_historial_trading():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM paper_trading ORDER BY id_operacion DESC")
    operaciones = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return operaciones

@app.get("/api/tickers")
def obtener_tickers():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Traemos solo los activos y ordenados alfabéticamente
    cursor.execute("SELECT ticker, empresa FROM universo_tickers WHERE activo = 1 ORDER BY ticker ASC")
    tickers = [dict(f) for f in cursor.fetchall()]
    conn.close()
    return tickers

# --- 7. SERVIDOR DEL FRONTEND ---

app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")
@app.get("/")
def servir_dashboard():
    """Sirve la interfaz web directamente desde FastAPI."""
    return FileResponse("frontend/index.html")


# --- 8. MOTOR DE INFERENCIA A DEMANDA (Generador de Reportes) ---
@app.get("/api/reporte/{ticker}")
def generar_reporte_demanda(ticker: str, dias: int):
    conn = get_db_connection()
    
    # 1. ESTADO TÉCNICO EN TIEMPO REAL
    # Traemos los precios para calcular RSI, Momentum y ATR exactos al día de hoy
    df_precios = pd.read_sql_query(
        "SELECT timestamp, close, high, low FROM precios WHERE ticker = ? ORDER BY timestamp ASC",
        conn, params=(ticker.upper(),)
    )
    
    if len(df_precios) < 60:
        conn.close()
        raise HTTPException(status_code=404, detail="Sin datos históricos suficientes.")
        
    df_precios['rsi'] = df_precios.ta.rsi(length=14)
    df_precios['momentum'] = df_precios.ta.roc(length=20)
    df_precios['atr'] = df_precios.ta.atr(length=14)
    
    ultima_vela = df_precios.iloc[-1]
    precio_actual = ultima_vela['close']
    rsi_actual = ultima_vela['rsi'] if not pd.isna(ultima_vela['rsi']) else 50.0
    mom_actual = ultima_vela['momentum'] if not pd.isna(ultima_vela['momentum']) else 0.0
    atr_actual = ultima_vela['atr'] if not pd.isna(ultima_vela['atr']) else (precio_actual * 0.02)
    
    # Volatilidad histórica (Desviación estándar de retornos diarios) para el Paseo Aleatorio
    df_precios['retorno_diario'] = df_precios['close'].pct_change()
    volatilidad_diaria = df_precios['retorno_diario'].std()
    
    max_anual = df_precios['high'].tail(252).max()
    min_anual = df_precios['low'].tail(252).min()

    # 2. ÚLTIMO CONTEXTO SEMÁNTICO (Sentimiento persistente)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sentimiento, importancia FROM noticias 
        WHERE ticker = ? AND sentimiento IS NOT NULL 
        ORDER BY timestamp DESC LIMIT 1
    """, (ticker.upper(),))
    noticia = cursor.fetchone()
    
    sentimiento_num = 0.0
    importancia = 0.0
    
    if noticia:
        # Convertimos el texto FinBERT a fuerza matemática[cite: 26]
        s_str = noticia['sentimiento']
        importancia = noticia['importancia']
        if s_str == 'positive': sentimiento_num = importancia
        elif s_str == 'negative': sentimiento_num = -importancia

    # 3. INFERENCIA UNIFICADA (El Cerebro)
    mu_t = 0.0
    certeza_base = 50.0
    
    ruta_reg = os.path.join("modelos_ia", "oraculo_rendimiento.pkl")
    ruta_clf = os.path.join("modelos_ia", "gestor_certeza.pkl")
    
    if os.path.exists(ruta_reg) and os.path.exists(ruta_clf):
        regresor = joblib.load(ruta_reg)
        clasificador = joblib.load(ruta_clf)
        
        # El vector se arma SIEMPRE, haya noticias recientes o no
        X = pd.DataFrame([{
            'importancia': importancia,
            'sentimiento': sentimiento_num,
            'es_contagio': 0,
            'rsi': rsi_actual,
            'momentum_pct': mom_actual,
            'atr': atr_actual
        }])
        
        predicciones = np.array([arbol.predict(X.values) for arbol in regresor.estimators_])
        mu_t = float(np.mean(predicciones))
        
        probs = clasificador.predict_proba(X)[0]
        if len(probs) > 1:
            certeza_base = probs[1] * 100

    # 4. SIMULACIÓN ESTOCÁSTICA (Paseo Aleatorio del Mercado)
    curva_proyeccion = []
    
    # Adaptamos la frecuencia de los pasos (ej: intradiario si son pocos días)
    pasos_totales = dias * 4 if dias <= 14 else dias  # 4 pasos por día si es a corto plazo
    drift_por_paso = mu_t / pasos_totales
    rendimiento_acumulado = 0.0
    
    for i in range(1, pasos_totales + 1):
        # Movimiento Browniano: Deriva esperada + Shock Aleatorio basado en volatilidad real
        shock = random.gauss(0, volatilidad_diaria * 100)
        rendimiento_acumulado += drift_por_paso + (shock / math.sqrt(pasos_totales))
        
        # La certeza cae a medida que nos alejamos en los pasos
        f_riesgo = math.sqrt(i / (4 if dias <= 14 else 1))
        c_ajustada = max(10.0, min(99.0, certeza_base - (f_riesgo * 2.5)))
        
        eje_x = f"Día {i/4:.2f}" if dias <= 14 else f"Día {i}"
        
        curva_proyeccion.append({
            "dia_label": eje_x,
            "rendimiento": round(rendimiento_acumulado, 2),
            "certeza": round(c_ajustada, 2)
        })

    # 5. EXPLICABILIDAD (Para la Interfaz)
    razonamiento = {
        "RSI Actual": f"{rsi_actual:.1f}",
        "Momentum": f"{mom_actual:.2f}%",
        "Fuerza Sentimiento": f"{sentimiento_num:.2f}",
        "Volatilidad (ATR)": f"{atr_actual:.2f}"
    }

    distancia_piso = ((precio_actual - min_anual) / min_anual) * 100
    distancia_techo = ((max_anual - precio_actual) / max_anual) * 100
    tension = "Equilibrio Estadístico"
    if distancia_piso < 5.0: tension = f"Acumulación en Mínimo ({distancia_piso:.1f}%)"
    elif distancia_techo < 5.0: tension = f"Saturación en Máximo ({distancia_techo:.1f}%)"
        
    conn.close()
    
    return {
        "precio_actual": round(precio_actual, 2),
        "rendimiento": curva_proyeccion[-1]["rendimiento"],
        "certeza": curva_proyeccion[-1]["certeza"],
        "tension": tension,
        "curva": curva_proyeccion,
        "razonamiento": razonamiento
    }
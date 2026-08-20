from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
import sqlite3
import json

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
@app.get("/api/grafo")
def obtener_topologia_mercado():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtenemos los nodos (empresas)
    cursor.execute("SELECT ticker, empresa, sector FROM universo_tickers WHERE activo = 1")
    nodos = [{"id": f["ticker"], "label": f["ticker"], "title": f["empresa"], "group": f["sector"]} for f in cursor.fetchall()]
    
    # Obtenemos las aristas (relaciones)
    cursor.execute("SELECT origen, destino, peso FROM relaciones_organicas")
    aristas = [{"from": f["origen"], "to": f["destino"], "value": abs(f["peso"]), "color": "green" if f["peso"] > 0 else "red"} for f in cursor.fetchall()]
    
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
@app.get("/")
def servir_dashboard():
    """Sirve la interfaz web directamente desde FastAPI."""
    return FileResponse("frontend/index.html")
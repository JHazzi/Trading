import sqlite3
import pandas as pd
import numpy as np
import time
import signal
import sys
import os
import joblib
from datetime import datetime, timedelta, timezone

DB_PATH = "data/market_data.db"
MODEL_DIR = "modelos_ia"
INTERVALO_ESPERA = 900  # 15 minutos
HORIZONTE_DEFAULT = 24  # Horas de maduración
COMISION_BROKER = 1   # 1% IOL

ejecutando = True

def cierre_elegante(sig, frame):
    global ejecutando
    print("\n[!] Señal de apagado recibida. Deteniendo Paper Trading...")
    ejecutando = False

signal.signal(signal.SIGINT, cierre_elegante)
signal.signal(signal.SIGTERM, cierre_elegante)

def cargar_modelos():
    ruta_reg = os.path.join(MODEL_DIR, "oraculo_rendimiento.pkl")
    ruta_clf = os.path.join(MODEL_DIR, "gestor_certeza.pkl")
    
    if not os.path.exists(ruta_reg) or not os.path.exists(ruta_clf):
        print("[!] Modelos no encontrados. Ejecuta 'entrenar_modelo.py' primero.")
        return None, None
        
    regresor = joblib.load(ruta_reg)
    clasificador = joblib.load(ruta_clf)
    return regresor, clasificador

def abrir_posiciones_virtuales(conn: sqlite3.Connection, regresor, clasificador):
    """Busca eventos recientes y utiliza la IA para decidir la entrada."""
    cursor = conn.cursor()
    limite_tiempo = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    
    # Extraemos el vector de características completo (NLP + Análisis Técnico)
    query = """
        SELECT 
            c.id_noticia, c.ticker, n.timestamp, n.titulo,
            c.fiabilidad_fuente as importancia, 
            c.sentimiento, c.es_contagio,
            v.rsi, v.momentum_pct, v.atr
        FROM correlaciones c
        JOIN noticias n ON c.id_noticia = n.id
        JOIN vectores_estado v ON c.id_noticia = v.id_noticia AND c.ticker = v.ticker
        WHERE n.timestamp >= ?
        AND NOT EXISTS (
            SELECT 1 FROM paper_trading pt 
            WHERE pt.id_noticia = c.id_noticia AND pt.ticker = c.ticker
        )
    """
    df_candidatos = pd.read_sql_query(query, conn, params=(limite_tiempo,))
    
    if df_candidatos.empty: return 0
    
    nuevas_ops = 0
    for _, row in df_candidatos.iterrows():
        # Ensamblamos el vector de estado X
        X = pd.DataFrame([{
            'importancia': row['importancia'],
            'sentimiento': row['sentimiento'],
            'es_contagio': row['es_contagio'],
            'rsi': row['rsi'],
            'momentum_pct': row['momentum_pct'],
            'atr': row['atr']
        }])
        
        # 1. El Oráculo predice el movimiento esperado (Upside)
        rendimiento_predicho = regresor.predict(X)[0]
        
        # 2. El Gestor de Riesgo predice la certeza (Probabilidad de éxito)
        probabilidades = clasificador.predict_proba(X)[0]
        certeza = probabilidades[1] if len(probabilidades) > 1 else 0.0
        
        # 3. Matemática de la Apuesta (Valor Esperado)
        # Asumimos el riesgo (Downside) como proporcional a la volatilidad proyectada si falla
        riesgo = abs(rendimiento_predicho) if rendimiento_predicho != 0 else row['atr']
        
        E_O = (rendimiento_predicho * certeza) - (riesgo * (1 - certeza)) - COMISION_BROKER
        
        if E_O > 0:
            cursor.execute("SELECT close FROM precios WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1", (row['ticker'],))
            precio_row = cursor.fetchone()
            if not precio_row: continue
            precio_entrada = precio_row[0]
            
            cursor.execute('''
                INSERT INTO paper_trading (id_noticia, ticker, fecha_senal, horizonte_horas, 
                                           rendimiento_esperado_pct, certeza_pct, precio_entrada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['id_noticia'], row['ticker'], row['timestamp'], HORIZONTE_DEFAULT, 
                  round(E_O, 4), round(certeza * 100, 2), precio_entrada))
            nuevas_ops += 1
            print(f"    [!] SEÑAL IA ({row['ticker']}): {row['titulo'][:40]}...")
            print(f"        -> Predicción: +{rendimiento_predicho:.2f}% | Certeza: {certeza*100:.1f}% | E[O]: {E_O:.2f}%")

    conn.commit()
    return nuevas_ops

def auditar_posiciones_cerradas(conn: sqlite3.Connection):
    """Cierra operaciones maduras para retroalimentar el modelo en el futuro."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_operacion, ticker, fecha_senal, horizonte_horas, precio_entrada 
        FROM paper_trading 
        WHERE rendimiento_real_pct IS NULL
    """)
    abiertas = cursor.fetchall()
    
    auditadas = 0
    ahora = datetime.now(timezone.utc)
    
    for id_op, ticker, fecha_senal, horizonte, p_entrada in abiertas:
        dt_senal = datetime.fromisoformat(fecha_senal.replace("Z", "+00:00"))
        dt_vencimiento = dt_senal + timedelta(hours=horizonte)
        
        if ahora >= dt_vencimiento:
            cursor.execute("""
                SELECT close FROM precios 
                WHERE ticker = ? AND timestamp >= ? 
                ORDER BY timestamp ASC LIMIT 1
            """, (ticker, dt_vencimiento.isoformat()))
            
            precio_row = cursor.fetchone()
            if not precio_row: continue
            
            p_salida = precio_row[0]
            rendimiento_real = (((p_salida - p_entrada) / p_entrada) * 100) - COMISION_BROKER
            
            cursor.execute("""
                UPDATE paper_trading 
                SET precio_salida_real = ?, rendimiento_real_pct = ?
                WHERE id_operacion = ?
            """, (p_salida, round(rendimiento_real, 4), id_op))
            
            resultado_str = "GANANCIA" if rendimiento_real > 0 else "PÉRDIDA"
            print(f"    [+] AUDITORÍA {ticker}: {resultado_str} de {rendimiento_real:.2f}% (Salida: ${p_salida:.2f})")
            auditadas += 1

    conn.commit()
    return auditadas

def ciclo_trading(regresor, clasificador):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo de inferencia y trading...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        abiertas = abrir_posiciones_virtuales(conn, regresor, clasificador)
        cerradas = auditar_posiciones_cerradas(conn)
        if abiertas > 0 or cerradas > 0:
            print(f"[*] Resumen de ciclo: {abiertas} compras virtuales, {cerradas} operaciones auditadas.")
    except Exception as e:
        print(f"[!] Error en el ciclo de trading: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("[*] Iniciando Sistema de Paper Trading Híbrido...")
    reg, clf = cargar_modelos()
    
    if reg and clf:
        print("[+] Modelos de Inteligencia Artificial cargados en memoria.")
        print("[*] Presiona Ctrl+C para detener")
        
        while ejecutando:
            ciclo_trading(reg, clf)
            
            segundos = 0
            while segundos < INTERVALO_ESPERA and ejecutando:
                time.sleep(1)
                segundos += 1
                
        print("[*] Paper Trading detenido de forma segura.")
    sys.exit(0)
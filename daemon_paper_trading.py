import sqlite3
import pandas as pd
import numpy as np
import time
import signal
import sys
import os
import joblib
from datetime import datetime, timedelta, timezone
import json

DB_PATH = "data/market_data.db"
MODEL_DIR = "modelos_ia"
CONFIG_PATH = "config.json"  # Agregado para que funcione cargar_config()

ejecutando = True

def cargar_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

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

def abrir_posiciones_virtuales(conn: sqlite3.Connection, regresor, clasificador, config: dict):
    """Busca eventos recientes y utiliza la IA Probabilística para decidir la entrada."""
    certeza_minima = config["trading"]["certeza_minima_ia_pct"] / 100.0
    comision = config["trading"]["comision_broker_pct"]
    horizonte = config["trading"]["horizonte_inversion_horas"]
    
    cursor = conn.cursor()
    limite_tiempo = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    
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
        X = pd.DataFrame([{
            'importancia': row['importancia'],
            'sentimiento': row['sentimiento'],
            'es_contagio': row['es_contagio'],
            'rsi': row['rsi'],
            'momentum_pct': row['momentum_pct'],
            'atr': row['atr']
        }])
        
        # --- 1. EXTRACCIÓN PROBABILÍSTICA (Varianza del Ensamble) ---
        # Extraemos la predicción de cada uno de los 200 árboles individuales
        predicciones_arboles = np.array([arbol.predict(X.values) for arbol in regresor.estimators_])
        
        mu_t = float(np.mean(predicciones_arboles))   # Rendimiento esperado (Media)
        sigma_t = float(np.std(predicciones_arboles)) # Caos/Incertidumbre proyectada (Desviación)
        
        probabilidades = clasificador.predict_proba(X)[0]
        certeza = probabilidades[1] if len(probabilidades) > 1 else 0.0
        
        # --- 2. CÁLCULO DEL VALOR ESPERADO (E[O]) ---
        # El riesgo ahora es el Absoluto del Rendimiento Esperado + la Incertidumbre Matemática
        riesgo_ajustado = abs(mu_t) + sigma_t 
        E_O = (mu_t * certeza) - (riesgo_ajustado * (1 - certeza)) - comision
        
        # Filtrado estricto: Debe tener esperanza positiva y superar nuestro umbral manual de certeza
        if E_O > 0 and certeza >= certeza_minima:
            cursor.execute("SELECT close FROM precios WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1", (row['ticker'],))
            precio_row = cursor.fetchone()
            if not precio_row: continue
            precio_entrada = precio_row[0]
            
            cursor.execute('''
                INSERT INTO paper_trading (id_noticia, ticker, fecha_senal, horizonte_horas, 
                                           rendimiento_esperado_pct, certeza_pct, precio_entrada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (row['id_noticia'], row['ticker'], row['timestamp'], horizonte, 
                  round(E_O, 4), round(certeza * 100, 2), precio_entrada))
            nuevas_ops += 1
            print(f"    [!] SEÑAL IA ({row['ticker']}): {row['titulo'][:40]}...")
            margen_inf = mu_t - sigma_t
            margen_sup = mu_t + sigma_t
            print(f"        -> Predicción: [{margen_inf:.2f}% a {margen_sup:.2f}%] | Certeza: {certeza*100:.1f}% | E[O]: {E_O:.2f}%")

    conn.commit()
    return nuevas_ops

def auditar_posiciones_cerradas(conn: sqlite3.Connection, config: dict):
    """Cierra operaciones maduras y calcula el Error Absoluto Medio (MAE) histórico."""
    comision = config["trading"]["comision_broker_pct"]
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id_operacion, ticker, fecha_senal, horizonte_horas, precio_entrada, rendimiento_esperado_pct 
        FROM paper_trading 
        WHERE rendimiento_real_pct IS NULL
    """)
    abiertas = cursor.fetchall()
    
    auditadas = 0
    ahora = datetime.now(timezone.utc)
    
    for id_op, ticker, fecha_senal, horizonte, p_entrada, r_esperado in abiertas:
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
            rendimiento_real = (((p_salida - p_entrada) / p_entrada) * 100) - comision
            
            cursor.execute("""
                UPDATE paper_trading 
                SET precio_salida_real = ?, rendimiento_real_pct = ?
                WHERE id_operacion = ?
            """, (p_salida, round(rendimiento_real, 4), id_op))
            
            resultado_str = "GANANCIA" if rendimiento_real > 0 else "PÉRDIDA"
            print(f"    [+] AUDITORÍA {ticker}: {resultado_str} de {rendimiento_real:.2f}% (Esperado: {r_esperado:.2f}%)")
            auditadas += 1

    # --- 3. CÁLCULO DEL MAE (Mean Absolute Error) ---
    cursor.execute("""
        SELECT abs(rendimiento_esperado_pct - rendimiento_real_pct) 
        FROM paper_trading 
        WHERE rendimiento_real_pct IS NOT NULL 
        ORDER BY fecha_senal DESC LIMIT 20
    """)
    errores = cursor.fetchall()
    mae = np.mean([e[0] for e in errores]) if errores else 0.0

    conn.commit()
    return auditadas, float(mae)

def ciclo_trading(regresor, clasificador, config: dict):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando ciclo de inferencia y trading...")
    conn = sqlite3.connect(DB_PATH)
    reentrenar = False
    
    try:
        abiertas = abrir_posiciones_virtuales(conn, regresor, clasificador, config)
        cerradas, mae = auditar_posiciones_cerradas(conn, config)
        
        if abiertas > 0 or cerradas > 0:
            print(f"[*] Resumen: {abiertas} compras virtuales, {cerradas} auditadas. MAE Actual: {mae:.2f}%")
            
            # --- 4. DISPARADOR DE AUTO-HEALING ---
            if cerradas > 0 and mae > 0.5:
                print("\n[!!!] ALERTA: Desviación del mercado detectada (MAE > 0.5%). Iniciando Auto-Healing...")
                # Importación dinámica para evitar bucles circulares al inicio del archivo
                from entrenar_modelo import entrenar_cerebro_hibrido
                entrenar_cerebro_hibrido()
                reentrenar = True
                
    except Exception as e:
        print(f"[!] Error en el ciclo de trading: {e}")
    finally:
        conn.close()
        
    return reentrenar

if __name__ == "__main__":
    print("[*] Iniciando Sistema de Paper Trading Probabilístico...")
    reg, clf = cargar_modelos()
    
    if reg and clf:
        print("[+] Modelos de Inteligencia Artificial cargados en memoria.")
        print("[*] Presiona Ctrl+C para detener")
        
        while ejecutando:
            config = cargar_config()
            necesita_recarga = ciclo_trading(reg, clf, config)
            
            if necesita_recarga:
                print("[*] Recargando modelos sinápticos actualizados en la RAM...")
                reg, clf = cargar_modelos()
                
            intervalo = config["intervalos_segundos"]["paper_trading"]
            segundos = 0
            while segundos < intervalo and ejecutando:
                time.sleep(1)
                segundos += 1
                
        print("[*] Paper Trading detenido de forma segura.")
    sys.exit(0)
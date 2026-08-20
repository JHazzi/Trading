import sqlite3
import os

DB_PATH = "data/market_data.db"

def forjar_base_de_datos_definitiva():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. UNIVERSO: Las empresas que seguimos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universo_tickers (
            ticker TEXT PRIMARY KEY,
            empresa TEXT,
            sector TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')

    # 2. PRECIOS: La gravedad algorítmica (Velas de 1 minuto)
    # UNIQUE(ticker, timestamp) permite el "INSERT OR IGNORE" del daemon_precios_2.py
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios (
            ticker TEXT,
            timestamp TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            UNIQUE(ticker, timestamp)
        )
    ''')

    # 3. NOTICIAS: El Cerebro NLP (Con escala continua 0-1)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS noticias (
            id TEXT PRIMARY KEY,
            ticker TEXT,
            timestamp TEXT,
            titulo TEXT,
            fuente TEXT,
            resumen TEXT,
            sentimiento TEXT,
            grado REAL,
            importancia REAL
        )
    ''')

    # 4. GRAFO ORGÁNICO: El Cerebro Topológico (Cadenas de suministro)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relaciones_organicas (
            origen TEXT,
            destino TEXT,
            peso INTEGER DEFAULT 1,
            ultima_actualizacion TEXT,
            PRIMARY KEY (origen, destino)
        )
    ''')

    # 5. MACROECONOMÍA: El Cerebro Macro (Temperatura Global)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS macro_diario (
            fecha TEXT PRIMARY KEY,
            vix REAL,
            tnx REAL,
            petroleo REAL,
            dolar REAL
        )
    ''')

    # 6. CORRELACIONES: El Oráculo del MFE (Maximum Favorable Excursion)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS correlaciones (
            id_noticia TEXT,
            ticker TEXT,
            es_contagio INTEGER DEFAULT 0,
            sentimiento REAL,
            fiabilidad_fuente REAL, -- Aquí guardamos la "importancia" de 0 a 1
            divergencia_previa_pct REAL,
            precio_instante REAL,
            precio_mfe_60m REAL,
            impacto_mfe_60m_pct REAL,
            PRIMARY KEY (id_noticia, ticker)
        )
    ''')

    # 7. VECTORES DE ESTADO (Feature Engineering): El tensor de entrenamiento IA
    cursor.execute('''
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

    # 8. PAPER TRADING: El auditor del caos psicológico y la rentabilidad (Walk-Forward)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS paper_trading (
            id_operacion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_noticia TEXT,
            ticker TEXT,
            fecha_senal TEXT,
            horizonte_horas INTEGER,
            rendimiento_esperado_pct REAL,
            certeza_pct REAL,
            precio_entrada REAL,
            precio_salida_real REAL,
            rendimiento_real_pct REAL DEFAULT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("[+] Schema definitivo creado exitosamente en data/market_data.db")

if __name__ == "__main__":
    forjar_base_de_datos_definitiva()
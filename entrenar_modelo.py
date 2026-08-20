import sqlite3
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report

DB_PATH = "data/market_data.db"
MODEL_DIR = "modelos_ia"

# Crear directorio para guardar los modelos si no existe
os.makedirs(MODEL_DIR, exist_ok=True)

def cargar_dataset_entrenamiento():
    """Extrae y fusiona los datos del NLP y el Análisis Técnico."""
    conn = sqlite3.connect(DB_PATH)
    
    # Unimos la tabla de correlaciones con los vectores técnicos
    query = """
        SELECT 
            c.fiabilidad_fuente AS importancia, 
            c.sentimiento, 
            c.es_contagio,
            v.rsi, 
            v.momentum_pct, 
            v.atr,
            c.impacto_mfe_60m_pct
        FROM correlaciones c
        JOIN vectores_estado v ON c.id_noticia = v.id_noticia AND c.ticker = v.ticker
        WHERE c.fiabilidad_fuente > 0.0
    """
    
    df = pd.read_sql_query(query, conn)
    print(df)
    conn.close()
    
    # Limpieza de datos espurios o nulos que puedan romper la matemática
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()
    
    return df

def entrenar_cerebro_hibrido():
    df = cargar_dataset_entrenamiento()
    if df.empty or len(df) < 50:
        print("[!] No hay suficientes datos para entrenar. El bot necesita recolectar más historia (mínimo 50 eventos).")
        return

    print(f"[*] Entrenando Cerebro Híbrido con {len(df)} eventos históricos...")

    # 1. Definir el Vector de Características (X)
    X = df[['importancia', 'sentimiento', 'es_contagio', 'rsi', 'momentum_pct', 'atr']]
    
    # 2. Definir los Objetivos (Y)
    # Y_Regresion: El porcentaje exacto que se movió (Para el Rendimiento Esperado)
    y_regresion = df['impacto_mfe_60m_pct']
    
    # Y_Clasificacion: 1 si fue un trade rentable (> 0.2% de ganancia para superar comisiones), 0 si falló (Para la Certeza)
    y_clasificacion = (df['impacto_mfe_60m_pct'] > 0.2).astype(int)

    # Dividir datos: 80% para que el bot estudie, 20% para tomarle un examen (Walk-Forward Analysis)
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_regresion, y_clasificacion, test_size=0.2, random_state=42
    )

    # --- ENTRENAMIENTO DEL REGRESOR (Rendimiento U/D) ---
    print("\n[+] Entrenando Oráculo de Rendimiento (Random Forest Regressor)...")
    regresor = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
    regresor.fit(X_train, y_reg_train)
    
    predicciones_reg = regresor.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_reg_test, predicciones_reg))
    print(f"    -> Error Cuadrático Medio (RMSE): {rmse:.4f}% (Desviación esperada por el caos)")

    # --- ENTRENAMIENTO DEL CLASIFICADOR (Certeza P_u) ---
    print("\n[+] Entrenando Gestor de Riesgo (Random Forest Classifier)...")
    clasificador = RandomForestClassifier(n_estimators=200, max_depth=10, class_weight="balanced", random_state=42)
    clasificador.fit(X_train, y_clf_train)
    
    predicciones_clf = clasificador.predict(X_test)
    exactitud = accuracy_score(y_clf_test, predicciones_clf)
    print(f"    -> Exactitud (Accuracy): {exactitud * 100:.2f}%")
    print("    -> Reporte de Clasificación:")
    print(classification_report(y_clf_test, predicciones_clf, target_names=["Falla", "Éxito"]))

    # --- PERSISTENCIA DE LOS MODELOS ---
    ruta_reg = os.path.join(MODEL_DIR, "oraculo_rendimiento.pkl")
    ruta_clf = os.path.join(MODEL_DIR, "gestor_certeza.pkl")
    
    joblib.dump(regresor, ruta_reg)
    joblib.dump(clasificador, ruta_clf)
    
    print(f"\n[*] Entrenamiento exitoso. Modelos guardados en '{MODEL_DIR}'.")
    
    # Análisis de importancia de variables (Para entender cómo piensa la IA)
    importancias = regresor.feature_importances_
    variables = X.columns
    print("\n[*] ¿A qué le presta atención la IA? (Importancia de Variables):")
    for var, imp in sorted(zip(variables, importancias), key=lambda x: x[1], reverse=True):
        print(f"    - {var}: {imp * 100:.1f}%")

if __name__ == "__main__":
    entrenar_cerebro_hibrido()
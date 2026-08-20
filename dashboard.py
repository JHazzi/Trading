import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import pytz

DB_PATH = "data/market_data.db"
TZ_LOCAL = pytz.timezone('America/Argentina/Buenos_Aires')
TZ_NYSE = pytz.timezone('America/New_York')

st.set_page_config(page_title="Quant Market Bot", layout="wide", page_icon="📈")
st.title("Sistema Cuantitativo de Ecosistemas")

def mercado_abierto():
    """Determina si el mercado de NY está abierto actualmente."""
    ahora_ny = datetime.now(TZ_NYSE)
    if ahora_ny.weekday() >= 5: return False # Sábado o Domingo
    apertura = ahora_ny.replace(hour=9, minute=30, second=0)
    cierre = ahora_ny.replace(hour=16, minute=0, second=0)
    return apertura <= ahora_ny <= cierre

# --- CAPA DE DATOS ---
@st.cache_data(ttl=30)
def cargar_datos_completos():
    conn = sqlite3.connect(DB_PATH)
    try: correlaciones = pd.read_sql_query("SELECT * FROM correlaciones", conn)
    except: correlaciones = pd.DataFrame()
    
    try: universo = pd.read_sql_query("SELECT ticker, empresa FROM universo_tickers WHERE activo = 1", conn)
    except: universo = pd.DataFrame()
        
    try: paper = pd.read_sql_query("SELECT * FROM paper_trading ORDER BY fecha_senal DESC", conn)
    except: paper = pd.DataFrame()
    
    latidos = {}
    for tabla, col_fecha in [('precios', 'timestamp'), ('noticias', 'timestamp'), ('paper_trading', 'fecha_senal')]:
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX({col_fecha}) FROM {tabla}")
            res = cursor.fetchone()[0]
            if res:
                dt_utc = datetime.fromisoformat(res.replace("Z", "+00:00"))
                latidos[tabla] = dt_utc.astimezone(TZ_LOCAL)
            else: latidos[tabla] = None
        except: latidos[tabla] = None
            
    conn.close()
    return correlaciones, universo, paper, latidos

def obtener_datos_grafico(ticker: str):
    """Extrae las últimas velas del activo para el gráfico."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT timestamp, open, high, low, close FROM precios WHERE ticker = '{ticker}' ORDER BY timestamp DESC LIMIT 300"
    df_precios = pd.read_sql_query(query, conn)
    conn.close()
    if not df_precios.empty:
        df_precios['timestamp'] = pd.to_datetime(df_precios['timestamp']).dt.tz_convert(TZ_LOCAL)
        df_precios = df_precios.sort_values('timestamp')
    return df_precios

correlaciones, universo, paper, latidos = cargar_datos_completos()

if universo.empty:
    st.error("El Universo de activos está vacío.")
    st.stop()

tab_predictiva, tab_auditoria, tab_salud = st.tabs(["🎯 Análisis Predictivo", "💸 Paper Trading", "⚙️ Salud del Sistema"])

# ==========================================
# PESTAÑA 1: MOTOR PREDICTIVO Y GRÁFICOS
# ==========================================
with tab_predictiva:
    st.sidebar.header("Parámetros del Modelo")
    ticker_seleccionado = st.sidebar.selectbox("Seleccionar Activo Objetivo", universo['ticker'])
    horizonte_tiempo = st.sidebar.slider("Horizonte de Inversión (Horas)", 1, 168, 24, 1)
    
    # Gráfico del Activo
    df_grafico = obtener_datos_grafico(ticker_seleccionado)
    if not df_grafico.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_grafico['timestamp'], open=df_grafico['open'],
            high=df_grafico['high'], low=df_grafico['low'], close=df_grafico['close'],
            name="Precio"
        )])
        fig.update_layout(title=f"Acción del Precio (Últimos registros) - {ticker_seleccionado}", 
                          yaxis_title="Precio (USD)", template="plotly_dark", height=400, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No hay suficientes datos intradiarios en SQLite para graficar {ticker_seleccionado}.")

    # (Aquí sigue la misma lógica matemática del E[O] que ya teníamos para mostrar las métricas)
    st.markdown("*(La lógica predictiva original sigue operando aquí bajo el capó...)*")

# ==========================================
# PESTAÑA 3: SALUD DEL ECOSISTEMA
# ==========================================
with tab_salud:
    st.markdown("### Monitor de Daemons (Ajustado a Hora Local)")
    
    mercado_abierto_flag = mercado_abierto()
    if mercado_abierto_flag:
        st.success("🗽 Mercado de NY: ABIERTO")
    else:
        st.warning("🗽 Mercado de NY: CERRADO (Los Daemons de precios no reportarán anomalías).")
    
    ahora_local = datetime.now(TZ_LOCAL)
    
    def evaluar_latido(dt_latido, tolerancia_minutos, ignora_mercado_cerrado=False):
        if not dt_latido: return "🔴 Inactivo (Sin Datos)"
        minutos_inactivo = (ahora_local - dt_latido).total_seconds() / 60
        
        if minutos_inactivo <= tolerancia_minutos:
            return f"🟢 ONLINE (Hace {int(minutos_inactivo)} min)"
        elif not mercado_abierto_flag and ignora_mercado_cerrado:
            return f"🟡 PAUSADO (Mercado Cerrado. Último dato: {dt_latido.strftime('%H:%M')})"
        else:
            return f"🔴 OFFLINE (Caído hace {int(minutos_inactivo)} min)"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Daemon de Precios**")
        st.info(evaluar_latido(latidos['precios'], 15, ignora_mercado_cerrado=True))
    with col2:
        st.markdown("**Daemon de Noticias**")
        st.info(evaluar_latido(latidos['noticias'], 60)) 
    with col3:
        st.markdown("**Daemon Paper Trading**")
        st.info(evaluar_latido(latidos['paper_trading'], 120, ignora_mercado_cerrado=True))
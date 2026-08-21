import sqlite3
import networkx as nx
from collections import deque

DB_PATH = "data/market_data.db"

def cargar_grafo_mercado() -> nx.DiGraph:
    """Construye el grafo dirigido en memoria leyendo SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    G = nx.DiGraph()
    
    # Cargar Nodos (El universo de activos)
    cursor.execute("SELECT ticker FROM universo_tickers WHERE activo = 1")
    nodos = [fila[0] for fila in cursor.fetchall()]
    G.add_nodes_from(nodos)
    
    # Cargar Aristas (Relaciones con pesos extraídos por la IA)
    cursor.execute("SELECT origen, destino, peso FROM relaciones_organicas")
    aristas = cursor.fetchall()
    for origen, destino, peso in aristas:
        G.add_edge(origen, destino, weight=peso)
        
    conn.close()
    return G

def calcular_shock_contagio(ticker_origen: str, sentimiento_inicial: float, G: nx.DiGraph, alfa: float = 0.85, umbral_ruido: float = 0.05) -> dict:
    """
    Propaga el sentimiento usando BFS (Búsqueda en Anchura) con atenuación matemática.
    Simula el efecto dominó corporativo cortando las ramas irrelevantes.
    
    Args:
        ticker_origen: Ticker donde se originó la noticia.
        sentimiento_inicial: Fuerza de la noticia original (ej. 0.85).
        G: Grafo NetworkX cargado en memoria.
        alfa: Damping Factor (atenuación por cada salto de distancia).
        umbral_ruido: Impacto mínimo para ser considerado relevante.
    """
    impactos = {}
    
    # Verificamos si el ticker está en nuestra topología
    if ticker_origen not in G:
        return impactos
        
    # Cola para BFS: almacena tuplas de (nodo_actual, impacto_acumulado, nivel_profundidad)
    cola = deque([(ticker_origen, sentimiento_inicial, 0)])
    
    # Evita ciclos infinitos (ej. A contagia a B, B contagia a A)
    visitados = {ticker_origen}
    
    while cola:
        nodo_actual, impacto_actual, profundidad = cola.popleft()
        
        for vecino in G.successors(nodo_actual):
            if vecino in visitados:
                continue
                
            peso_relacion = G[nodo_actual][vecino]['weight']
            
            # MATEMÁTICA DEL CONTAGIO:
            # Impacto = (Fuerza Recibida) * (Fuerza de la Arista) * (Atenuación α)
            sentimiento_transferido = impacto_actual * peso_relacion * alfa
            
            # Filtro de Ruido: Cortamos la propagación si el impacto se vuelve marginal
            if abs(sentimiento_transferido) >= umbral_ruido:
                impactos[vecino] = round(sentimiento_transferido, 4)
                visitados.add(vecino)
                
                # Añadimos el vecino a la cola para que propague la onda hacia adelante
                cola.append((vecino, sentimiento_transferido, profundidad + 1))
                
    return impactos

if __name__ == "__main__":
    # Prueba de concepto aislada para verificar el BFS
    grafo = cargar_grafo_mercado()
    print("[*] Topología Neuronal cargada en memoria.")
    print(f"    Nodos: {grafo.number_of_nodes()}")
    print(f"    Aristas: {grafo.number_of_edges()}")
    
    # Simulamos una noticia brutal sobre NVIDIA
    ticker_noticia = "NVDA"
    sentimiento_noticia = 0.95 
    
    print(f"\n[!] EPICENTRO: Noticia de {ticker_noticia} con fuerza {sentimiento_noticia}")
    
    contagios = calcular_shock_contagio(ticker_noticia, sentimiento_noticia, grafo)
    
    if contagios:
        print("\n[*] Onda expansiva calculada (Efecto Dominó):")
        # Ordenamos los contagiados por la magnitud absoluta de su impacto
        contagios_ordenados = sorted(contagios.items(), key=lambda x: abs(x[1]), reverse=True)
        
        for afectado, impacto in contagios_ordenados:
            direccion = "Impulso (+)" if impacto > 0 else "Arrastre (-)"
            print(f"    -> {afectado}: {direccion} {impacto}")
    else:
        print("\n[*] El shock no tuvo la fuerza suficiente para propagarse o el nodo está aislado.")
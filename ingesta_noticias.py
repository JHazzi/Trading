import hashlib
import sqlite3
from datetime import datetime, timezone
import yfinance as yf

DB_PATH = "data/market_data.db"


def descargar_noticias(ticker: str):
    """Descarga noticias recientes del ticker y las guarda en SQLite.

    Maneja tanto el formato nuevo de yfinance (anidado en 'content') como el
    legado.
    """
    print(f"[*] Escaneando titulares para {ticker}...")
    activo = yf.Ticker(ticker)
    noticias = activo.news

    if not noticias:
        print(f"[!] No hay noticias recientes para {ticker}.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    nuevas = 0

    for n in noticias:
        # Detectar si la respuesta viene anidada en 'content' (formato nuevo)
        item = n.get("content", n)

        # 1. Extraer el Título
        titulo = item.get("title", "Sin título")

        # 2. Extraer el Link
        link = ""
        if "canonicalUrl" in item and isinstance(item["canonicalUrl"], dict):
            link = item["canonicalUrl"].get("url", "")
        elif "clickThroughUrl" in item and isinstance(
            item["clickThroughUrl"], dict
        ):
            link = item["clickThroughUrl"].get("url", "")
        else:
            link = item.get("link", "")

        if not link:
            continue  # Si no hay link para generar el hash, saltear

        # 3. Extraer la Fuente / Publisher
        fuente = "Desconocido"
        if "provider" in item and isinstance(item["provider"], dict):
            fuente = item["provider"].get("displayName", "Desconocido")
        else:
            fuente = item.get("publisher", "Desconocido")

        # 4. Extraer y formatear Fecha
        dt = None
        if "pubDate" in item:
            # Formato ISO (ej: '2025-01-15T12:30:00Z')
            try:
                dt = datetime.fromisoformat(
                    item["pubDate"].replace("Z", "+00:00")
                )
            except ValueError:
                dt = datetime.now(timezone.utc)
        elif "providerPublishTime" in item:
            # Formato Unix timestamp legado
            dt = datetime.fromtimestamp(
                item["providerPublishTime"], tz=timezone.utc
            )
        else:
            dt = datetime.now(timezone.utc)

        # Generar ID único
        id_noticia = hashlib.md5(link.encode()).hexdigest()

        try:
            cursor.execute(
                """
                INSERT INTO noticias (id, ticker, timestamp, titulo, fuente)
                VALUES (?, ?, ?, ?, ?)
            """,
                (id_noticia, ticker, dt.isoformat(), titulo, fuente),
            )
            nuevas += 1
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()
    print(
        f"[+] Se agregaron {nuevas} noticias nuevas a la base de datos para {ticker}."
    )


if __name__ == "__main__":
    descargar_noticias("AAPL")
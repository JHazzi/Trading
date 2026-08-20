import sqlite3
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DB_PATH = "data/market_data.db"
MODEL_NAME = "ProsusAI/finbert"
BATCH_SIZE = 32

# 1. Configuración de Hardware (Aprovecha tu RTX 4060)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[*] Usando dispositivo de cómputo: {device}")
if device.type == "cuda":
    print(f"[*] GPU detectada: {torch.cuda.get_device_name(0)}")

# 2. Carga del Modelo y Tokenizer
print("[*] Cargando modelo FinBERT...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, 
    use_safetensors=True
).to(device)
model.eval()
# Mapeo de etiquetas del modelo
# ProsusAI/finbert maneja: 0 -> positive, 1 -> negative, 2 -> neutral
LABELS = model.config.id2label


def procesar_noticias_pendientes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Obtener noticias sin procesar
    cursor.execute("SELECT id, titulo FROM noticias WHERE (sentimiento IS NULL OR grado IS NULL) AND importancia > 0.0")
    filas = cursor.fetchall()

    if not filas:
        print("[!] No hay noticias pendientes de clasificar.")
        conn.close()
        return

    print(f"[*] Analizando {len(filas)} noticias pendientes...")

    # Procesamiento por lotes (Batch processing)
    actualizaciones = []

    for i in range(0, len(filas), BATCH_SIZE):
        batch = filas[i : i + BATCH_SIZE]
        ids = [item[0] for item in batch]
        titulos = [item[1] for item in batch]

        # Tokenización
        inputs = tokenizer(
            titulos,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            # Aplicar Softmax para obtener probabilidades [0.0 a 1.0]
            probs = F.softmax(outputs.logits, dim=-1)

        for idx, prob in enumerate(probs):
            # Obtener la clase ganadora y su grado de certeza (score)
            max_prob, predicted_class_id = torch.max(prob, dim=-1)
            sentimiento = LABELS[predicted_class_id.item()]
            grado = round(max_prob.item(), 4)

            actualizaciones.append((sentimiento, grado, ids[idx]))

    # Actualizar la base de datos de forma masiva
    cursor.executemany(
        """
        UPDATE noticias 
        SET sentimiento = ?, grado = ?
        WHERE id = ?
    """,
        actualizaciones,
    )

    conn.commit()
    conn.close()
    print(f"[+] Se procesaron y actualizaron {len(actualizaciones)} noticias.")


if __name__ == "__main__":
    procesar_noticias_pendientes()
/**
 * Controlador Central de la API
 * Maneja todas las comunicaciones entre el Frontend JS y el Backend FastAPI.
 */

const BASE_URL = "http://localhost:8000/api";

const API = {
    // Función auxiliar para manejar respuestas y errores de red
    async fetchJSON(endpoint, options = {}) {
        try {
            const response = await fetch(`${BASE_URL}${endpoint}`, options);
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Error HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API Error] en ${endpoint}:`, error.message);
            throw error;
        }
    },

    // --- MÉTODOS DE LA API ---

    // Obtener estadísticas globales para la barra superior
    getEstadisticas: async () => {
        return await API.fetchJSON("/estadisticas");
    },

    // Obtener la configuración actual (para el panel de settings)
    getConfig: async () => {
        return await API.fetchJSON("/config");
    },

    // Guardar nueva configuración en el config.json del backend
    guardarConfig: async (nuevaConfig) => {
        return await API.fetchJSON("/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(nuevaConfig)
        });
    },

    // Obtener velas japonesas para ECharts
    getPrecios: async (ticker, limite = 100) => {
        return await API.fetchJSON(`/precios/${ticker}?limite=${limite}`);
    },

    // Obtener el feed de NLP (Zero-Shot & FinBERT)
    getNoticias: async (limite = 50) => {
        return await API.fetchJSON(`/noticias?limite=${limite}`);
    },

    // Obtener los nodos y aristas para Vis.js
    getTopologia: async () => {
        return await API.fetchJSON("/grafo");
    },
    
    getTickers: async () => {
        return await API.fetchJSON("/tickers");
    },
    // Obtener reporte proyectado a demanda
    getReporte: async (ticker, dias) => {
        return await API.fetchJSON(`/reporte/${ticker}?dias=${dias}`);
    },
};

// Exponer el objeto globalmente para que los módulos lo puedan usar
window.API = API;
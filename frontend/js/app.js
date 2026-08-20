/**
 * Orquestador Principal (app.js)
 * Maneja la navegación y delega tareas a los submódulos.
 */

// Estado de la aplicación para no recargar gráficos que ya se renderizaron
const AppState = {
    grafoCargado: false,
    tecnicoCargado: false
};

async function actualizarTopbar() {
    try {
        const data = await API.getEstadisticas();
        document.getElementById('hdr-noticias').innerText = data.noticias_totales.toLocaleString();
        document.getElementById('hdr-aristas').innerText = data.aristas_grafo.toLocaleString();
        document.getElementById('hdr-trades').innerText = data.operaciones_paper.toLocaleString();
    } catch(e) { 
        console.error("Error cargando Topbar:", e); 
    }
}

// Función global requerida por el evento 'onchange' del HTML
window.cargarGraficoVelas = function() {
    const ticker = document.getElementById('select-ticker').value;
    if (window.Tecnico) {
        window.Tecnico.cargarGrafico(ticker);
    }
};

// Lógica del enrutador de pestañas
window.switchTab = function(tabId) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    
    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');

    // Carga perezosa de submódulos
    if (tabId === 'tab-analisis' && !AppState.tecnicoCargado) {
        poblarTickers(); // CORRECTO: Primero llenamos el menú, luego esta función dibuja la vela
        AppState.tecnicoCargado = true;
    }
    if (tabId === 'tab-noticias' && !AppState.nlpCargado) {
        if (window.NLPFeed) window.NLPFeed.renderizar();
        AppState.nlpCargado = true;
    }
    if (tabId === 'tab-grafo' && !AppState.grafoCargado) {
        if (window.Topologia) window.Topologia.renderizar();
        AppState.grafoCargado = true;
    }
};

async function poblarTickers() {
    try {
        const tickers = await API.getTickers();
        const select = document.getElementById('select-ticker');
        
        // Limpiamos el HTML hardcodeado
        select.innerHTML = ""; 
        
        // Inyectamos el universo real
        tickers.forEach(t => {
            const option = document.createElement('option');
            option.value = t.ticker;
            option.textContent = `${t.ticker} - ${t.empresa}`;
            select.appendChild(option);
        });

        // Si la lista tiene elementos, graficamos el primero por defecto
        if (window.Tecnico && tickers.length > 0) {
            window.Tecnico.cargarGrafico(select.value);
        }
    } catch(e) {
        console.error("Error poblando tickers:", e);
    }
}

// Arranque inicial cuando el DOM está listo
document.addEventListener("DOMContentLoaded", () => {
    actualizarTopbar();
});
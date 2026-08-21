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

// --- Lógica del Generador de Reportes (Corregido y Expandido) ---

let chartProyeccionInstancia = null;

document.addEventListener("DOMContentLoaded", () => {
    actualizarTopbar();
    
    const slider = document.getElementById('slider-tiempo');
    const label = document.getElementById('lbl-horizonte');
    
    if (slider && label) {
        
        label.innerText = `${slider.value} Días`;
        
        slider.addEventListener('input', function() {
            const dias = parseInt(this.value);
            if (dias === 1) label.innerText = "1 Día";
            else if (dias < 7) label.innerText = `${dias} Días`;
            else if (dias === 7) label.innerText = "1 Semana";
            else if (dias < 30) label.innerText = `${Math.floor(dias/7)} Semanas`;
            else if (dias === 30) label.innerText = "1 Mes";
            else if (dias < 365) label.innerText = `${Math.floor(dias/30)} Meses`;
            else label.innerText = "1 Año";
        });
    }
});

// 2. Solicitar Reporte y Graficar el Cono de Incertidumbre
window.solicitarReporte = async function() {
    const ticker = document.getElementById('select-ticker').value;
    const dias = parseInt(document.getElementById('slider-tiempo').value);
    
    const tarjeta = document.getElementById('tarjeta-reporte');
    const contProyeccion = document.getElementById('contenedor-proyeccion');
    
    tarjeta.style.display = 'grid';
    contProyeccion.style.display = 'flex';
    
    document.getElementById('rep-rendimiento').innerText = '...';
    document.getElementById('rep-certeza').innerText = '...';
    document.getElementById('rep-tension').innerText = '...';

    // Inicializar ECharts si no existe
    if (!chartProyeccionInstancia) {
        chartProyeccionInstancia = echarts.init(document.getElementById('chart-proyeccion'));
        window.addEventListener('resize', () => chartProyeccionInstancia.resize());
    }
    chartProyeccionInstancia.showLoading({ color: '#3B82F6', maskColor: 'transparent' });

    try {
        const data = await API.getReporte(ticker, dias);
        
        const colorRend = data.rendimiento > 0 ? 'var(--bullish)' : 'var(--bearish)';
        const signo = data.rendimiento > 0 ? '+' : '';
        document.getElementById('rep-rendimiento').parentElement.firstElementChild.innerText = 'Rentabilidad Esperada';
        document.getElementById('rep-rendimiento').innerHTML = `<span style="color: ${colorRend}">${signo}${data.rendimiento}%</span>`;
        
        const colorCert = data.certeza > 70 ? 'var(--bullish)' : (data.certeza > 40 ? 'var(--warning)' : 'var(--bearish)');
        document.getElementById('rep-certeza').innerHTML = `<span style="color: ${colorCert}">${data.certeza}%</span>`;
        
        document.getElementById('rep-tension').innerText = data.tension;

        // Mostrar la Caja de Cristal (Razonamiento de la IA)
        const cajaCristal = document.getElementById('caja-cristal');
        cajaCristal.style.display = 'grid';
        cajaCristal.innerHTML = Object.entries(data.razonamiento).map(([clave, valor]) => `
            <div style="text-align: center;">
                <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">${clave}</div>
                <div style="font-size: 14px; font-weight: 600; color: var(--text-main); margin-top: 3px;">${valor}</div>
            </div>
        `).join('');

        // --- 2. Dibujar el Gráfico de Proyección (Paseo Aleatorio) ---
        const ejeDias = data.curva.map(d => d.dia_label);
        const lineaRendimiento = data.curva.map(d => d.rendimiento);
        const lineaCerteza = data.curva.map(d => d.certeza);

        const option = {
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
            legend: { data: ['Trayectoria Simulada', 'Nivel de Certeza'], textStyle: { color: '#64748B' } },
            grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
            xAxis: { type: 'category', data: ejeDias, boundaryGap: false, axisLine: { lineStyle: { color: '#2B303B' } }, axisLabel: { color: '#64748B' } },
            yAxis: [
                { type: 'value', name: 'Rendimiento (%)', nameTextStyle: { color: '#64748B' }, position: 'left', splitLine: { lineStyle: { color: '#151922' } }, axisLabel: { color: '#3B82F6', formatter: '{value}%' } },
                { type: 'value', name: 'Certeza (%)', nameTextStyle: { color: '#64748B' }, position: 'right', splitLine: { show: false }, axisLabel: { color: '#F59E0B', formatter: '{value}%' }, min: 0, max: 100 }
            ],
            series: [
                {
                    name: 'Trayectoria Simulada', 
                    type: 'line', 
                    data: lineaRendimiento, 
                    yAxisIndex: 0,
                    smooth: false, // APAGAMOS EL SMOOTH: Queremos ver el zig-zag realista del mercado
                    symbol: 'none',
                    lineStyle: { color: '#3B82F6', width: 2 },
                    areaStyle: { 
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
                            { offset: 1, color: 'rgba(59, 130, 246, 0.0)' }
                        ]) 
                    }
                },
                {
                    name: 'Nivel de Certeza', 
                    type: 'line', 
                    data: lineaCerteza, 
                    yAxisIndex: 1,
                    smooth: true, 
                    symbol: 'none', 
                    lineStyle: { color: '#F59E0B', width: 2, type: 'dashed' }
                }
            ]
        };
        
        chartProyeccionInstancia.setOption(option);
    } catch (error) {
        console.error("Error en reporte:", error);
        document.getElementById('rep-rendimiento').innerText = "Error";
    } finally {
        chartProyeccionInstancia.hideLoading();
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
    if (tabId === 'tab-config' && !AppState.configCargada) {
        if (window.ConfigMotor) window.ConfigMotor.cargarConfig();
        AppState.configCargada = true;
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


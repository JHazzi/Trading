/**
 * Módulo de Análisis Técnico (tecnico.js)
 * Controla el renderizado de la acción del precio y correlaciones.
 */

const Tecnico = {
    chartInstancia: null,

    init: function() {
        const contenedor = document.getElementById('chart-velas');
        if (!contenedor) return;
        
        // Inicializamos ECharts
        this.chartInstancia = echarts.init(contenedor);
        
        // Auto-redimensionado si cambia la ventana
        window.addEventListener('resize', () => {
            if (this.chartInstancia) this.chartInstancia.resize();
        });
    },

    cargarGrafico: async function(ticker) {
        if (!this.chartInstancia) this.init();

        this.chartInstancia.showLoading({
            text: 'Procesando tensores de precio...',
            color: '#3B82F6',
            maskColor: 'rgba(11, 14, 20, 0.8)',
            textColor: '#E2E8F0'
        });

        try {
            // Llamamos a tu backend usando el api.js
            const datos = await API.getPrecios(ticker, 150); 
            
            // ECharts espera formato OHLC: [Apertura, Cierre, Mínimo, Máximo]
            const fechas = datos.map(d => d.time.replace('T', ' ').slice(0, 16));
            const valores = datos.map(d => [d.open, d.close, d.low, d.high]);

            const option = {
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    axisPointer: { type: 'cross', lineStyle: { color: '#64748B' } }
                },
                grid: { left: '5%', right: '5%', bottom: '15%', top: '5%' },
                xAxis: {
                    type: 'category',
                    data: fechas,
                    boundaryGap: false,
                    axisLine: { lineStyle: { color: '#2B303B' } },
                    axisLabel: { color: '#64748B' }
                },
                yAxis: {
                    scale: true,
                    splitArea: { show: false },
                    splitLine: { lineStyle: { color: '#151922' } },
                    axisLabel: { color: '#64748B' }
                },
                dataZoom: [
                    { type: 'inside', start: 50, end: 100 },
                    { show: true, type: 'slider', bottom: 10, borderColor: '#2B303B' }
                ],
                series: [
                    {
                        name: ticker,
                        type: 'candlestick',
                        data: valores,
                        itemStyle: {
                            color: '#10B981',       // Cierre > Apertura (Bullish)
                            color0: '#EF4444',      // Cierre < Apertura (Bearish)
                            borderColor: '#10B981',
                            borderColor0: '#EF4444'
                        }
                    }
                ]
            };

            this.chartInstancia.setOption(option);
        } catch (error) {
            console.error("Error al graficar velas:", error);
            this.chartInstancia.clear();
        } finally {
            this.chartInstancia.hideLoading();
        }
    }
};

// Exponer el módulo globalmente
window.Tecnico = Tecnico;
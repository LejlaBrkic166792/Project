document.addEventListener('DOMContentLoaded', function() {
    const apiUrlElement = document.getElementById('api-url');
    const container = document.getElementById('charts-container');
    const spinner = document.getElementById('loading-spinner');
    const rangeLabel = document.getElementById('range-label');
    const template = document.getElementById('chart-template');
    
    // Bottone PDF globale (se presente nell'HTML)
    const downloadPdfBtn = document.getElementById('download-pdf-btn');

    let allCharts = [];
    let processedData = [];

    // Interrompi l'esecuzione se mancano elementi chiave nel DOM
    if (!apiUrlElement || !container || !template) return;


    function cleanValue(val) {
        // Pulisce le stringhe (rimuove % e converte virgole in punti)
        if (typeof val === 'string') {
            return parseFloat(val.replace(',', '.').replace('%', '').trim()) || 0;
        }
        return val || 0;
    }

    function calculateWeightedAverage(row) {
        // Calcola la media pesata (Punteggi da 1 a 4)
        const v1 = cleanValue(row["Decisamente No"] || 0);
        const v2 = cleanValue(row["Più No che Sì"] || 0);
        const v3 = cleanValue(row["Più Sì che No"] || 0);
        const v4 = cleanValue(row["Decisamente Sì"] || 0);
        
        const total = v1 + v2 + v3 + v4;
        return total > 0 ? ((v1*1 + v2*2 + v3*3 + v4*4) / total) : 0;
    }

    function extractYear(dataset) {
        // Estrae l'anno accademico (es. 2023_24) o usa il nome del file
        if (dataset.year !== 'N/D') return dataset.year;
        const match = dataset.filename.match(/\d{4}[\/_-]\d{2,4}/);
        return match ? match[0] : dataset.filename;
    }


    function processReportData(data) {
        const questionsCount = data[0].data_json.length;

        // Raggruppa i dati per singola domanda tracciandoli nel tempo
        for (let i = 0; i < questionsCount; i++) {
            let historicalSeries = data.map(dataset => {
                const row = dataset.data_json[i];
                const average = calculateWeightedAverage(row);

                return {
                    year: extractYear(dataset),
                    average: average.toFixed(2),
                    label: row["Domanda"]
                };
            });
            processedData.push(historicalSeries);
        }
    }

    // permette di mettere a capo le domande nel grafico
    function wrapTextByWords(text, maxWordsPerLine = 8) {
    if (!text) return '';
        const words = text.split(' ');
        let lines = [];
        
        for (let i = 0; i < words.length; i += maxWordsPerLine) {
            // Prende un blocco di parole (da 'i' a 'i + maxWordsPerLine') e le unisce con uno spazio
            lines.push(words.slice(i, i + maxWordsPerLine).join(' '));
        }
        
        return lines;
    }

    function initCharts() {
        container.innerHTML = ''; // Svuota lo spinner

        processedData.forEach((series, index) => {
            const clone = template.content.cloneNode(true);
            
            // NOTA: La riga che inseriva il testo nella classe .chart-title è stata rimossa 
            // per mantenere la domanda ESCLUSIVAMENTE dentro il grafico.
            
            const canvas = clone.querySelector('.chart-canvas');
            canvas.id = `chart-${index}`;
            
            // Cerca il bottone PNG all'interno del template clonato
            const downloadPngBtn = clone.querySelector('.download-png-btn');

            container.appendChild(clone);

            const ctx = canvas.getContext('2d');

            // --- Creazione Gradiente Premium ---
            let gradient = ctx.createLinearGradient(0, 0, 0, 350);
            gradient.addColorStop(0, 'rgba(13, 110, 253, 0.4)'); // Blu in alto
            gradient.addColorStop(1, 'rgba(13, 110, 253, 0.0)'); // Trasparente in basso

            const newChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: series.map(s => s.year),
                    datasets: [{
                        label: 'Media Punteggio', 
                        data: series.map(s => s.average),
                        borderColor: '#0d6efd',
                        backgroundColor: gradient, 
                        borderWidth: 3,
                        tension: 0.3, 
                        fill: true,
                        pointBackgroundColor: '#ffffff', 
                        pointBorderColor: '#0d6efd',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { 
                        
                        title: {
                            display: true,
                            text: wrapTextByWords(series[0].label, 20), 
                            font: {
                                size: 14,
                                family: 'Inter, sans-serif',
                                weight: 'bold'
                            },
                            color: '#212529',
                            padding: {
                                top: 10,
                                bottom: 15
                            }
                        },
                        
                        legend: { display: false },
                        tooltip: { 
                            backgroundColor: '#212529',
                            padding: 12,
                            cornerRadius: 8,
                            titleFont: { size: 14, family: 'Inter, sans-serif' },
                            bodyFont: { size: 13, family: 'Inter, sans-serif' },
                            displayColors: false
                        }
                    },
                    scales: {
                        x: { 
                            grid: { display: false, drawBorder: false } 
                        },
                        y: { 
                            min: 1, max: 4, 
                            ticks: { stepSize: 1, padding: 10 },
                            border: { display: false },
                            grid: { color: '#e9ecef', tickLength: 0 }, 
                            title: { display: true, text: 'Punteggio (1-4)' }
                        }
                    }
                }
            });

            // Logica Esportazione Singolo Grafico in PNG ---
            if (downloadPngBtn) {
                downloadPngBtn.addEventListener('click', function() {
                    const imageURL = newChart.toBase64Image();
                    const link = document.createElement('a');
                    link.download = `${series[0].label.substring(0, 30).replace(/[^a-z0-9]/gi, '_').toLowerCase()}_chart.png`;
                    link.href = imageURL;
                    link.click();
                });
            }

            allCharts.push(newChart);
        });
    }

    function initSlider(totalFiles) {
        $("#slider-range").slider({
            range: true,
            min: 0,
            max: totalFiles - 1,
            values: [0, totalFiles - 1],
            slide: function(event, ui) {
                updateAll(ui.values[0], ui.values[1]);
            }
        });
    }

    function updateAll(minIdx, maxIdx) {
        // Aggiorna etichetta del periodo (es. "2020/2021 — 2023/2024")
        const sampleSeries = processedData[0].slice(minIdx, maxIdx + 1);
        if (rangeLabel && sampleSeries.length > 0) {
            rangeLabel.textContent = `${sampleSeries[0].year} — ${sampleSeries[sampleSeries.length - 1].year}`;
        }

        // Aggiorna istantaneamente tutti i grafici
        allCharts.forEach((chart, i) => {
            const dataSlice = processedData[i].slice(minIdx, maxIdx + 1);
            chart.data.labels = dataSlice.map(s => s.year);
            chart.data.datasets[0].data = dataSlice.map(s => s.average);
            chart.update('none'); // L'animazione 'none' rende lo slider più reattivo
        });
    }


    if (downloadPdfBtn) {
        downloadPdfBtn.addEventListener('click', function() {
            const element = document.getElementById('charts-container');
            const rangeText = rangeLabel ? rangeLabel.textContent : "report";

            const options = {
                margin:       15, 
                filename:     `Report_Analytics_${rangeText.replace(/\s+/g, '_')}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true }, 
                jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
            };

            // Nasconde temporaneamente i bottoni PNG per non stamparli nel PDF
            const pngButtons = document.querySelectorAll('.download-png-btn');
            pngButtons.forEach(btn => btn.style.display = 'none');

            html2pdf().set(options).from(element).save().then(() => {
                // Riattiva i bottoni PNG terminato il salvataggio
                pngButtons.forEach(btn => btn.style.display = 'block');
            });
        });
    }

   
    fetch(apiUrlElement.value)
        .then(response => {
            if (!response.ok) throw new Error("Errore di rete API");
            return response.json();
        })
        .then(data => {
            if (spinner) spinner.style.display = 'none';
            
            // Gestione del caso "Materia senza file"
            if (!data || data.length === 0) {
                container.innerHTML = '<div class="col-12"><div class="alert alert-info shadow-sm text-center">Nessun report disponibile per questa materia.</div></div>';
                return;
            }

            processReportData(data);
            initCharts(); 
            initSlider(data.length);
            updateAll(0, data.length - 1);
        })
        .catch(error => {
            console.error("Errore recupero dati:", error);
            if (spinner) spinner.style.display = 'none';
            container.innerHTML = '<div class="col-12"><div class="alert alert-danger shadow-sm text-center"><i class="bi bi-exclamation-triangle-fill me-2"></i> Errore caricamento dati report.</div></div>';
        });
});
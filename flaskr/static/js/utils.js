
export function cleanValue(val) {
    if (typeof val === 'string') {
        return parseFloat(val.replace(',', '.').replace('%', '').trim()) || 0;
    }
    return val || 0;
}

export function calculateWeightedAverage(row) {
    if (!row) return null; 
    
    const v1 = cleanValue(row["Decisamente No"]);
    const v2 = cleanValue(row["Più No che Sì"]);
    const v3 = cleanValue(row["Più Sì che No"]);
    const v4 = cleanValue(row["Decisamente Sì"]);
    const nonSo = cleanValue(row['di cui "non so/non pertinente"']) || cleanValue(row["Non so/Non pertinente"]) || cleanValue(row["Non so"]) || 0;
    
    const total = v1 + v2 + v3 + v4 + nonSo;
    
    if (total === 0) return null;

    const pesoNonSo = 2.5; 
    const punteggioTotale = (v1 * 1) + (v2 * 2) + (v3 * 3) + (v4 * 4) + (nonSo * pesoNonSo);
    
    return {
        media: parseFloat((punteggioTotale / total).toFixed(2)),
        v1: v1, v2: v2, v3: v3, v4: v4, nonSo: nonSo, total: total
    };
    
}

export function extractYear(dataset) {
    if (dataset.year && dataset.year !== 'N/D') return dataset.year;
    const match = dataset.filename.match(/\d{4}[\/_-]\d{2,4}/);
    return match ? match[0] : dataset.filename;
}

export function groupDataByYearAndQuestion(datasets) {
    let grouped = {};
    datasets.forEach(ds => {
        const year = extractYear(ds);
        if (!grouped[year]) grouped[year] = {};

        ds.data_json.forEach(row => {
            let dom = row['Domanda'];
            let tipo = row['Tipo_Studenti'] || 'Frequentanti'; 
            let media = calculateWeightedAverage(row);
            
            if (media !== null) {
                if (!grouped[year][dom]) grouped[year][dom] = {};
                grouped[year][dom][tipo] = media;
            }
        });
    });
    return grouped;
}

export function extractQuestions(groupedData) {
    let questions = new Set();
    for (let year in groupedData) {
        for (let q in groupedData[year]) {
            questions.add(q);
        }
    }
    return questions;
}

export function getAverage(groupedData, year, question, tipo) {
    if (groupedData[year] && groupedData[year][question] && groupedData[year][question][tipo] !== undefined) {
        return groupedData[year][question][tipo];
    }
    return null; 
}

export function wrapTextByWords(text, maxWordsPerLine = 8) {
    if (!text) return '';
    const words = text.split(' ');
    let lines = [];
    for (let i = 0; i < words.length; i += maxWordsPerLine) {
        lines.push(words.slice(i, i + maxWordsPerLine).join(' '));
    }
    return lines;
}

// Crea il grafico standard (Line Chart)
export function createLineChart(ctx, labels, datasets, chartTitle = null) {
    return new Chart(ctx, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true, 
            maintainAspectRatio: false,
            parsing: {
                yAxisKey: 'media' 
            },
            plugins: { 
                title: {
                    display: chartTitle !== null,
                    text: chartTitle,
                    font: { size: 14, family: 'Inter, sans-serif', weight: 'bold' },
                    color: '#212529',
                    padding: { top: 5, bottom: 20 }
                },
                legend: { display: true, position: 'bottom' },
                tooltip: {        
                    callbacks: {
                        label: function(context) {
                            const raw = context.raw;
                            if (!raw) return `Nessun dato`;
                            
                            return [
                                `Media: ${raw.media}`,
                                `------------------------------`,
                                `Decisamente Sì: ${raw.v4}`,
                                `Più Sì che No: ${raw.v3}`,
                                `Più No che Sì: ${raw.v2}`,
                                `Decisamente No: ${raw.v1}`,
                                `Non so / Non pert.: ${raw.nonSo}`,
                                `Totale Partecipanti: ${raw.total}`
                            ];
                        }
                    }
                }
            },
            scales: { 
                y: { 
                    min: 1,
                    max: 4, 
                    ticks: { 
                        stepSize: 0.5,
                        callback: function(value) {
                            const mapping = {
                                1: 'Decisamente No (1)',
                                2: 'Più No che Sì (2)',
                                3: 'Più Sì che No (3)',
                                4: 'Decisamente Sì (4)'
                            };
                            return mapping[value] || ' ';
                        }
                    }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

// Configura il bottone per scaricare il singolo grafico (PNG)
export function setupPngDownload(buttonElement, chartInstance, filename) {
    if (!buttonElement || !chartInstance) return;
    buttonElement.addEventListener('click', () => {
        const link = document.createElement('a');
        link.download = filename;
        link.href = chartInstance.toBase64Image();
        link.click();
    });
}

// Configura il bottone per scaricare tutti i grafici (PDF)
export function setupPdfDownload(buttonElement, containerId, filename) {
    if (!buttonElement) return;
    buttonElement.addEventListener('click', function() {
        const element = document.getElementById(containerId);
        const pngButtons = document.querySelectorAll('.download-png-btn');
        
        pngButtons.forEach(btn => btn.style.display = 'none');

        html2pdf().set({
            margin: 15, 
            filename: filename, 
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true }, 
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        }).from(element).save().then(() => {
            pngButtons.forEach(btn => btn.style.display = 'block');
        });
    });
}
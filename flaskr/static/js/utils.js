// ==========================================
// FILE: static/js/utils.js
// Logica, Matematica, Grafica e Download
// ==========================================

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
    
    const total = v1 + v2 + v3 + v4;
    return total > 0 ? ((v1*1 + v2*2 + v3*3 + v4*4) / total) : null;
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
                grouped[year][dom][tipo] = parseFloat(media.toFixed(2));
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

// --- NUOVE UTILITY GRAFICHE E DI DOWNLOAD ---

// Crea il grafico standard (Line Chart)
export function createLineChart(ctx, labels, datasets, chartTitle = null) {
    return new Chart(ctx, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true, 
            maintainAspectRatio: false,
            plugins: { 
                // ECCO IL TITOLO INTEGRATO NEL CANVAS:
                title: {
                    display: chartTitle !== null,
                    text: chartTitle,
                    font: { size: 14, family: 'Inter, sans-serif', weight: 'bold' },
                    color: '#212529',
                    padding: { top: 5, bottom: 20 }
                },
                legend: { display: true, position: 'bottom' },
                tooltip: { backgroundColor: '#212529', padding: 12, cornerRadius: 8 }
            },
            scales: { 
                y: { min: 1, max: 4, ticks: { stepSize: 1 }, title: { display: true, text: 'Punteggio (1-4)' } },
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
        
        // Nasconde i bottoni PNG per non stamparli nel PDF
        pngButtons.forEach(btn => btn.style.display = 'none');

        html2pdf().set({
            margin: 15, 
            filename: filename, 
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true }, 
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        }).from(element).save().then(() => {
            // Ripristina i bottoni PNG al termine
            pngButtons.forEach(btn => btn.style.display = 'block');
        });
    });
}
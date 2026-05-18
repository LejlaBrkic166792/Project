import pandas as pd
import io

def estrai_valore(file_storage, etichetta):
    try:
        file_storage.seek(0)
        # Leggiamo fino a 50 righe per sicurezza
        for _ in range(25): 
            line = file_storage.readline().decode('utf-8-sig').strip()
            if etichetta in line:
                # Gestiamo sia virgola che punto e virgola
                parti = line.split(';') if ';' in line else line.split(',')
                if len(parti) > 1:
                    # Rimuoviamo spazi e virgolette (es: "2023/24" -> 2023/24)
                    valore = parti[1].strip()
                    return valore if valore else None
        return None
    except Exception as e:
        print(f"Errore estrazione {etichetta}: {e}")
        return None

def stat_csv(file_storage):
    try:
        # Estraiamo l'anno accademico prima di processare il CSV
        anno_accademico = estrai_valore(file_storage, "Anno Accademico:") or "0000/0000"
        
        file_storage.seek(0)
        lines = [line.decode('utf-8-sig').strip() for line in file_storage.readlines()]
        
        header_idx = -1
        for i, line in enumerate(lines):
            if line.startswith("Domanda"):
                header_idx = i
                break
        
        if header_idx == -1:
            raise ValueError("Impossibile trovare la riga di intestazione 'Domanda'.")

        file_storage.seek(0)
        df = pd.read_csv(
            io.BytesIO(file_storage.read()), 
            skiprows=header_idx, 
            encoding='utf-8-sig',
            sep=','
        )

        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['Domanda'])
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # AGGIUNTA: Inseriamo l'anno in ogni record per facilitare l'ordinamento nel DB
        records = df.to_dict(orient='records')
        for r in records:
            r['anno_accademico_metadata'] = anno_accademico
            
        return records

    except Exception as e:
        raise Exception(f"Errore nel file {file_storage.filename}: {str(e)}")

def ordina_datasets(datasets):
    
    def get_sort_key(ds):
        # Cerchiamo l'anno nel primo record del JSON salvato nel DB
        if ds.data_json and len(ds.data_json) > 0:
            return ds.data_json[0].get('anno_accademico_metadata', ds.filename)
        return ds.filename

    return sorted(datasets, key=get_sort_key)

def prepara_dataset_per_js(datasets):

    datasets_ordinati = ordina_datasets(datasets)
    return [
        {
            'filename': ds.filename,
            'data_json': ds.data_json,
            'anno': ds.data_json[0].get('anno_accademico_metadata', 'N/D') if ds.data_json else 'N/D'
        }
        for ds in datasets_ordinati
    ]
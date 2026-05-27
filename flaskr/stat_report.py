import pandas as pd
import io

def extract_metadata(file_storage, label):
    try:
        file_storage.seek(0)
        
        for _ in range(25): 
            line = file_storage.readline().decode('utf-8-sig').strip()
            if label in line:
                # Gestiamo sia virgola che punto e virgola
                parti = line.split(';') if ';' in line else line.split(',')
                if len(parti) > 1:
                    # Rimuoviamo spazi e virgolette 
                    value = parti[1].strip().strip('"')
                    return value if value else None
        return None
    except Exception:
        return None

#in caso se in futuro si vogliono controllare piu materie bisogna eliminare questa funzione
def validate_files_consistency(files):
   
    if not files or files[0].filename == '':
        return False, "Nessun file selezionato.", None

    reference_ad = extract_metadata(files[0], 'Attività Didattica (AD)')
    files[0].seek(0) 

    for file in files:
        if file and file.filename != '':
            current_ad = extract_metadata(file, 'Attività Didattica (AD)')
            file.seek(0)  
            
            if reference_ad and current_ad and current_ad != reference_ad:
                error_msg = f'Errore: il file "{file.filename}" appartiene a "{current_ad}", non a "{reference_ad}".'
                return False, error_msg, None

    return True, "", reference_ad

def csv_to_json(file_storage):
    try:
        # Estraiamo l'anno accademico prima di processare il CSV
        academic_year = extract_metadata(file_storage, "Anno Accademico:") or "0000/0000"
        
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
            sep=',',
            engine='python' #migliora la gestione dei csv sporchi
        )

        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['Domanda'])
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # AGGIUNTA: Inseriamo l'anno in ogni record per facilitare l'ordinamento nel DB
        records = df.to_dict(orient='records')
        for r in records:
            r['academic_year_metadata'] = academic_year
            
        return records

    except Exception as e:
        raise Exception(f"Errore nel file {file_storage.filename}: {str(e)}")

def sort_datasets(datasets):
    
    def get_sort_key(ds):
        # Cerchiamo l'anno nel primo record del JSON salvato nel DB
        if ds.data_json and len(ds.data_json) > 0:
            return ds.data_json[0].get('academic_year_metadata', ds.filename)
        return ds.filename

    return sorted(datasets, key=get_sort_key)

def prepare_datasets_for_js(datasets):

    sorted_datasets = sort_datasets(datasets)
    return [
        {
            'filename': ds.filename,
            'data_json': ds.data_json,
            'year': ds.data_json[0].get('academic_year_metadata', 'N/D') if ds.data_json else 'N/D'
        }
        for ds in sorted_datasets
    ]
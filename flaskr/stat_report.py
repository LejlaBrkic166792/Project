import pandas as pd
import io

def extract_metadata(file_storage, label):
    try:
        file_storage.seek(0)
        
        for _ in range(25): 
            line = file_storage.readline().decode('utf-8-sig').strip()
            if label in line:
                parti = line.split(';') if ';' in line else line.split(',')
                if len(parti) > 1:
                    value = parti[1].strip().strip('"')
                    return value if value else None
        return None
    except Exception:
        return None
    finally:
        # MIGLIORIA 1: Riavvolge SEMPRE il cursore alla fine, anche in caso di errore.
        # Così non dobbiamo più farlo manualmente nel resto del codice!
        file_storage.seek(0)

# in caso se in futuro si vogliono controllare piu materie bisogna eliminare questa funzione
def validate_files_consistency(files):
    if not files or files[0].filename == '':
        return False, "Nessun file selezionato.", None

    reference_ad = extract_metadata(files[0], 'Attività Didattica (AD)')

    for file in files:
        if file and file.filename != '':
            current_ad = extract_metadata(file, 'Attività Didattica (AD)')
            
            if reference_ad and current_ad and current_ad != reference_ad:
                error_msg = f'Errore: il file "{file.filename}" appartiene a "{current_ad}", non a "{reference_ad}".'
                return False, error_msg, None

    return True, "", reference_ad


def csv_to_json(file_storage):
    try:
        academic_year = extract_metadata(file_storage, "Anno Accademico:") or "0000/0000"
        
        # MIGLIORIA 2: Legge solo riga per riga senza caricare tutto in memoria
        header_idx = -1
        for i in range(50): # Cerca nelle prime 50 righe
            line = file_storage.readline().decode('utf-8-sig').strip()
            if line.startswith("Domanda"):
                header_idx = i
                break
        
        if header_idx == -1:
            raise ValueError("Impossibile trovare la riga di intestazione 'Domanda'.")

        file_storage.seek(0) # Riporta il cursore a zero prima di passare la palla a Pandas
        
        df = pd.read_csv(
            io.BytesIO(file_storage.read()), 
            skiprows=header_idx, 
            encoding='utf-8-sig',
            sep=',',
            engine='python'
        )

        # Pulizia colonne
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['Domanda'])
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Calcolo tipo studenti
        numero_domande = len(df)
        tipo_studenti = "Frequentanti" if numero_domande > 14 else "Non Frequentanti"

        # MIGLIORIA 3: Assegnazione veloce (vettorializzata) usando direttamente Pandas
        df['academic_year_metadata'] = academic_year
        df['Tipo_Studenti'] = tipo_studenti
        
        # Trasformazione finale in dizionario
        records = df.to_dict(orient='records')
        return records

    except Exception as e:
        raise Exception(f"Errore nel file {file_storage.filename}: {str(e)}")
    finally:
        file_storage.seek(0) # Buona norma per assicurarsi che il file sia pronto per futuri utilizzi

def sort_datasets(datasets):
    def get_sort_key(ds):
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

def validate_years_continuity(existing_datasets, new_files):
    all_years = set()

    # 1. Recupera gli anni dai dataset GIÀ SALVATI (leggendo il JSON)
    for ds in existing_datasets:
        if ds.data_json and len(ds.data_json) > 0:
            ay = ds.data_json[0].get('academic_year_metadata')
            if ay and ay != "0000/0000":
                try:
                    # Prende i primi 4 caratteri (es. "2021" da "2021/2022")
                    start_year = int(str(ay)[:4])
                    all_years.add(start_year)
                except ValueError:
                    pass

    # 2. Recupera gli anni dai NUOVI FILE
    for file in new_files:
        if file and file.filename != '':
            ay = extract_metadata(file, "Anno Accademico:")
            if ay:
                try:
                    start_year = int(str(ay)[:4])
                    all_years.add(start_year)
                except ValueError:
                    pass

    # 3. Controlla la continuità matematica
    if not all_years:
        return True, ""

    sorted_years = sorted(list(all_years))

    for i in range(1, len(sorted_years)):
        if sorted_years[i] != sorted_years[i-1] + 1:
            missing_start = sorted_years[i-1] + 1
            missing_end = missing_start + 1
            return False, f"Sequenza interrotta! Manca l'anno accademico {missing_start}/{missing_end}."

    return True, ""
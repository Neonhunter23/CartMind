import pandas as pd
import os
import re
import random
import numpy as np

# --- CONFIGURACIÓN ---
GARBAGE_NAMES = [
    'TABLES', 'CHAIRS', 'FURNITURE', 'BOOKCASES', 'PHONES',
    'BINDERS', 'ACCESSORIES', 'ART', 'MACHINES', 'PAPER',
    'FASTENERS', 'ENVELOPES', 'LABELS', 'STORAGE', 'APPLIANCES', 'COPIERS', 'SUPPLIES'
]


def clean_text(text):
    if pd.isna(text): return ""
    text = str(text).replace('\n', ' ').replace('\r', '')
    return re.sub(' +', ' ', text).strip()


def format_dims_safe(row):
    """Genera las dimensiones de forma segura, evitando errores si faltan columnas."""
    dims = []
    try:
        if pd.notna(row.get('width')): dims.append(f"Ancho: {row['width']}cm")
        if pd.notna(row.get('height')): dims.append(f"Alto: {row['height']}cm")
        if pd.notna(row.get('depth')): dims.append(f"Fondo: {row['depth']}cm")
    except:
        return "Medidas no disponibles"
    return ", ".join(dims) if dims else "Medidas no disponibles"


def process_data():
    print("INICIANDO PROCESAMIENTO (ETL + FUSIÓN + INYECCIÓN)...")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'Data')

    FURNITURE_FILE = 'IKEA_SA_Furniture_Web_Scrapings_sss.csv'
    SALES_FILE = 'IKEA SALES DATA.xlsx'
    OUTPUT_FILE = os.path.join(DATA_DIR, 'DecoMate_Master_Augmented.csv')

    # ==========================================
    # PASO 1: CARGA Y LIMPIEZA BÁSICA
    # ==========================================
    print(f"Leyendo archivos...")
    try:
        try:
            furniture_df = pd.read_csv(os.path.join(DATA_DIR, FURNITURE_FILE), encoding='utf-8')
        except:
            furniture_df = pd.read_csv(os.path.join(DATA_DIR, FURNITURE_FILE), encoding='latin-1')

        sales_path = os.path.join(DATA_DIR, SALES_FILE)
        sales_df = pd.read_excel(sales_path, engine='openpyxl')
    except Exception as e:
        print(f"❌ Error leyendo archivos: {e}")
        return

    # Renombrar columnas clave
    if 'ProductName' in sales_df.columns: sales_df = sales_df.rename(columns={'ProductName': 'name'})
    if 'UnitPrice' in sales_df.columns: sales_df = sales_df.rename(columns={'UnitPrice': 'price'})

    # --- CORRECCIÓN CLAVE AQUÍ ---
    # Generamos la columna 'dimensions' INMEDIATAMENTE después de cargar
    print("   📏 Calculando dimensiones...")
    # Aseguramos que existan las columnas base, si no, las creamos vacías
    for col in ['width', 'height', 'depth']:
        if col not in furniture_df.columns:
            furniture_df[col] = np.nan

    furniture_df['dimensions'] = furniture_df.apply(format_dims_safe, axis=1)

    # Limpieza de textos en el catálogo
    for col in ['name', 'category', 'short_description', 'designer']:
        if col in furniture_df.columns:
            furniture_df[col] = furniture_df[col].apply(clean_text)

    # Preparar claves de cruce
    sales_df['join_key'] = sales_df['name'].astype(str).str.split().str[0].str.upper().str.strip()
    furniture_df['join_key'] = furniture_df['name'].str.split().str[0].str.upper().str.strip()

    # Eliminar duplicados en el catálogo (quedándonos con la fila que ya tiene dimensions)
    furniture_unique = furniture_df.drop_duplicates(subset=['join_key'])

    # CRUCE (Ahora furniture_unique SÍ tiene 'dimensions')
    cols_to_merge = ['join_key', 'short_description', 'link', 'dimensions', 'category']
    # Filtramos solo las columnas que realmente existen para evitar KeyErrors futuros
    cols_to_merge = [c for c in cols_to_merge if c in furniture_unique.columns]

    df = pd.merge(sales_df, furniture_unique[cols_to_merge], on='join_key', how='left')

    # Limpieza de Basura y Precios
    df['name'] = df['join_key']  # Usar nombre corto
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
    df = df[df['price'] < 3000]  # Quitar errores
    df = df[df['price'] > 0]
    df = df[~df['name'].str.upper().isin(GARBAGE_NAMES)]

    # Rellenar categorías
    if 'category' not in df.columns: df['category'] = np.nan
    if 'ProductSubCategory' in df.columns: df['category'] = df['category'].fillna(df['ProductSubCategory'])
    df['category'] = df['category'].fillna("General")

    # ==========================================
    # PASO 2: FUSIÓN DE PEDIDOS
    # ==========================================
    print("Fusionando pedidos originales...")
    df = df.sort_values(['OrderDate', 'OrderID']).reset_index(drop=True)

    fusion_count = 0
    for i in range(1, len(df)):
        if random.random() < 0.35:
            current_id = df.at[i, 'OrderID']
            prev_id = df.at[i - 1, 'OrderID']
            if current_id != prev_id:
                df.at[i, 'OrderID'] = prev_id
                fusion_count += 1

    print(f"      - Se han fusionado {fusion_count} líneas.")

    # ==========================================
    # PASO 3: INYECCIÓN DE CATALOGO (Starter Pack)
    # ==========================================
    dummy_products = [
        {'name': 'ÄPPLARÖ', 'category': 'Outdoor', 'price': 149.0, 'short_description': 'Mesa jardín',
         'dimensions': '140x78 cm'},
        {'name': 'TÄRNÖ', 'category': 'Outdoor', 'price': 15.0, 'short_description': 'Silla plegable',
         'dimensions': 'Alto: 70cm'},
        {'name': 'MARKUS', 'category': 'Chairs', 'price': 179.0, 'short_description': 'Silla ergonómica',
         'dimensions': 'Alto: 140cm'},
        {'name': 'FLINTAN', 'category': 'Chairs', 'price': 79.0, 'short_description': 'Silla escritorio',
         'dimensions': 'Alto: 110cm'},
        {'name': 'MICKE', 'category': 'Tables', 'price': 89.0, 'short_description': 'Escritorio blanco',
         'dimensions': '73x50 cm'},
        {'name': 'HEKTAR', 'category': 'Lighting', 'price': 69.0, 'short_description': 'Lámpara pie',
         'dimensions': 'Alto: 180cm'},
        {'name': 'NYMÅNE', 'category': 'Lighting', 'price': 45.0, 'short_description': 'Lámpara techo',
         'dimensions': 'Ancho: 40cm'},
        {'name': 'VINDUM', 'category': 'Rugs', 'price': 149.0, 'short_description': 'Alfombra pelo largo',
         'dimensions': '200x270 cm'},
        {'name': 'STOCKHOLM', 'category': 'Decoration', 'price': 99.0, 'short_description': 'Espejo redondo',
         'dimensions': '80 cm'},
        {'name': 'MALM', 'category': 'Beds', 'price': 249.0, 'short_description': 'Cama alta',
         'dimensions': '160x200 cm'}
    ]

    dummy_rows = []
    existing = df['name'].astype(str).str.upper()
    for dp in dummy_products:
        if not existing.str.contains(dp['name'].upper()).any():
            row = df.iloc[0].copy()
            row['name'] = dp['name']
            row['category'] = dp['category']
            row['price'] = dp['price']
            row['short_description'] = dp['short_description']
            row['dimensions'] = dp['dimensions']
            row['link'] = f"https://www.ikea.com/es/es/search/products/?q={dp['name']}"
            row['OrderID'] = f"DEMO-{random.randint(1000, 9999)}"
            dummy_rows.append(row)

    if dummy_rows: df = pd.concat([df, pd.DataFrame(dummy_rows)], ignore_index=True)

    # ==========================================
    # PASO 4: REGLAS DE ASOCIACIÓN
    # ==========================================
    print("   💉 Inyectando complementos...")
    patterns = [
        {'trigger': 'ÄPPLARÖ', 'inject': 'TÄRNÖ', 'cat': 'Outdoor', 'price': 15.0, 'prob': 0.95},
        {'trigger': 'MICKE', 'inject': 'FLINTAN', 'cat': 'Chairs', 'price': 69.0, 'prob': 0.85},
        {'trigger': 'KIVIK', 'inject': 'LACK', 'cat': 'Tables', 'price': 10.0, 'prob': 0.8},
        {'trigger': 'EKTORP', 'inject': 'STRANDMON', 'cat': 'Chairs', 'price': 249.0, 'prob': 0.7},
        {'trigger': 'MALM', 'inject': 'NATTJASMIN', 'cat': 'Textiles', 'price': 29.99, 'prob': 0.8},
        {'trigger': 'HEKTAR', 'inject': 'TRÅDFRI', 'cat': 'Lighting', 'price': 15.0, 'prob': 0.9}
    ]

    new_rows = []
    df_temp = df.copy()
    df_temp['name_upper'] = df_temp['name'].astype(str).str.upper()

    for index, row in df_temp.iterrows():
        prod_name = row['name_upper']
        for p in patterns:
            if p['trigger'] in prod_name:
                if random.random() < p['prob']:
                    new_row = row.copy()
                    new_row['name'] = p['inject']
                    new_row['category'] = p['cat']
                    new_row['price'] = p['price']
                    new_row['Quantity'] = 1
                    new_row['OrderID'] = row['OrderID']
                    new_rows.append(new_row)

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    # ==========================================
    # PASO 5: GUARDADO
    # ==========================================
    df = df.sort_values(['OrderID', 'name'])

    # Si alguna columna no existe en el merge final, no la incluimos para evitar error
    possible_cols = ['OrderID', 'OrderDate', 'name', 'category', 'price', 'short_description', 'dimensions', 'link']
    final_cols = [c for c in possible_cols if c in df.columns]

    df[final_cols].to_csv(OUTPUT_FILE, index=False)
    print(f"✅ ¡LISTO! Dataset guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_data()
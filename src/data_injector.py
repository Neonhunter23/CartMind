import pandas as pd
import os
import random
import numpy as np


def inject_patterns():
    print("💉 INICIANDO SUPER-INYECCIÓN Y LIMPIEZA DE DATOS...")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Ajusta la ruta 'data' o 'Data' según tu carpeta real (Linux distingue mayúsculas)
    DATA_DIR = os.path.join(BASE_DIR, 'Data')


    INPUT_FILE = os.path.join(DATA_DIR, 'DecoMate_Master_Clean.csv')
    OUTPUT_FILE = os.path.join(DATA_DIR, 'DecoMate_Master_Augmented.csv')

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: No encuentro {INPUT_FILE}")
        return

    # 1. CARGA Y LIMPIEZA PREVIA (Crucial para evitar errores)
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"📊 Filas originales leídas: {len(df)}")
    except Exception as e:
        print(f"❌ Error crítico leyendo CSV: {e}")
        return

    # A) Arreglar PRECIOS (Convertir a numérico forzosamente)
    # Si hay comas, simbolos o texto, lo convertimos a NaN y luego a 0
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)

    # B) Arreglar CATEGORÍAS (Rellenar huecos vacíos)
    # Estrategia en cascada: category -> ProductSubCategory -> ProductCategory -> "General"
    if 'category' not in df.columns: df['category'] = np.nan
    if 'ProductSubCategory' in df.columns:
        df['category'] = df['category'].fillna(df['ProductSubCategory'])
    if 'ProductCategory' in df.columns:
        df['category'] = df['category'].fillna(df['ProductCategory'])

    df['category'] = df['category'].fillna("General")

    # C) Limpiar filas basura (sin OrderID o sin nombre)
    df = df.dropna(subset=['OrderID', 'name'])

    # --- 2. ASEGURAR PRODUCTOS BASE (Para que el buscador encuentre algo) ---
    dummy_products = [
        {'name': 'HEKTAR Floor Lamp', 'category': 'Lighting', 'price': 69.0,
         'short_description': 'Lámpara de pie estilo industrial', 'dimensions': 'Alto: 180cm'},
        {'name': 'NYMÅNE Ceiling Lamp', 'category': 'Lighting', 'price': 45.0,
         'short_description': 'Lámpara de techo moderna', 'dimensions': 'Ancho: 40cm'},
        {'name': 'VINDUM Rug', 'category': 'Rugs', 'price': 149.0, 'short_description': 'Alfombra pelo largo blanca',
         'dimensions': '200x270 cm'},
        {'name': 'STOCKHOLM Mirror', 'category': 'Decoration', 'price': 99.0,
         'short_description': 'Espejo redondo nogal', 'dimensions': '80 cm'}
    ]

    dummy_rows = []
    # Solo añadimos si no existen ya (búsqueda parcial insensible a mayúsculas)
    existing_names = df['name'].astype(str).str.upper()

    for dp in dummy_products:
        keyword = dp['name'].split()[0].upper()
        if not existing_names.str.contains(keyword).any():
            # Clonamos la primera fila para mantener la estructura de columnas
            row = df.iloc[0].copy()
            row['name'] = dp['name']
            row['category'] = dp['category']
            row['price'] = dp['price']
            row['short_description'] = dp['short_description']
            row['dimensions'] = dp['dimensions']
            row['OrderID'] = f"DEMO-{random.randint(1000, 9999)}"
            # Limpiamos campos irrelevantes para el dummy
            row['link'] = ""
            dummy_rows.append(row)

    if dummy_rows:
        df = pd.concat([df, pd.DataFrame(dummy_rows)], ignore_index=True)
        print(f"   ✨ Se han añadido {len(dummy_rows)} productos base.")

    # --- 3. INYECCIÓN DE REGLAS DE ASOCIACIÓN (Cross-Selling) ---
    patterns = [
        {'trigger': 'KIVIK', 'inject': 'LACK Table', 'cat': 'Tables', 'price': 10.0, 'prob': 0.8},
        {'trigger': 'EKTORP', 'inject': 'STRANDMON Chair', 'cat': 'Chairs', 'price': 249.0, 'prob': 0.7},
        {'trigger': 'STRANDMON', 'inject': 'LÖVBACKEN Table', 'cat': 'Tables', 'price': 79.0, 'prob': 0.6},
        {'trigger': 'MALM', 'inject': 'NATTJASMIN Sheet', 'cat': 'Textiles', 'price': 29.99, 'prob': 0.8},
        {'trigger': 'MICKE', 'inject': 'FLINTAN Chair', 'cat': 'Chairs', 'price': 69.0, 'prob': 0.8},
        {'trigger': 'HEKTAR', 'inject': 'TRÅDFRI Bulb', 'cat': 'Lighting', 'price': 15.0, 'prob': 0.9},
        {'trigger': 'NYMÅNE', 'inject': 'TRÅDFRI Remote', 'cat': 'Lighting', 'price': 12.0, 'prob': 0.7},
        {'trigger': 'BILLY', 'inject': 'OXBERG Door', 'cat': 'Storage', 'price': 35.0, 'prob': 0.6}
    ]

    new_rows = []
    # Optimizamos loop pre-calculando nombres en mayúsculas
    df['name_upper'] = df['name'].astype(str).str.upper()

    count_injected = 0
    for index, row in df.iterrows():
        prod_name = row['name_upper']

        for p in patterns:
            if p['trigger'] in prod_name:
                if random.random() < p['prob']:
                    new_row = row.copy()
                    new_row['name'] = p['inject']
                    new_row['category'] = p['cat']
                    new_row['price'] = p['price']
                    new_row['Quantity'] = 1
                    # IMPORTANTE: No cambiamos el OrderID, para que cuenten como compra conjunta
                    new_rows.append(new_row)
                    count_injected += 1

    # Eliminamos columna auxiliar
    df = df.drop(columns=['name_upper'])

    # Unir
    if new_rows:
        df_final = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    else:
        df_final = df

    # Ordenar y Guardar
    df_final = df_final.sort_values('OrderID')

    # Seleccionamos solo columnas útiles para limpiar el archivo final
    cols_wanted = ['OrderID', 'OrderDate', 'name', 'category', 'price', 'short_description', 'dimensions', 'link',
                   'designer']
    # Nos aseguramos de quedarnos solo con las que existen
    final_cols = [c for c in cols_wanted if c in df_final.columns]
    df_final = df_final[final_cols]

    df_final.to_csv(OUTPUT_FILE, index=False)

    print(f"✅ ¡PROCESO COMPLETADO!")
    print(f"   - Productos inyectados: {count_injected}")
    print(f"   - Total filas final: {len(df_final)}")
    print(f"💾 Guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    inject_patterns()
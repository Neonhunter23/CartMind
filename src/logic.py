import pandas as pd
import os


def load_catalog():
    """Carga el dataset optimizado."""
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Intentamos cargar el aumentado (el que tiene sillas y jardín)
    DATA_PATH = os.path.join(BASE_DIR, 'Data', 'DecoMate_Master_Augmented.csv')


    try:
        df = pd.read_csv(DATA_PATH)
        # Aseguramos que el precio es float para poder ordenar
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        # Aseguramos textos para búsqueda
        df['name'] = df['name'].fillna('').astype(str)
        df['short_description'] = df['short_description'].fillna('').astype(str)
        df['category'] = df['category'].fillna('').astype(str)
        return df
    except Exception as e:
        print(f"❌ Error cargando catálogo: {e}")
        return pd.DataFrame()


def search_products(intent, catalog_df):
    """
    Motor de búsqueda avanzado.
    """
    if catalog_df.empty:
        return pd.DataFrame()

    results = catalog_df.copy()

    # 1. FILTRO POR CATEGORÍA (El más potente)
    # Si la IA detectó una categoría válida (ej: "Chairs"), filtramos por ella.
    cat_filter = intent.get('category')
    if cat_filter and cat_filter in results['category'].unique():
        results = results[results['category'] == cat_filter]

    # 2. BÚSQUEDA POR PALABRAS CLAVE (Fuzzy Search)
    # Buscamos en Nombre Y Descripción
    keywords = intent.get('keywords') or intent.get('category_keyword')  # Compatibilidad

    if keywords and isinstance(keywords, str):
        # Limpiamos palabras vacías comunes
        keywords = keywords.lower().replace('cheap', '').replace('expensive', '').strip()

        if keywords:
            # Lógica: Contiene keyword en Nombre O en Descripción
            mask = (
                    results['name'].str.lower().str.contains(keywords, regex=False) |
                    results['short_description'].str.lower().str.contains(keywords, regex=False) |
                    results['category'].str.lower().str.contains(keywords, regex=False)
            )
            # Si el filtro de categoría fue muy estricto y nos dejó sin nada,
            # relajamos y buscamos en el catálogo
            if results[mask].empty and not results.empty:
                results = catalog_df[
                    catalog_df['name'].str.lower().str.contains(keywords, regex=False) |
                    catalog_df['short_description'].str.lower().str.contains(keywords, regex=False)
                    ]
            else:
                results = results[mask]

    # 3. FILTRO DE PRECIO
    max_price = intent.get('max_price')
    if max_price:
        try:
            results = results[results['price'] <= float(max_price)]
        except:
            pass  # Si falla la conversión, ignoramos filtro

    # 4. ORDENACIÓN
    sort_by = intent.get('sort_by', 'relevance')

    if sort_by == 'price_asc':
        results = results.sort_values('price', ascending=True)
    elif sort_by == 'price_desc':
        results = results.sort_values('price', ascending=False)
    else:
        # Relevancia simple: Priorizamos si la palabra clave está en el NOMBRE
        if keywords:
            results['is_exact_match'] = results['name'].str.lower().str.contains(keywords.lower(), na=False)
            results = results.sort_values(['is_exact_match', 'price'], ascending=[False, True])

    return results.head(5)  # Devolvemos top 5
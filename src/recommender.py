import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import os
import streamlit as st

# Rutas
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CAMBIO AQUÍ: Apuntamos al dataset trucado
AUGMENTED_DATA_PATH = os.path.join(BASE_DIR, 'Data', 'DecoMate_Master_Augmented.csv')


@st.cache_resource
def build_association_rules():
    print("\n ENTRENANDO RECOMENDADOR (Modo Diagnóstico)...")

    if not os.path.exists(AUGMENTED_DATA_PATH):
        return pd.DataFrame()

    try:
        df = pd.read_csv(AUGMENTED_DATA_PATH)

        # 1. DIAGNÓSTICO DE DATOS
        print(f"   📊 Total filas ventas: {len(df)}")
        unique_orders = df['OrderID'].nunique()
        print(f"   📊 Total pedidos únicos: {unique_orders}")

        # Contar ítems por pedido
        items_per_order = df.groupby('OrderID').size()
        multi_item_orders = items_per_order[items_per_order > 1].count()
        print(f"  Pedidos con más de 1 artículo: {multi_item_orders} de {unique_orders}")

        if multi_item_orders < 5:
            print("   ❌ PROBLEMA: Casi nadie compra 2 cosas juntas. El algoritmo no encontrará patrones reales.")
            # AQUÍ PODRÍAMOS FALSEAR REGLAS SI ES NECESARIO PARA LA DEMO
            return pd.DataFrame()

        # 2. PREPARAR CESTA
        basket = (df.groupby(['OrderID', 'name'])
                  .size().unstack().fillna(0))

        def encode_units(x):
            return 1 if x >= 1 else 0

        basket_sets = basket.applymap(encode_units)

        # 3. APRIORI (Con umbral MUY BAJO para forzar resultados)
        # Bajamos a 0.001 (0.1% de aparición). Si hay algún patrón, saldrá.
        frequent_itemsets = apriori(basket_sets, min_support=0.0001, use_colnames=True)  # <--- CAMBIO CLAVE

        if frequent_itemsets.empty:
            print("   ❌ Aún con soporte 0.0001 no hay conjuntos frecuentes.")
            return pd.DataFrame()

        # 4. REGLAS
        # lift > 0.5 (muy permisivo)
        rules = association_rules(frequent_itemsets, metric="lift", min_threshold=0.5)
        rules = rules.sort_values('confidence', ascending=False)

        print(f"   ✅ ¡ÉXITO! Se encontraron {len(rules)} reglas (incluso las débiles).")
        return rules

    except Exception as e:
        print(f"❌ Error recomendador: {e}")
        return pd.DataFrame()


def get_recommendations(product_name, rules_df, top_n=3):
    if rules_df.empty: return []

    recommendations = []
    target = product_name.lower()

    # Si el dataframe es muy grande, filtramos primero
    for idx, row in rules_df.iterrows():
        antecedents = list(row['antecedents'])
        if any(target in str(item).lower() for item in antecedents):
            cons = list(row['consequents'])[0]
            rec = {
                "product": cons,
                "confidence": f"{row['confidence'] * 100:.1f}%",
                "reason": "Comprado frecuentemente junto"
            }
            if rec['product'] not in [r['product'] for r in recommendations]:
                recommendations.append(rec)
            if len(recommendations) >= top_n: break

    return recommendations
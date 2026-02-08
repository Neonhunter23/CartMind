import streamlit as st
import pandas as pd
from ui_config import setup_ikea_style, display_header
from ai_engine import extract_search_intent, generate_sales_response
from logic import load_catalog, search_products
from recommender import build_association_rules, get_recommendations

# --- CONFIGURACIÓN ---
setup_ikea_style()
display_header()

# Cargar datos
if 'catalog' not in st.session_state:
    st.session_state.catalog = load_catalog()

# Cargar recomendador
if 'rules' not in st.session_state:
    with st.spinner("Inicializando IA..."):
        st.session_state.rules = build_association_rules()

# Historial
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "¡Hola! Soy DecoMate. ¿En qué puedo ayudarte hoy?"
    })

# --- INTERFAZ ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Escribe aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- LÓGICA ---
if st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]

    with st.spinner("Analizando..."):
        # 1. ENTENDER (Gemini)
        intent = extract_search_intent(last_user_msg)

        # 2. DEBUG SIDEBAR (¡Para ver si funciona!)
        with st.sidebar:
            st.warning("🔍 Debug IA (Lo que ha entendido):")
            st.json(intent)

        # 3. BUSCAR (Pandas)
        results = search_products(intent, st.session_state.catalog)

        response_text = ""

        if results.empty:
            response_text = "Lo siento, no encuentro nada con esos filtros. ¿Prueba con 'Mesa', 'Silla' o 'Sofá'?"
        else:
            # 4. RESPONDER
            top_product = results.iloc[0]

            # GENERADOR DE ENLACES IKEA ESPAÑA 🇪🇸
            # Truco: Creamos una URL de búsqueda directa
            product_name_clean = top_product['name'].replace(' ', '%20')  # KIVIK Sofa -> KIVIK%20Sofa
            ikea_es_link = f"https://www.ikea.com/es/es/search/products/?q={product_name_clean}"

            price_display = f"{top_product['price']} €"
            ai_pitch = generate_sales_response(top_product, last_user_msg)

            response_text = f"{ai_pitch}\n\n"

            # Usamos la variable ikea_es_link en lugar de top_product['link']
            response_text += f"**Mejor opción:** [{top_product['name']}]({ikea_es_link}) - **{price_display}**\n\n"

            # Recomendaciones (Cross-selling)
            recommendations = get_recommendations(top_product['name'], st.session_state.rules)
            if recommendations:
                response_text += "---\n### Nuestros clientes también han comprado:\n"
                for rec in recommendations:
                    # También generamos link para las recomendaciones
                    rec_link = f"https://www.ikea.com/es/es/search/products/?q={rec['product'].replace(' ', '%20')}"
                    response_text += f"➕ **[{rec['product']}]({rec_link})** ({rec['confidence']})\n\n"

            # Otras alternativas
            response_text += "---\n**Otras alternativas:**\n"
            for index, row in results.iloc[1:4].iterrows():
                alt_link = f"https://www.ikea.com/es/es/search/products/?q={row['name'].replace(' ', '%20')}"
                response_text += f"- [{row['name']}]({alt_link}) - {row['price']} €\n"

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()

# Sidebar Stats
with st.sidebar:
    st.divider()
    if 'catalog' in st.session_state:
        st.caption(f"Productos en catálogo: {len(st.session_state.catalog)}")
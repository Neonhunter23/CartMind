import streamlit as st
import pandas as pd
import time
from ui_config import setup_ikea_style, display_header
from ai_engine import extract_search_intent, generate_sales_response
from logic import load_catalog, search_products
from recommender import build_association_rules, get_recommendations

# --- CONFIGURACIÓN INICIAL ---
setup_ikea_style()

# --- BARRA LATERAL (SIDEBAR) MEJORADA ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/1024px-Ikea_logo.svg.png",
             width=100)
    st.markdown("## ⚙️ Panel de Control")

    # 1. KPIs (Datos del Catálogo)
    if 'catalog' not in st.session_state:
        st.session_state.catalog = load_catalog()

    df = st.session_state.catalog
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Productos", len(df))
    with col2:
        avg_price = f"{df['price'].mean():.0f}€" if not df.empty else "0€"
        st.metric("Precio Medio", avg_price)

    st.markdown("---")

    # 2. ATAJOS RÁPIDOS (Categorías)
    st.markdown("### 🗂️ Navegación Rápida")
    if st.button("🛋️ Salón"):
        st.session_state.messages.append({"role": "user", "content": "Busco muebles para el salón"})
        st.rerun()
    if st.button("🛏️ Dormitorio"):
        st.session_state.messages.append({"role": "user", "content": "Quiero cosas para el dormitorio"})
        st.rerun()
    if st.button("🌳 Exterior"):
        st.session_state.messages.append({"role": "user", "content": "Muebles para el jardín"})
        st.rerun()
    if st.button("💡 Iluminación"):
        st.session_state.messages.append({"role": "user", "content": "Busco iluminación"})
        st.rerun()

    st.markdown("---")

    # 3. HERRAMIENTAS DE DEMO (Para el profesor)
    st.markdown("### 🛠️ Zona Técnica")
    debug_mode = st.checkbox("Mostrar Cerebro IA (JSON)", value=False)
    if st.button("🗑️ Limpiar Chat"):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "¡Hola! Soy DecoMate. ¿En qué puedo ayudarte hoy?"
        })
        st.rerun()

# --- CABECERA PRINCIPAL ---
display_header()

# Cargar recomendador (Solo una vez)
if 'rules' not in st.session_state:
    with st.spinner("Inicializando motor de recomendación..."):
        st.session_state.rules = build_association_rules()

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "¡Hola! Soy DecoMate. ¿En qué puedo ayudarte hoy?"
    })

# --- MOSTRAR CHAT ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        # Si es mensaje del bot, puede tener formato especial, lo dejamos tal cual
        st.markdown(f'<div class="bot-msg">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

# --- LÓGICA DE RESPUESTA ---
if prompt := st.chat_input("Escribe aquí... (Ej: Quiero una mesa de jardín)"):
    # 1. Guardar y mostrar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Si el último mensaje es del usuario, generamos respuesta
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]

    with st.spinner("Analizando catálogo..."):
        # A) Entender Intención
        intent = extract_search_intent(last_user_msg)

        # MOSTRAR DEBUG SI ESTÁ ACTIVADO (Esto queda genial en la demo)
        if debug_mode:
            with st.expander("🧠 DEBUG: Lo que la IA ha entendido"):
                st.json(intent)

        # B) Buscar Productos
        results = search_products(intent, st.session_state.catalog)

        # C) Generar Respuesta
        if results.empty:
            response_text = "Lo siento, no he encontrado productos exactos para eso. ¿Podrías probar con otra categoría como 'Sofás' o 'Iluminación'?"
        else:
            top_product = results.iloc[0]

            # Formateo de precio seguro
            try:
                price_val = float(top_product['price'])
                price_display = f"{price_val:.2f} €"
            except:
                price_display = f"{top_product['price']} €"

            # Generar Link a IKEA España
            ikea_es_link = f"https://www.ikea.com/es/es/search/products/?q={top_product['name'].replace(' ', '%20')}"

            # Pitch de venta (IA)
            ai_pitch = generate_sales_response(top_product, last_user_msg)

            response_text = f"{ai_pitch}\n\n"
            response_text += f"⭐ **Recomendación Top:** [{top_product['name']}]({ikea_es_link}) - **{price_display}**\n\n"

            # Mostrar dimensiones si existen
            if str(top_product['dimensions']) != "nan" and str(top_product['dimensions']) != "":
                response_text += f"📏 *Medidas: {top_product['dimensions']}*\n\n"

            # Recomendaciones (Cross-selling)
            recommendations = get_recommendations(top_product['name'], st.session_state.rules)
            if recommendations:
                response_text += "---\n### 💡 Frecuentemente comprados juntos:\n"
                for rec in recommendations:
                    rec_link = f"https://www.ikea.com/es/es/search/products/?q={rec['product'].replace(' ', '%20')}"
                    response_text += f"➕ **[{rec['product']}]({rec_link})** ({rec['confidence']})\n\n"

            # Otras alternativas
            if len(results) > 1:
                response_text += "---\n**Otras opciones:**\n"
                for index, row in results.iloc[1:4].iterrows():
                    alt_link = f"https://www.ikea.com/es/es/search/products/?q={row['name'].replace(' ', '%20')}"
                    response_text += f"- [{row['name']}]({alt_link}) - {row['price']} €\n"

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()
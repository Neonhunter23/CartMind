import streamlit as st
import pandas as pd
from ui_config import setup_ikea_style, display_header
from ai_engine import extract_search_intent, generate_sales_response
from logic import load_catalog, search_products
from recommender import build_association_rules, get_recommendations
from semantic_search import SemanticIndex

# --- CONFIGURACIÓN INICIAL ---
setup_ikea_style()

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/1024px-Ikea_logo.svg.png",
             width=100)
    st.markdown("## ⚙️ Panel de Control")

    # KPIs
    if "catalog" not in st.session_state:
        st.session_state.catalog = load_catalog()

    df = st.session_state.catalog
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Productos", len(df))
    with col2:
        avg_price = f"{df['price'].mean():.0f}€" if not df.empty else "0€"
        st.metric("Precio Medio", avg_price)

    st.markdown("---")

    # Atajos rápidos
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

    # Zona técnica
    st.markdown("### 🛠️ Zona Técnica")
    debug_mode = st.checkbox("Mostrar Cerebro IA (JSON)", value=False)
    semantic_mode = st.checkbox("Búsqueda Semántica", value=True,
                                help="Usa embeddings para entender el significado, no solo palabras clave")
    if st.button("🗑️ Limpiar Chat"):
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant",
            "content": "¡Hola! Soy CartMind. ¿En qué puedo ayudarte hoy?"
        })
        st.rerun()

# --- CABECERA ---
display_header()

# Cargar recomendador (una vez)
if "rules" not in st.session_state:
    with st.spinner("Inicializando motor de recomendación (FP-Growth)..."):
        st.session_state.rules = build_association_rules()

# Cargar índice semántico (una vez)
if "semantic_index" not in st.session_state:
    with st.spinner("Cargando modelo de búsqueda semántica..."):
        idx = SemanticIndex()
        if not st.session_state.catalog.empty:
            idx.build(st.session_state.catalog)
        st.session_state.semantic_index = idx

# Inicializar historial
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "¡Hola! Soy CartMind. ¿En qué puedo ayudarte hoy?"
    })

# --- CHAT ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">👤 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">🤖 {msg["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Escribe aquí... (Ej: algo cómodo para ver la tele)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- RESPUESTA ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_msg = st.session_state.messages[-1]["content"]

    with st.spinner("Analizando..."):
        intent = extract_search_intent(last_user_msg)

        if debug_mode:
            with st.expander("🧠 DEBUG: Intención detectada"):
                st.json(intent)

        # Búsqueda: semántica si está activada, keyword como fallback
        search_used = "keyword"
        results = pd.DataFrame()

        if semantic_mode and st.session_state.semantic_index.is_ready:
            results = st.session_state.semantic_index.search(last_user_msg, top_k=5)
            # Aplicar filtro de precio si Gemini lo detectó
            max_price = intent.get("max_price")
            if not results.empty and max_price:
                filtered = results[results["price"] <= float(max_price)]
                if not filtered.empty:
                    results = filtered
            if not results.empty:
                search_used = "semantic"

        if results.empty:
            results = search_products(intent, st.session_state.catalog)

        if debug_mode:
            st.caption(f"🔍 Modo de búsqueda: **{search_used}**")

        if results.empty:
            response_text = "Lo siento, no he encontrado productos para eso. ¿Podrías intentarlo con otra descripción?"
        else:
            top_product = results.iloc[0]

            try:
                price_display = f"{float(top_product['price']):.2f} €"
            except (ValueError, TypeError):
                price_display = f"{top_product['price']} €"

            ikea_es_link = f"https://www.ikea.com/es/es/search/products/?q={top_product['name'].replace(' ', '%20')}"
            ai_pitch = generate_sales_response(top_product, last_user_msg)

            response_text = f"{ai_pitch}\n\n"
            response_text += f"⭐ **Recomendación Top:** [{top_product['name']}]({ikea_es_link}) - **{price_display}**\n\n"

            dims = str(top_product.get("dimensions", ""))
            if dims and dims != "nan":
                response_text += f"📏 *Medidas: {dims}*\n\n"

            recommendations = get_recommendations(top_product["name"], st.session_state.rules)
            if recommendations:
                response_text += "---\n### 💡 Frecuentemente comprados juntos:\n"
                for rec in recommendations:
                    rec_link = f"https://www.ikea.com/es/es/search/products/?q={rec['product'].replace(' ', '%20')}"
                    response_text += f"➕ **[{rec['product']}]({rec_link})** ({rec['confidence']} · lift {rec['lift']})\n\n"

            if len(results) > 1:
                response_text += "---\n**Otras opciones:**\n"
                for _, row in results.iloc[1:4].iterrows():
                    alt_link = f"https://www.ikea.com/es/es/search/products/?q={row['name'].replace(' ', '%20')}"
                    response_text += f"- [{row['name']}]({alt_link}) - {row['price']} €\n"

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()

import streamlit as st

# COLORES OFICIALES IKEA
IKEA_BLUE = "#0051ba"
IKEA_YELLOW = "#ffda1a"
IKEA_GREY = "#f5f5f5"


def setup_ikea_style():
    st.set_page_config(
        page_title="DecoMate | IKEA AI Assistant",
        page_icon="🛋️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS AVANZADO
    st.markdown(f"""
        <style>
        /* 1. FONDO GENERAL */
        .stApp {{
            background-color: white;
        }}

        /* 2. BARRA LATERAL (Azul IKEA) */
        section[data-testid="stSidebar"] {{
            background-color: {IKEA_BLUE};
        }}
        /* Textos de la sidebar en blanco */
        section[data-testid="stSidebar"] * {{
            color: white !important;
        }}
        /* Títulos de la sidebar */
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2 {{
            color: {IKEA_YELLOW} !important;
        }}

        /* 3. MENSAJES DEL CHAT */
        /* Usuario (Gris claro / Azul) */
        .stChatMessage[data-testid="user-message"] {{
            background-color: {IKEA_GREY};
            border-radius: 15px;
            padding: 10px;
        }}

        /* 4. BOTONES (Amarillo IKEA con texto azul) */
        div.stButton > button {{
            background-color: {IKEA_YELLOW};
            color: {IKEA_BLUE};
            border: none;
            border-radius: 25px;
            padding: 10px 25px;
            font-weight: 800; /* Extra bold */
            font-size: 16px;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }}
        div.stButton > button:hover {{
            background-color: #ffd000;
            transform: scale(1.05);
            color: {IKEA_BLUE};
        }}

        /* 5. INPUT DE TEXTO */
        .stTextInput > div > div > input {{
            border: 2px solid {IKEA_BLUE};
            border-radius: 20px;
            padding: 10px;
        }}

        /* 6. LINKS EN RESPUESTAS */
        a {{
            color: {IKEA_BLUE} !important;
            font-weight: bold;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}

        /* Divisor */
        hr {{
            border-top: 2px solid {IKEA_YELLOW};
        }}
        </style>
    """, unsafe_allow_html=True)


def display_header():
    """Muestra la cabecera con el Logo Oficial"""
    col1, col2 = st.columns([1, 6])

    with col1:
        # LOGO OFICIAL IKEA (Desde Wikimedia)
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/1024px-Ikea_logo.svg.png",
                 width=120)

    with col2:
        st.markdown(f"""
            <div style='padding-top: 10px;'>
                <h1 style='color: {IKEA_BLUE}; margin-bottom: 0px;'>DecoMate AI</h1>
                <p style='color: #666; font-size: 18px; margin-top: 0px;'>
                    <i>Tu asistente personal de diseño interior</i>
                </p>
            </div>
        """, unsafe_allow_html=True)

    # Línea amarilla decorativa
    st.markdown(f"<div style='height: 5px; background-color: {IKEA_YELLOW}; margin-bottom: 20px;'></div>",
                unsafe_allow_html=True)
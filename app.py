
import streamlit as st

# ==========================================
# CONFIGURACIÓN GENERAL
# ==========================================

st.set_page_config(
    page_title="EcoScan | Reciclaje inteligente",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTILOS
# ==========================================

st.markdown("""
<style>

.stApp {
    background-color: #F5F8F3;
}

section[data-testid="stSidebar"] {
    background-color: #E8F0E5;
}

.main-title {
    font-size: 48px;
    font-weight: 800;
    color: #205C3B;
    margin-bottom: 0;
}

.subtitle {
    color: #607568;
    font-size: 18px;
}

.info-card {
    background: white;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #E1E9DF;
    min-height: 190px;
}

.info-card h3 {
    color: #205C3B;
}

.info-card p {
    color: #52665A;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# BARRA LATERAL
# ==========================================

with st.sidebar:

    st.markdown("## ♻️ EcoScan")
    st.caption("Reciclaje inteligente")

    st.divider()

    st.markdown("### Navegación")

    st.page_link(
        "app.py",
        label="Inicio",
        icon="🏠"
    )

    st.page_link(
        "pages/1_EcoScan.py",
        label="EcoScan",
        icon="📷"
    )

    st.page_link(
        "pages/2_EcoStation.py",
        label="EcoStation",
        icon="🗑️"
    )

    st.divider()

    st.caption("Proyecto de Interfaces Multimodales")


# ==========================================
# PORTADA PRINCIPAL
# ==========================================

st.markdown(
    '<p class="main-title">♻️ EcoScan</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">La inteligencia artificial al servicio del reciclaje.</p>',
    unsafe_allow_html=True
)

st.write("")

st.markdown("""
EcoScan es un asistente inteligente que ayuda a identificar y
clasificar residuos mediante imágenes, voz y texto, indicando
cuál es la caneca adecuada para depositarlos.
""")

st.write("")


# ==========================================
# TARJETAS PRINCIPALES
# ==========================================

col1, col2 = st.columns(2)

with col1:

    st.markdown("""
    <div class="info-card">
        <h3>📷 EcoScan</h3>
        <p>
        Identifica residuos mediante fotografías, mensajes de voz
        o descripciones escritas y recomienda su clasificación.
        </p>
        <b>Reconocimiento multimodal</b>
    </div>
    """, unsafe_allow_html=True)


with col2:

    st.markdown("""
    <div class="info-card">
        <h3>🗑️ EcoStation</h3>
        <p>
        Visualiza la clasificación y comunica la categoría
        identificada al ESP32 para mover una flecha indicadora.
        </p>
        <b>Interacción con hardware simulado</b>
    </div>
    """, unsafe_allow_html=True)


st.write("")
st.divider()


# ==========================================
# CATEGORÍAS DE RESIDUOS
# ==========================================

st.subheader("Las tres categorías de EcoScan")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### ⚪ Blanca")
    st.write("Residuos aprovechables.")

with c2:
    st.markdown("### ⚫ Negra")
    st.write("Residuos no aprovechables.")

with c3:
    st.markdown("### 🟢 Verde")
    st.write("Residuos orgánicos aprovechables.")


st.write("")
st.divider()


# ==========================================
# CÓMO FUNCIONA
# ==========================================

st.subheader("¿Cómo funciona EcoScan?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📷 Imagen")
    st.write("Sube una fotografía del residuo.")

with col2:
    st.markdown("### 🎤 Voz")
    st.write("Describe verbalmente qué vas a desechar.")

with col3:
    st.markdown("### 💬 Texto")
    st.write("Escribe el nombre o descripción del residuo.")


st.write("")

st.info(
    "EcoScan busca facilitar la separación de residuos "
    "y promover hábitos de reciclaje responsables."
)

st.caption("EcoScan | Proyecto de Interfaces Multimodales")

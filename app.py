
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
# ESTILOS GENERALES
# ==========================================

st.markdown("""
<style>

/* FONDO GENERAL */
.stApp {
    background-color: #F5F8F3;
    color: #26382D;
}

/* TEXTOS GENERALES */
.stApp p,
.stApp span,
.stApp label,
.stApp li {
    color: #35483B;
}

/* TÍTULOS */
h1, h2, h3, h4 {
    color: #205C3B !important;
}

/* BARRA LATERAL */
section[data-testid="stSidebar"] {
    background-color: #E8F0E5;
}

section[data-testid="stSidebar"] * {
    color: #26382D !important;
}

/* TÍTULO PRINCIPAL */
.main-title {
    font-size: 48px;
    font-weight: 800;
    color: #205C3B !important;
    margin-bottom: 0;
}

.subtitle {
    color: #52665A !important;
    font-size: 18px;
}

/* TARJETAS */
.info-card {
    background: #FFFFFF;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #DCE7DC;
    min-height: 190px;
}

.info-card h3 {
    color: #205C3B !important;
}

.info-card p {
    color: #52665A !important;
}

/* BOTONES */
.stButton button {
    background-color: #205C3B;
    color: #FFFFFF !important;
    border: none;
    border-radius: 10px;
}

.stButton button p {
    color: #FFFFFF !important;
}

.stButton button:hover {
    background-color: #17472D;
    color: #FFFFFF !important;
}

/* MENSAJES INFORMATIVOS */
[data-testid="stAlert"] {
    background-color: #E5F1E5;
    color: #205C3B;
}

[data-testid="stAlert"] p {
    color: #205C3B !important;
}

/* ENLACES */
a {
    color: #205C3B !important;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# BARRA LATERAL Y NAVEGACIÓN
# ==========================================

with st.sidebar:

    st.markdown("## ♻️ EcoScan")
    st.caption("Reciclaje inteligente")

    st.divider()

    st.markdown("### Navegación")

    st.markdown("🏠 **Inicio**")

    if st.button("📷 EcoScan", use_container_width=True):
        st.switch_page("pages/1_EcoScan.py")

    if st.button("🗑️ EcoStation", use_container_width=True):
        st.switch_page("pages/2_EcoStation.py")

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
        <b style="color:#205C3B;">Reconocimiento multimodal</b>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button(
        "Comenzar a clasificar →",
        key="ir_ecoscan",
        use_container_width=True
    ):
        st.switch_page("pages/1_EcoScan.py")


with col2:

    st.markdown("""
    <div class="info-card">
        <h3>🗑️ EcoStation</h3>
        <p>
        Visualiza la clasificación y comunica la categoría
        identificada al ESP32 para mover una flecha indicadora.
        </p>
        <b style="color:#205C3B;">Interacción con hardware simulado</b>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    if st.button(
        "Ver estación inteligente →",
        key="ir_ecostation",
        use_container_width=True
    ):
        st.switch_page("pages/2_EcoStation.py")


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

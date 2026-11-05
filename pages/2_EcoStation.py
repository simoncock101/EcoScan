import streamlit as st

st.set_page_config(
    page_title="EcoStation",
    page_icon="🗑️",
    layout="wide"
)

st.title("🗑️ EcoStation")

st.write(
    "Visualiza la estación inteligente de reciclaje."
)

st.info(
    "Aquí conectaremos Streamlit con el ESP32 "
    "y el servomotor que indicará la caneca correcta."
)

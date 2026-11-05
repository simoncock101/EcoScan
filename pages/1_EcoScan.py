
import streamlit as st
import paho.mqtt.client as mqtt
import queue
import time
import uuid
import threading
import unicodedata

st.set_page_config(
    page_title="EcoScan",
    page_icon="📷",
    layout="wide"
)

# =====================================
# CONFIGURACION MQTT
# =====================================

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_CONTROL = "ecoscan/estacion/control"
TOPIC_ESTADO = "ecoscan/estacion/estado"


@st.cache_resource
def crear_conexion():
    mensajes = queue.Queue()
    conectado = threading.Event()
    suscrito = threading.Event()

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="EcoScan-Scan-" + uuid.uuid4().hex[:8]
    )

    def al_conectar(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            conectado.set()
            client.subscribe(TOPIC_ESTADO)

    def al_suscribirse(client, userdata, mid, reason_code_list, properties):
        if reason_code_list and reason_code_list[0].is_failure:
            return
        suscrito.set()

    def al_recibir(client, userdata, msg):
        mensajes.put(msg.payload.decode("utf-8"))

    client.on_connect = al_conectar
    client.on_subscribe = al_suscribirse
    client.on_message = al_recibir

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    return client, mensajes, conectado, suscrito


# =====================================
# CLASIFICACION DE RESIDUOS
# =====================================

def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def clasificar_residuo(texto):

    texto = normalizar(texto)

    ejemplos = {
        "BLANCA": [
            "botella plastica", "botella de plastico",
            "botella pet", "botella de agua",
            "papel limpio", "carton", "caja de carton",
            "lata", "lata de aluminio", "vidrio",
            "frasco de vidrio", "envase limpio",
            "periodico", "revista"
        ],

        "NEGRA": [
            "servilleta", "papel higienico",
            "papel sucio", "papel contaminado",
            "panal", "colilla", "icopor sucio",
            "empaque sucio", "residuo sanitario"
        ],

        "VERDE": [
            "cascara", "cascara de banano",
            "cascara de platano", "cascara de huevo",
            "restos de comida", "comida",
            "fruta", "verdura", "hojas",
            "residuos organicos", "borra de cafe"
        ]
    }

    for caneca, palabras in ejemplos.items():
        for palabra in palabras:
            if palabra in texto:
                return caneca

    return None


# =====================================
# INTERFAZ
# =====================================

st.title("📷 EcoScan")

st.write(
    "Tu asistente inteligente para identificar y separar residuos."
)

st.divider()

st.subheader("♻️ Identifica tu residuo")

st.write(
    "Escribe el nombre o describe el residuo que deseas clasificar."
)

descripcion = st.text_input(
    "¿Qué residuo quieres identificar?",
    placeholder="Ejemplo: botella de plástico"
)

if st.button("🔍 Identificar residuo", type="primary"):

    if not descripcion.strip():
        st.warning("Escribe primero una descripción.")

    else:
        caneca = clasificar_residuo(descripcion)

        if caneca is None:
            st.warning(
                "No pudimos identificar este residuo. "
                "Intenta describirlo de otra manera."
            )

        else:
            st.session_state["residuo"] = descripcion.upper()
            st.session_state["caneca"] = caneca
            st.session_state["clasificado"] = True

if st.session_state.get("clasificado", False):

    caneca = st.session_state["caneca"]
    residuo = st.session_state["residuo"]

    nombres = {
        "BLANCA": "Aprovechables",
        "NEGRA": "No aprovechables",
        "VERDE": "Orgánicos aprovechables"
    }

    emojis = {
        "BLANCA": "♻️",
        "NEGRA": "🗑️",
        "VERDE": "🌱"
    }

    st.divider()
    st.subheader("Resultado de identificación")

    st.success(
        f"Residuo identificado: {residuo}"
    )

    st.markdown(
        f"## {emojis[caneca]} Caneca {caneca}"
    )

    st.write(nombres[caneca])

    if st.button("🚀 Enviar a EcoStation", type="primary"):

        try:
            client, mensajes, conectado, suscrito = crear_conexion()

            if not conectado.wait(timeout=10):
                st.error("No se pudo conectar al broker MQTT.")
                st.stop()

            if not suscrito.wait(timeout=10):
                st.error("No se pudo suscribir al tópico de respuestas.")
                st.stop()

            # Limpiar respuestas anteriores
            while not mensajes.empty():
                try:
                    mensajes.get_nowait()
                except queue.Empty:
                    break

            # Preparar mensaje para Wokwi
            mensaje = f"{residuo[:20]}|{caneca}"

            resultado = client.publish(
                TOPIC_CONTROL,
                mensaje
            )

            if resultado.rc == mqtt.MQTT_ERR_SUCCESS:

                st.info("Orden enviada a EcoStation.")

                respuesta = None
                limite = time.time() + 10

                with st.spinner("Esperando respuesta de la estación..."):

                    while time.time() < limite:
                        try:
                            dato = mensajes.get(timeout=0.5)

                            if dato == f"OK|{residuo[:20]}|{caneca}":
                                respuesta = dato
                                break

                        except queue.Empty:
                            pass

                if respuesta:
                    st.success(
                        f"¡EcoStation confirmó la operación! {respuesta}"
                    )
                else:
                    st.warning(
                        "La orden fue enviada, pero no recibimos "
                        "confirmación de la estación."
                    )

            else:
                st.error("No se pudo enviar la orden MQTT.")

        except Exception as e:
            st.error(f"Error de comunicación: {e}")

st.divider()

st.subheader("🗑️ Código de separación colombiano")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### ⚪ Blanca")
    st.write("Papel, cartón, plástico, vidrio y metales limpios.")

with col2:
    st.markdown("### ⚫ Negra")
    st.write("Residuos no aprovechables y contaminados.")

with col3:
    st.markdown("### 🟢 Verde")
    st.write("Restos de comida y residuos orgánicos.")

st.divider()

st.caption("EcoScan | Reciclaje inteligente multimodal")

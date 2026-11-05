
import streamlit as st
import paho.mqtt.client as mqtt
import queue
import time
import uuid
import threading

st.set_page_config(
    page_title="EcoStation",
    page_icon="🗑️",
    layout="wide"
)

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
        client_id="EcoScan-" + uuid.uuid4().hex[:10]
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


st.title("🗑️ EcoStation")
st.write("Control remoto de la estación inteligente EcoScan.")

try:
    client, mensajes, conectado, suscrito = crear_conexion()

    if not conectado.wait(timeout=10):
        st.error("No se pudo conectar al broker MQTT.")
        st.stop()

    if not suscrito.wait(timeout=10):
        st.error("No se pudo suscribir al tópico de respuestas.")
        st.stop()

    st.success("Conectado y escuchando respuestas del ESP32.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.divider()
st.subheader("Enviar residuo a la estación")

residuos = {
    "Botella": ("BOTELLA", "BLANCA"),
    "Servilleta": ("SERVILLETA", "NEGRA"),
    "Cáscara": ("CASCARA", "VERDE")
}

seleccion = st.selectbox(
    "Selecciona un residuo:",
    list(residuos.keys())
)

if st.button("Enviar a EcoStation", type="primary"):
    # Limpiar confirmaciones anteriores
    while not mensajes.empty():
        try:
            mensajes.get_nowait()
        except queue.Empty:
            break

    residuo, caneca = residuos[seleccion]
    mensaje = f"{residuo}|{caneca}"

    resultado = client.publish(TOPIC_CONTROL, mensaje)

    if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
        st.success(f"Orden enviada: {mensaje}")

        respuesta = None

        with st.spinner("Esperando confirmación del ESP32..."):
            limite = time.time() + 10

            while time.time() < limite:
                try:
                    dato = mensajes.get(timeout=0.5)

                    if dato == f"OK|{residuo}|{caneca}":
                        respuesta = dato
                        break

                except queue.Empty:
                    pass

        if respuesta:
            st.success(f"¡Estación respondió correctamente! {respuesta}")
        else:
            st.warning(
                "La orden llegó a la estación, pero no recibimos "
                "su confirmación. Revisa la consola de Wokwi."
            )
    else:
        st.error("No se pudo enviar la orden MQTT.")

st.divider()
st.caption("EcoScan | Comunicación bidireccional ESP32 - Streamlit")

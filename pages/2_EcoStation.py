
import streamlit as st
import paho.mqtt.client as mqtt
import queue
import time
import uuid

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

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="EcoScan-Streamlit-" + uuid.uuid4().hex[:8]
    )

    def al_conectar(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(TOPIC_ESTADO)

    def al_recibir(client, userdata, msg):
        mensajes.put(msg.payload.decode("utf-8"))

    client.on_connect = al_conectar
    client.on_message = al_recibir

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    return client, mensajes


st.title("🗑️ EcoStation")
st.write("Control remoto de la estación inteligente EcoScan.")

try:
    client, mensajes = crear_conexion()
    st.success("Conexión MQTT iniciada.")
except Exception as e:
    st.error(f"No se pudo conectar al broker: {e}")
    st.stop()

st.divider()

st.subheader("Enviar residuo a la estación")

residuos = {
    "Botella": ("BOTELLA", "BLANCA"),
    "Servilleta": ("SERVILLETA", "NEGRA"),
    "Cáscara": ("CASCARA", "VERDE")
}

seleccion = st.selectbox(
    "Selecciona un residuo para probar:",
    list(residuos.keys())
)

if st.button("Enviar a EcoStation", type="primary"):
    residuo, caneca = residuos[seleccion]
    mensaje = f"{residuo}|{caneca}"

    resultado = client.publish(TOPIC_CONTROL, mensaje)

    if resultado.rc == mqtt.MQTT_ERR_SUCCESS:
        st.success(f"Orden enviada: {mensaje}")

        with st.spinner("Esperando respuesta del ESP32..."):
            respuesta = None
            limite = time.time() + 5

            while time.time() < limite:
                try:
                    respuesta = mensajes.get(timeout=0.5)
                    break
                except queue.Empty:
                    pass

        if respuesta:
            st.success(f"Respuesta del ESP32: {respuesta}")
        else:
            st.warning(
                "La orden se envió, pero no recibimos confirmación. "
                "Revisa la consola de Wokwi."
            )
    else:
        st.error("No se pudo publicar el mensaje.")

st.divider()

st.caption("EcoScan | Comunicación ESP32 mediante MQTT")

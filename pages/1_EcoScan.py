
import streamlit as st
import paho.mqtt.client as mqtt
import queue
import time
import uuid
import threading
import unicodedata
import re

st.set_page_config(
    page_title="EcoScan",
    page_icon="📷",
    layout="wide"
)

# ==========================================
# CONFIGURACION MQTT
# ==========================================

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


# ==========================================
# NORMALIZAR TEXTO
# ==========================================

def normalizar(texto):
    texto = texto.lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


# ==========================================
# CATALOGO DE RESIDUOS
# ==========================================

RESIDUOS_VERDES = [
    "cascara de banano",
    "cascara de platano",
    "cascara de naranja",
    "cascara de huevo",
    "cascara de papa",
    "cascara de fruta",
    "restos de comida",
    "sobras de comida",
    "restos de alimentos",
    "residuos organicos",
    "residuo organico",
    "borra de cafe",
    "posos de cafe",
    "bolsa de te",
    "hojas secas",
    "flores marchitas",
    "pasto",
    "hierba",
    "frutas",
    "verduras",
    "vegetales",
    "arroz",
    "pasta cocida",
    "pan",
    "cascaras",
    "comida sobrante"
]

RESIDUOS_NEGROS = [
    "papel higienico",
    "papel sanitario",
    "servilleta usada",
    "servilleta sucia",
    "papel contaminado",
    "papel grasoso",
    "papel con grasa",
    "panal",
    "panales",
    "toalla higienica",
    "tampon",
    "colilla de cigarrillo",
    "tapabocas usado",
    "residuos sanitarios",
    "papel encerado",
    "papel metalizado",
    "empaque contaminado",
    "empaque sucio",
    "icopor sucio",
    "algodon usado",
    "curita usada",
    "barrido",
    "polvo"
]

RESIDUOS_BLANCO = [
    "botella de plastico",
    "botella plastica",
    "botella pet",
    "botella de agua",
    "botella de gaseosa",
    "envase plastico limpio",
    "envase de plastico",
    "recipiente plastico limpio",
    "vaso plastico limpio",
    "bolsa plastica limpia",
    "plastico limpio",
    "papel limpio",
    "hoja de papel",
    "papel blanco",
    "periodico",
    "revista",
    "cuaderno",
    "carton limpio",
    "caja de carton limpia",
    "caja de cereal",
    "carton",
    "vidrio",
    "frasco de vidrio",
    "botella de vidrio",
    "tarro de vidrio",
    "lata de aluminio",
    "lata de gaseosa",
    "lata de cerveza",
    "lata de atun limpia",
    "aluminio",
    "metal limpio",
    "chatarra metalica",
    "envase tetrapak limpio",
    "tetrapak"
]

# Materiales que requieren limpieza antes de aprovecharse
MATERIALES_CONDICIONALES = [
    "caja de pizza",
    "envase de comida",
    "recipiente de comida",
    "frasco",
    "botella",
    "lata",
    "carton",
    "papel",
    "plastico",
    "vidrio"
]

# ==========================================
# RESIDUOS ESPECIALES
# ==========================================

RESIDUOS_ESPECIALES = [
    "camiseta",
    "camisa",
    "ropa",
    "pantalon",
    "jean",
    "zapatos",
    "tenis",
    "medicamento",
    "medicamentos",
    "pila",
    "pilas",
    "bateria",
    "baterias",
    "bombillo",
    "bombillos",
    "computador",
    "celular",
    "telefono",
    "electrodomestico",
    "aceite usado",
    "aceite de cocina usado",
    "pintura",
    "quimico",
    "residuo electronico",
    "aparato electronico"
]


# ==========================================
# CLASIFICADOR
# ==========================================

def contiene_palabra(texto, palabra):
    patron = r"\b" + re.escape(palabra) + r"\b"
    return re.search(patron, texto) is not None


def clasificar_residuo(descripcion):

    texto = normalizar(descripcion)

    if not texto:
        return None

    # 1. Detectar residuos especiales
    for residuo in RESIDUOS_ESPECIALES:
        if contiene_palabra(texto, residuo):
            return {
                "caneca": None,
                "tipo": "ESPECIAL",
                "mensaje": (
                    "Este residuo necesita una ruta especial. "
                    "Considera reutilizarlo, donarlo o llevarlo "
                    "a un punto de recoleccion autorizado."
                )
            }

    # 2. Detectar residuos sanitarios o contaminados
    for residuo in RESIDUOS_NEGROS:
        if contiene_palabra(texto, residuo):
            return {
                "caneca": "NEGRA",
                "tipo": "NO APROVECHABLE",
                "mensaje": "Deposita este residuo en la caneca negra."
            }

    palabras_contaminacion = [
        "sucio",
        "sucia",
        "grasoso",
        "grasosa",
        "contaminado",
        "contaminada",
        "con grasa",
        "con comida",
        "con aceite",
        "mojado"
    ]

    tiene_contaminacion = any(
        contiene_palabra(texto, palabra)
        for palabra in palabras_contaminacion
    )

    if tiene_contaminacion:
        for material in MATERIALES_CONDICIONALES:
            if contiene_palabra(texto, material):
                return {
                    "caneca": "NEGRA",
                    "tipo": "NO APROVECHABLE",
                    "mensaje": (
                        "El material presenta contaminacion "
                        "y no se puede aprovechar en estas condiciones."
                    )
                }

    # 3. Detectar residuos organicos
    for residuo in RESIDUOS_VERDES:
        if contiene_palabra(texto, residuo):
            return {
                "caneca": "VERDE",
                "tipo": "ORGANICO",
                "mensaje": "Este residuo puede ir a la caneca verde."
            }

    # 4. Detectar residuos aprovechables
    for residuo in RESIDUOS_BLANCO:
        if contiene_palabra(texto, residuo):
            return {
                "caneca": "BLANCA",
                "tipo": "APROVECHABLE",
                "mensaje": (
                    "Deposita este residuo limpio y seco "
                    "en la caneca blanca."
                )
            }

    # 5. No identificado
    return None


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

st.title("♻️ Identifica tu residuo")

st.write(
    "EcoScan te ayuda a identificar residuos y encontrar "
    "la forma correcta de separarlos."
)

st.divider()

st.subheader("🔎 Identificación por texto")

descripcion = st.text_input(
    "¿Qué residuo quieres identificar?",
    placeholder="Ejemplo: botella de gaseosa, camiseta vieja, caja de cartón..."
)

if st.button("🔍 Identificar residuo", type="primary"):

    st.session_state.pop("resultado_residuo", None)
    st.session_state.pop("descripcion_residuo", None)
    st.session_state.pop("error_clasificacion", None)

    resultado = clasificar_residuo(descripcion)

    if resultado is None:
        st.session_state["error_clasificacion"] = True
    else:
        st.session_state["error_clasificacion"] = False
        st.session_state["resultado_residuo"] = resultado
        st.session_state["descripcion_residuo"] = descripcion.upper()


if st.session_state.get("error_clasificacion", False):
    st.warning(
        "No pudimos identificar este residuo. "
        "Prueba con una descripción más específica."
    )


# ==========================================
# MOSTRAR RESULTADO
# ==========================================

resultado = st.session_state.get("resultado_residuo")

if resultado:

    caneca = resultado["caneca"]
    residuo = st.session_state["descripcion_residuo"]

    st.divider()
    st.subheader("Resultado de identificación")

    st.success(f"Residuo identificado: {residuo}")

    if caneca == "BLANCA":
        st.markdown("## ⚪ Caneca BLANCA")

    elif caneca == "NEGRA":
        st.markdown("## ⚫ Caneca NEGRA")

    elif caneca == "VERDE":
        st.markdown("## 🟢 Caneca VERDE")

    else:
        st.markdown("## ♻️ Residuo de manejo especial")

    st.write(resultado["mensaje"])

    # ======================================
    # ENVIAR A ESTACION
    # ======================================

    if caneca:

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

                # Preparar nombre corto para LCD
                residuo_mqtt = normalizar(descripcion).upper()
                residuo_mqtt = residuo_mqtt[:8].replace(" ", "_")

                mensaje = f"{residuo_mqtt}|{caneca}"

                resultado_envio = client.publish(
                    TOPIC_CONTROL,
                    mensaje
                )

                if resultado_envio.rc == mqtt.MQTT_ERR_SUCCESS:

                    st.info(f"Orden enviada a EcoStation: {mensaje}")

                    respuesta = None
                    limite = time.time() + 10

                    with st.spinner("Esperando respuesta del ESP32..."):

                        while time.time() < limite:
                            try:
                                dato = mensajes.get(timeout=0.5)

                                if dato == f"OK|{residuo_mqtt}|{caneca}":
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


# ==========================================
# GUIA DE SEPARACION
# ==========================================

st.divider()

st.subheader("🗑️ Código de separación colombiano")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### ⚪ Blanca")
    st.write(
        "Papel, cartón, plástico, vidrio y metales "
        "limpios y secos."
    )

with col2:
    st.markdown("### ⚫ Negra")
    st.write(
        "Residuos no aprovechables y materiales "
        "contaminados."
    )

with col3:
    st.markdown("### 🟢 Verde")
    st.write(
        "Restos de comida y residuos orgánicos aprovechables."
    )

st.divider()

st.caption(
    "EcoScan | Reciclaje inteligente multimodal"
)

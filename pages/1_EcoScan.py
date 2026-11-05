
import streamlit as st
import paho.mqtt.client as mqtt
import queue
import time
import uuid
import threading
import unicodedata
import re
import speech_recognition as sr

# ==========================================
# CONFIGURACION GENERAL
# ==========================================

st.set_page_config(
    page_title="EcoScan",
    page_icon="♻️",
    layout="wide"
)

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_CONTROL = "ecoscan/estacion/control"
TOPIC_ESTADO = "ecoscan/estacion/estado"


# ==========================================
# CONEXION MQTT
# ==========================================

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
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def contiene_palabra(texto, palabra):

    patron = r"\b" + re.escape(palabra) + r"\b"

    return re.search(patron, texto) is not None


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
# CLASIFICADOR DE RESIDUOS
# ==========================================

def clasificar_residuo(descripcion):

    texto = normalizar(descripcion)

    if not texto:
        return None

    # Residuos especiales

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

    # Residuos no aprovechables

    for residuo in RESIDUOS_NEGROS:

        if contiene_palabra(texto, residuo):

            return {
                "caneca": "NEGRA",
                "tipo": "NO APROVECHABLE",
                "mensaje": (
                    "Deposita este residuo en la caneca negra."
                )
            }

    # Detectar contaminacion

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

    # Residuos organicos

    for residuo in RESIDUOS_VERDES:

        if contiene_palabra(texto, residuo):

            return {
                "caneca": "VERDE",
                "tipo": "ORGANICO",
                "mensaje": (
                    "Este residuo puede ir a la caneca verde."
                )
            }

    # Residuos aprovechables

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

    return None


# ==========================================
# RECONOCIMIENTO DE VOZ
# ==========================================

def reconocer_voz(audio):

    reconocedor = sr.Recognizer()

    audio_datos = sr.AudioData(
        audio.getvalue(),
        sample_rate=audio.sample_rate,
        sample_width=audio.sample_width
    )

    texto = reconocedor.recognize_google(
        audio_datos,
        language="es-CO"
    )

    return texto


# ==========================================
# ENVIAR A ECOSTATION
# ==========================================

def enviar_a_estacion(residuo, caneca):

    client, mensajes, conectado, suscrito = crear_conexion()

    if not conectado.wait(timeout=10):
        return False, "No se pudo conectar al broker MQTT."

    if not suscrito.wait(timeout=10):
        return False, "No se pudo suscribir al tópico de respuestas."

    # Limpiar respuestas anteriores

    while not mensajes.empty():

        try:
            mensajes.get_nowait()

        except queue.Empty:
            break

    # Preparar nombre para LCD (maximo 8 caracteres)

    residuo_mqtt = normalizar(residuo).upper()

    residuo_mqtt = re.sub(
        r"[^A-Z0-9]",
        "_",
        residuo_mqtt
    )

    residuo_mqtt = residuo_mqtt[:8]

    mensaje = f"{residuo_mqtt}|{caneca}"

    resultado_envio = client.publish(
        TOPIC_CONTROL,
        mensaje
    )

    if resultado_envio.rc != mqtt.MQTT_ERR_SUCCESS:
        return False, "No se pudo enviar la orden MQTT."

    limite = time.time() + 10

    while time.time() < limite:

        try:

            dato = mensajes.get(timeout=0.5)

            if dato == f"OK|{residuo_mqtt}|{caneca}":
                return True, dato

        except queue.Empty:
            pass

    return False, "La estación no confirmó la operación."


# ==========================================
# MOSTRAR RESULTADO
# ==========================================

def mostrar_resultado(resultado, residuo, origen):

    st.divider()

    st.subheader(f"Resultado por {origen}")

    st.success(f"Residuo identificado: {residuo.upper()}")

    caneca = resultado["caneca"]

    if caneca == "BLANCA":
        st.markdown("## ⚪ Caneca BLANCA")

    elif caneca == "NEGRA":
        st.markdown("## ⚫ Caneca NEGRA")

    elif caneca == "VERDE":
        st.markdown("## 🟢 Caneca VERDE")

    else:
        st.markdown("## ♻️ Residuo de manejo especial")

    st.write(resultado["mensaje"])

    if caneca:

        if st.button(
            f"🚀 Enviar resultado de {origen} a EcoStation",
            key=f"enviar_{origen}"
        ):

            with st.spinner("Enviando a EcoStation..."):

                correcto, respuesta = enviar_a_estacion(
                    residuo,
                    caneca
                )

            if correcto:
                st.success(
                    f"¡EcoStation confirmó la operación! {respuesta}"
                )
            else:
                st.warning(respuesta)


# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================

st.title("♻️ EcoScan")

st.write(
    "Identifica tus residuos mediante texto o voz "
    "y descubre cómo separarlos correctamente."
)

st.divider()


# ==========================================
# IDENTIFICACION POR TEXTO
# ==========================================

st.subheader("✍️ Identificación por texto")

descripcion = st.text_input(
    "¿Qué residuo quieres identificar?",
    placeholder="Ejemplo: botella de gaseosa, camiseta vieja..."
)

if st.button(
    "🔍 Identificar por texto",
    type="primary"
):

    st.session_state.pop("resultado_texto", None)
    st.session_state.pop("error_texto", None)

    resultado = clasificar_residuo(descripcion)

    if resultado is None:

        st.session_state["error_texto"] = True

    else:

        st.session_state["resultado_texto"] = resultado
        st.session_state["descripcion_texto"] = descripcion


if st.session_state.get("error_texto", False):

    st.warning(
        "No pudimos identificar este residuo. "
        "Prueba con una descripción más específica."
    )


resultado_texto = st.session_state.get("resultado_texto")

if resultado_texto:

    mostrar_resultado(
        resultado_texto,
        st.session_state["descripcion_texto"],
        "texto"
    )


# ==========================================
# IDENTIFICACION POR VOZ
# ==========================================

st.divider()

st.subheader("🎙️ Identificación por voz")

st.write(
    "Pulsa el micrófono, menciona el residuo "
    "y EcoScan lo convertirá en texto para clasificarlo."
)

audio = st.audio_input(
    "Graba el nombre del residuo",
    key="audio_residuo"
)

if audio:

    if st.button(
        "🎧 Reconocer y clasificar voz",
        type="primary"
    ):

        st.session_state.pop("resultado_voz", None)
        st.session_state.pop("error_voz", None)

        try:

            with st.spinner("Reconociendo tu voz..."):

                texto_reconocido = reconocer_voz(audio)

            st.session_state["texto_reconocido"] = texto_reconocido

            resultado = clasificar_residuo(texto_reconocido)

            if resultado is None:

                st.session_state["error_voz"] = True

            else:

                st.session_state["error_voz"] = False
                st.session_state["resultado_voz"] = resultado

        except sr.UnknownValueError:

            st.session_state["error_voz_audio"] = (
                "No pudimos entender lo que dijiste. "
                "Intenta hablar más claro."
            )

        except sr.RequestError:

            st.session_state["error_voz_audio"] = (
                "No fue posible conectar con el servicio "
                "de reconocimiento de voz. Intenta nuevamente."
            )

        except Exception as e:

            st.session_state["error_voz_audio"] = (
                f"Error al procesar el audio: {str(e)}"
            )


if st.session_state.get("error_voz_audio"):

    st.error(st.session_state["error_voz_audio"])


if st.session_state.get("texto_reconocido"):

    st.info(
        "🎤 Lo que dijiste: "
        + st.session_state["texto_reconocido"]
    )


if st.session_state.get("error_voz", False):

    st.warning(
        "Escuchamos tu voz, pero no pudimos identificar "
        "el residuo. Intenta describirlo de otra manera."
    )


resultado_voz = st.session_state.get("resultado_voz")

if resultado_voz:

    mostrar_resultado(
        resultado_voz,
        st.session_state["texto_reconocido"],
        "voz"
    )


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
        "Residuos no aprovechables y materiales contaminados."
    )

with col3:

    st.markdown("### 🟢 Verde")

    st.write(
        "Restos de comida y residuos orgánicos aprovechables."
    )

st.divider()

st.caption(
    "EcoScan | Identificación por texto y voz"
)

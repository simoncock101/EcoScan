
import streamlit as st
import paho.mqtt.client as mqtt
import queue
import time
import uuid
import threading
import unicodedata
import re
import json
import io

from PIL import Image
from google import genai
from google.genai import types


st.set_page_config(
    page_title="EcoScan",
    page_icon="📷",
    layout="wide"
)

# ==========================================
# CONFIGURACION
# ==========================================

BROKER = "broker.hivemq.com"
PORT = 1883

TOPIC_CONTROL = "ecoscan/estacion/control"
TOPIC_ESTADO = "ecoscan/estacion/estado"

MODELO_GEMINI = "gemini-flash-latest"


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
# CONEXION GEMINI
# ==========================================

@st.cache_resource
def crear_cliente_gemini():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


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
# CLASIFICADOR POR TEXTO
# ==========================================

def clasificar_residuo(descripcion):

    texto = normalizar(descripcion)

    if not texto:
        return None

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

    for residuo in RESIDUOS_NEGROS:
        if contiene_palabra(texto, residuo):
            return {
                "caneca": "NEGRA",
                "tipo": "NO APROVECHABLE",
                "mensaje": "Deposita este residuo en la caneca negra."
            }

    palabras_contaminacion = [
        "sucio", "sucia", "grasoso", "grasosa",
        "contaminado", "contaminada", "con grasa",
        "con comida", "con aceite", "mojado"
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

    for residuo in RESIDUOS_VERDES:
        if contiene_palabra(texto, residuo):
            return {
                "caneca": "VERDE",
                "tipo": "ORGANICO",
                "mensaje": "Este residuo puede ir a la caneca verde."
            }

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
# IDENTIFICACION POR IMAGEN CON GEMINI
# ==========================================

def analizar_imagen(imagen):

    cliente = crear_cliente_gemini()

    instrucciones = """
    Eres EcoScan, un asistente especializado en separar residuos
    siguiendo el codigo de colores colombiano.

    Analiza la imagen e identifica el residuo principal.

    Reglas de clasificacion:

    BLANCA:
    Materiales aprovechables como papel, carton, plastico,
    vidrio y metales, siempre que esten limpios y secos.

    NEGRA:
    Residuos no aprovechables, sanitarios o materiales
    contaminados que no puedan recuperarse.

    VERDE:
    Residuos organicos aprovechables, como restos de comida
    y residuos vegetales.

    ESPECIAL:
    Pilas, medicamentos, aparatos electronicos, bombillos,
    quimicos, aceite usado y otros residuos que necesitan
    puntos de recoleccion o rutas especiales.
    La ropa y los zapatos deben orientarse preferiblemente
    a reutilizacion, donacion o recoleccion textil.

    IMPORTANTE:
    - No inventes objetos que no se vean.
    - Si no puedes identificar el objeto, usa NO_IDENTIFICADO.
    - Si no puedes determinar su estado de limpieza, explica
      que debe verificarse antes de depositarlo.
    - No clasifiques automaticamente un material como blanco
      si parece estar sucio o contaminado.
    - Devuelve exclusivamente un JSON valido.

    Usa exactamente esta estructura:

    {
      "residuo": "nombre corto del objeto",
      "caneca": "BLANCA, NEGRA, VERDE, ESPECIAL o NO_IDENTIFICADO",
      "tipo": "tipo de residuo",
      "mensaje": "explicacion breve en español",
      "confianza": "ALTA, MEDIA o BAJA"
    }
    """

    respuesta = cliente.models.generate_content(
        model=MODELO_GEMINI,
        contents=[
            instrucciones,
            imagen
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    resultado = json.loads(respuesta.text)

    canecas_validas = [
        "BLANCA",
        "NEGRA",
        "VERDE",
        "ESPECIAL",
        "NO_IDENTIFICADO"
    ]

    caneca = str(resultado.get("caneca", "")).upper()

    if caneca not in canecas_validas:
        raise ValueError("Gemini devolvio una clasificacion no valida.")

    resultado["caneca"] = caneca
    resultado["residuo"] = str(
        resultado.get("residuo", "Residuo")
    )

    resultado["tipo"] = str(
        resultado.get("tipo", "No identificado")
    )

    resultado["mensaje"] = str(
        resultado.get("mensaje", "")
    )

    resultado["confianza"] = str(
        resultado.get("confianza", "BAJA")
    ).upper()

    return resultado


# ==========================================
# FUNCION PARA ENVIAR A ECOSTATION
# ==========================================

def enviar_a_estacion(residuo, caneca):

    client, mensajes, conectado, suscrito = crear_conexion()

    if not conectado.wait(timeout=10):
        return False, "No se pudo conectar al broker MQTT."

    if not suscrito.wait(timeout=10):
        return False, "No se pudo suscribir al tópico de respuestas."

    while not mensajes.empty():
        try:
            mensajes.get_nowait()
        except queue.Empty:
            break

    # El LCD muestra maximo 8 caracteres
    residuo_mqtt = normalizar(residuo).upper()
    residuo_mqtt = re.sub(r"[^A-Z0-9]", "_", residuo_mqtt)
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
# INTERFAZ PRINCIPAL
# ==========================================

st.title("♻️ EcoScan")

st.write(
    "Identifica tus residuos mediante texto o imágenes "
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

if st.button("🔍 Identificar por texto", type="primary"):

    st.session_state.pop("resultado_texto", None)

    resultado = clasificar_residuo(descripcion)

    if resultado is None:
        st.session_state["error_texto"] = True
    else:
        st.session_state["error_texto"] = False
        st.session_state["resultado_texto"] = {
            **resultado,
            "residuo": descripcion
        }


if st.session_state.get("error_texto", False):
    st.warning(
        "No pudimos identificar este residuo. "
        "Prueba con una descripción más específica."
    )


# ==========================================
# RESULTADO TEXTO
# ==========================================

resultado_texto = st.session_state.get("resultado_texto")

if resultado_texto:

    st.divider()
    st.subheader("Resultado por texto")

    st.success(
        f"Residuo identificado: {resultado_texto['residuo']}"
    )

    caneca = resultado_texto["caneca"]

    if caneca == "BLANCA":
        st.markdown("## ⚪ Caneca BLANCA")
    elif caneca == "NEGRA":
        st.markdown("## ⚫ Caneca NEGRA")
    elif caneca == "VERDE":
        st.markdown("## 🟢 Caneca VERDE")
    else:
        st.markdown("## ♻️ Residuo especial")

    st.write(resultado_texto["mensaje"])

    if caneca:

        if st.button("🚀 Enviar resultado de texto a EcoStation"):

            with st.spinner("Enviando a EcoStation..."):
                correcto, respuesta = enviar_a_estacion(
                    resultado_texto["residuo"],
                    caneca
                )

            if correcto:
                st.success(f"EcoStation confirmó: {respuesta}")
            else:
                st.warning(respuesta)


# ==========================================
# IDENTIFICACION POR IMAGEN
# ==========================================

st.divider()
st.subheader("📷 Identificación por imagen")

st.write(
    "Carga una fotografía del residuo para que la inteligencia "
    "artificial lo analice."
)

archivo = st.file_uploader(
    "Selecciona una fotografía",
    type=["jpg", "jpeg", "png", "webp"],
    key="imagen_residuo"
)

if archivo:

    imagen = Image.open(io.BytesIO(archivo.getvalue())).convert("RGB")

    st.image(
        imagen,
        caption="Imagen seleccionada",
        use_container_width=True
    )

    if st.button("🤖 Analizar imagen con Gemini", type="primary"):

        st.session_state.pop("resultado_imagen", None)

        try:
            with st.spinner("Gemini está analizando el residuo..."):

                resultado = analizar_imagen(imagen)

                st.session_state["resultado_imagen"] = resultado

        except Exception as e:
            st.error(
                "No fue posible analizar la imagen. "
                "Verifica la conexión y la configuración de Gemini."
            )
            st.caption(str(e))


# ==========================================
# MOSTRAR RESULTADO DE IMAGEN
# ==========================================

resultado_imagen = st.session_state.get("resultado_imagen")

if resultado_imagen:

    st.divider()
    st.subheader("Resultado del análisis visual")

    st.success(
        f"Residuo identificado: {resultado_imagen['residuo']}"
    )

    caneca = resultado_imagen["caneca"]

    if caneca == "BLANCA":
        st.markdown("## ⚪ Caneca BLANCA")
    elif caneca == "NEGRA":
        st.markdown("## ⚫ Caneca NEGRA")
    elif caneca == "VERDE":
        st.markdown("## 🟢 Caneca VERDE")
    elif caneca == "ESPECIAL":
        st.markdown("## ♻️ Residuo de manejo especial")
    else:
        st.markdown("## ❓ Residuo no identificado")

    st.write(resultado_imagen["mensaje"])

    st.caption(
        f"Tipo: {resultado_imagen['tipo']} | "
        f"Confianza estimada: {resultado_imagen['confianza']}"
    )

    if caneca in ["BLANCA", "NEGRA", "VERDE"]:

        if st.button("🚀 Enviar resultado de imagen a EcoStation"):

            with st.spinner("Enviando a EcoStation..."):

                correcto, respuesta = enviar_a_estacion(
                    resultado_imagen["residuo"],
                    caneca
                )

            if correcto:
                st.success(
                    f"¡EcoStation confirmó la operación! {respuesta}"
                )
            else:
                st.warning(respuesta)


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
    "EcoScan | Identificación multimodal inteligente"
)

import requests
import webbrowser
import datetime
import random
import json
import re
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.storage import AppStorage
from kivy.utils import platform

# ========== CONFIGURACIÓN DE APIS ==========
WEATHER_API_KEY = "89e66808ba050748592e14483b243fa0"
NEWS_API_KEY = "a5bfa74319fc48ada1ba1c21fba33576"

# ========== ALMACENAMIENTO LOCAL ==========
STORAGE = AppStorage('jarvis_data')

# ========== FUNCIONES DE RED EN HILOS (NO BLOQUEAN LA UI) ==========
def run_in_thread(func, *args, callback=None):
    import threading
    def wrapper():
        result = func(*args)
        if callback:
            Clock.schedule_once(lambda dt: callback(result), 0)
    threading.Thread(target=wrapper, daemon=True).start()

def obtener_clima(ciudad):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={WEATHER_API_KEY}&units=metric&lang=es"
        r = requests.get(url, timeout=10)
        datos = r.json()
        if datos.get('cod') != 200:
            return f"No encontré '{ciudad}'. Prueba: Madrid, Mexico, London"
        temp = datos['main']['temp']
        desc = datos['weather'][0]['description']
        humedad = datos['main']['humidity']
        return f"🌡️ {ciudad}: {temp}°C, {desc}\n💧 Humedad: {humedad}%"
    except:
        return "Error de clima"

def obtener_noticias():
    try:
        for pais in ["mx", "es"]:
            url = f"https://newsapi.org/v2/top-headlines?country={pais}&apiKey={NEWS_API_KEY}"
            r = requests.get(url, timeout=10)
            noticias = r.json().get('articles', [])
            if noticias:
                resultado = f"📰 NOTICIAS DE {'MÉXICO' if pais == 'mx' else 'ESPAÑA'}:\n\n"
                for n in noticias[:3]:
                    titulo = n.get('title', '')[:60]
                    if titulo and titulo != "[Removed]":
                        resultado += f"• {titulo}\n"
                return resultado
        return "No hay noticias disponibles"
    except:
        return "Error de noticias"

def traducir_texto(texto, idioma):
    try:
        url = f"https://api.mymemory.translated.net/get?q={texto}&langpair=es|{idioma[:2]}"
        r = requests.get(url, timeout=10)
        return r.json()["responseData"]["translatedText"]
    except:
        return f"🌐 No pude traducir a {idioma}"

# ========== MEMORIA Y RECORDATORIOS ==========
def guardar_memoria(usuario, jarvis):
    try:
        memoria = STORAGE.get('memoria', [])
        memoria.append({"usuario": usuario, "jarvis": jarvis, "fecha": str(datetime.datetime.now())})
        STORAGE.put('memoria', memoria[-50:])
    except:
        pass

def recordar_conversacion():
    try:
        memoria = STORAGE.get('memoria', [])
        if memoria:
            recuerdo = random.choice(memoria)
            return f"📝 Recuerdo que una vez me dijiste: '{recuerdo['usuario']}' y yo respondí: '{recuerdo['jarvis']}'"
    except:
        pass
    return None

def guardar_recordatorio(texto):
    try:
        recordatorios = STORAGE.get('recordatorios', [])
        recordatorios.append({"texto": texto, "fecha": str(datetime.datetime.now())})
        STORAGE.put('recordatorios', recordatorios[-20:])
        return True
    except:
        return False

def mostrar_recordatorios():
    try:
        recordatorios = STORAGE.get('recordatorios', [])
        if recordatorios:
            resultado = "📋 TUS RECORDATORIOS:\n\n"
            for i, r in enumerate(recordatorios[-5:], 1):
                resultado += f"{i}. {r['texto']}\n"
            return resultado
    except:
        pass
    return "📋 No tienes recordatorios guardados"

# ========== JUEGOS Y EXTRAS ==========
def piedra_papel_tijera(jugador):
    opciones = ["piedra", "papel", "tijera"]
    compu = random.choice(opciones)
    if jugador == compu:
        return f"🤝 Empate! Ambos {jugador}"
    elif (jugador == "piedra" and compu == "tijera") or (jugador == "papel" and compu == "piedra") or (jugador == "tijera" and compu == "papel"):
        return f"🎉 ¡Ganaste! {jugador} vence a {compu}"
    return f"😅 Perdiste. {compu} vence a {jugador}"

def adivinanza():
    preguntas = [
        {"p": "¿Qué tiene dientes pero no come?", "r": "el peine"},
        {"p": "¿Qué es blanco como la nieve y negro como el carbón?", "r": "el periódico"},
        {"p": "¿Qué cosa es que cuanto más le quitas, más grande se hace?", "r": "el agujero"},
    ]
    return random.choice(preguntas)

def chiste():
    chistes = [
        "🤣 ¿Qué le dice un techo a otro? ¡Techo de menos!",
        "😂 ¿Qué hace una abeja en el gimnasio? ¡Zum-ba!",
        "😄 ¿Cómo se llama el campeón de buceo japonés? Tokofondo.",
    ]
    return random.choice(chistes)

FRASES = {
    "bienvenida": ["¡Hola! Soy Jarvis 🦾", "¡Buenas! Jarvis al servicio 🤖", "¡Saludos! ✨"],
    "gracias": ["¡De nada! 😊", "Un placer 👍", "¡Para eso estoy! 🫡"],
    "despedida": ["👋 ¡Hasta luego!", "🤖 Nos vemos", "👋 ¡Adiós!"],
    "motivacion": ["💪 ¡Tú puedes!", "🌟 Sigue adelante", "🚀 Tú puedes lograr lo que te propongas"]
}

# ========== PROCESAMIENTO DE LENGUAJE COLOQUIAL ==========
def normalizar_comando(texto):
    texto = texto.lower()
    expr = {
        "que onda": "hola", "que pedo": "hola", "buenas": "hola",
        "bye": "adios", "nos vemos": "adios",
        "chale": "triste", "que padre": "feliz", "que chido": "feliz",
        "que show": "estado", "que tal": "estado", "que cuentas": "estado",
        "que tiempo hace": "clima", "como esta el clima": "clima",
        "que hay de nuevo": "noticias", "que pasa en el mundo": "noticias",
        "recuerdame": "recordatorio", "mis recordatorios": "recordatorios"
    }
    for k, v in expr.items():
        if k in texto:
            texto = texto.replace(k, v)
    return texto

def interpretar_estado_animico(texto):
    texto = texto.lower()
    if any(p in texto for p in ["enojo", "coraje", "frustrado"]):
        return "😤 Parece que estás molesto. ¿Quieres hablar de eso?"
    if any(p in texto for p in ["feliz", "alegre", "contento", "padre", "chido"]):
        return "😊 ¡Qué bueno verte feliz! ¿En qué puedo ayudarte?"
    if any(p in texto for p in ["triste", "deprimido", "mal", "chale"]):
        return "😔 Lo siento. Estoy aquí para ti."
    if any(p in texto for p in ["flojera", "hueva", "cansado"]):
        return "😴 Entiendo la flojera. Tómate un descanso."
    return None

# ========== APLICACIÓN PRINCIPAL ==========
class JarvisApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        self.titulo = Label(text="JARVIS", size_hint_y=None, height=50, font_size='30sp', bold=True)
        self.subtitulo = Label(text="ASISTENTE TOTAL", size_hint_y=None, height=25, font_size='15sp')
        self.estado = Label(text="🟢 ONLINE", size_hint_y=None, height=25)
        self.entrada = TextInput(hint_text="✏️ Escribe un comando...", size_hint_y=None, height=50)
        self.boton = Button(text="ENVIAR", size_hint_y=None, height=45)
        self.boton.bind(on_press=self.activar)
        self.respuesta = Label(text="✨ Esperando comando...", size_hint_y=None, height=150, text_size=(None, None))
        self.respuesta.bind(size=self.respuesta.setter('text_size'))
        layout.add_widget(self.titulo)
        layout.add_widget(self.subtitulo)
        layout.add_widget(self.estado)
        layout.add_widget(self.entrada)
        layout.add_widget(self.boton)
        layout.add_widget(self.respuesta)
        return layout

    def activar(self, instance):
        comando = self.entrada.text.strip()
        if comando == "":
            self.respuesta.text = "✏️ Escribe un comando"
            return
        self.procesar_comando(comando)

    def procesar_comando(self, comando):
        c = normalizar_comando(comando)
        animico = interpretar_estado_animico(comando)
        if animico:
            self.respuesta.text = animico
            self.estado.text = "🟢 ONLINE"
            self.entrada.text = ""
            return

        # Comandos inmediatos (sin internet)
        if "hola" in c:
            self.respuesta.text = random.choice(FRASES["bienvenida"])
            guardar_memoria(c, self.respuesta.text)
        elif "hora" in c:
            self.respuesta.text = f"⏰ Son las {datetime.datetime.now().strftime('%I:%M %p')}"
        elif "fecha" in c:
            self.respuesta.text = f"📅 Hoy es {datetime.datetime.now().strftime('%d/%m/%Y')}"
        elif "gracias" in c:
            self.respuesta.text = random.choice(FRASES["gracias"])
        elif "adios" in c:
            self.respuesta.text = random.choice(FRASES["despedida"])
            self.entrada.text = ""
            return
        elif "dado" in c:
            self.respuesta.text = f"🎲 Dado: {random.randint(1, 6)}"
        elif "moneda" in c:
            self.respuesta.text = f"🪙 Moneda: {'Cara' if random.choice([True, False]) else 'Cruz'}"
        elif "chiste" in c:
            self.respuesta.text = chiste()
        elif "motivacion" in c:
            self.respuesta.text = random.choice(FRASES["motivacion"])
        elif "adivinanza" in c:
            a = adivinanza()
            self.respuesta.text = f"❓ {a['p']}"
        elif "ppt" in c or "piedra papel tijera" in c:
            if "piedra" in c:
                self.respuesta.text = piedra_papel_tijera("piedra")
            elif "papel" in c:
                self.respuesta.text = piedra_papel_tijera("papel")
            elif "tijera" in c:
                self.respuesta.text = piedra_papel_tijera("tijera")
            else:
                self.respuesta.text = "✂️ Elige: piedra, papel o tijera"
        elif "recuerdo" in c:
            rec = recordar_conversacion()
            self.respuesta.text = rec if rec else "📝 Aún no tengo recuerdos. Háblame más."
        elif "recordatorio" in c and "recordatorios" not in c:
            texto = c.replace("recordatorio", "").strip()
            if texto:
                guardar_recordatorio(texto)
                self.respuesta.text = f"✅ Recordatorio guardado: {texto}"
            else:
                self.respuesta.text = "📋 ¿Qué quieres recordar? Ej: 'recordatorio comprar pan'"
        elif "recordatorios" in c:
            self.respuesta.text = mostrar_recordatorios()
        elif any(p in c for p in ["funciones", "que puedes hacer", "ayuda"]):
            self.respuesta.text = """🎯 FUNCIONES:
- Clima: "clima en Madrid"
- Noticias: "noticias"
- Traducción: "traduce hola al ingles"
- Juegos: dado, moneda, chiste, motivación, adivinanza, piedra papel tijera
- Memoria: "recuerdo"
- Recordatorios: "recordatorio [texto]", "mis recordatorios"
- Apps: youtube, whatsapp, google, maps
- Hora, fecha
- Jerga: que onda, chale, que padre, etc."""
        # Comandos con internet (en hilos)
        elif "clima" in c:
            ciudad = c.replace("clima", "").replace("en", "").strip()
            if not ciudad:
                ciudad = "Madrid"
            self.respuesta.text = "🌤️ Consultando clima..."
            run_in_thread(obtener_clima, ciudad, callback=self.actualizar_respuesta)
        elif "noticias" in c:
            self.respuesta.text = "📰 Cargando noticias..."
            run_in_thread(obtener_noticias, callback=self.actualizar_respuesta)
        elif "traduce" in c:
            match = re.search(r'traduce (.+) al (\w+)', c)
            if match:
                texto = match.group(1)
                idioma = match.group(2)
                self.respuesta.text = "🌐 Traduciendo..."
                run_in_thread(traducir_texto, texto, idioma, callback=self.actualizar_respuesta)
            else:
                self.respuesta.text = "🌐 Usa: 'traduce [texto] al [idioma]'"
        # Apps externas
        elif "youtube" in c:
            webbrowser.open("https://youtube.com")
            self.respuesta.text = "🎬 Abriendo YouTube"
        elif "whatsapp" in c:
            webbrowser.open("https://web.whatsapp.com/")
            self.respuesta.text = "📱 Abriendo WhatsApp Web"
        elif "google" in c:
            webbrowser.open("https://google.com")
            self.respuesta.text = "🔍 Abriendo Google"
        elif "maps" in c:
            webbrowser.open("https://www.google.com/maps")
            self.respuesta.text = "🗺️ Abriendo Google Maps"
        else:
            self.respuesta.text = f"😅 No entendí '{comando}'. Escribe 'funciones'."

        self.entrada.text = ""
        self.estado.text = "🟢 ONLINE"

    def actualizar_respuesta(self, resultado):
        self.respuesta.text = resultado

if __name__ == "__main__":
    JarvisApp().run()

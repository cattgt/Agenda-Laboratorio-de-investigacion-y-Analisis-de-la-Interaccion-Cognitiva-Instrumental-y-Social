import streamlit as st
import datetime as dt
from clabcalendar import GoogleCalendarManager
from dateutil import parser 

# Mostrar logotipo al inicio
st.image("logo_11.png", width=120)

# Inicializa el manejador de calendario
calendar_manager = GoogleCalendarManager()

# Estilos y título
st.markdown(
    """
    <style>
        .title {
            font-size: 36px;
            color: #00BFFF;
            text-align: center;
        }
        .available {
            background-color: #98FB98;
            color: black;
            font-weight: bold;
            padding: 5px;
            margin: 2px;
            border-radius: 5px;
        }
        .occupied {
            background-color: #FF6347;
            color: white;
            font-weight: bold;
            padding: 5px;
            margin: 2px;
            border-radius: 5px;
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="title">AGENDA LABORATORIO DE INVESTIGACION Y ANALISIS DE LA INTERACCION COGNITIVA, INSTRUMENTAL Y SOCIAL</div>', unsafe_allow_html=True)

# --- 1. Ver horas disponibles ---
st.header("🕒 Ver horas disponibles")
fecha_seleccionada = st.date_input("Selecciona una fecha", dt.date.today())

# Bloques fijos definidos
bloques_fijos = {
    "08:30 - 09:30": dt.time(8, 30),
    "09:40 - 10:40": dt.time(9, 40),
    "10:50 - 11:50": dt.time(10, 50),
    "12:00 - 13:00": dt.time(12, 00),
    "14:10 - 15:10": dt.time(14, 10),
    "15:20 - 16:20": dt.time(15, 20),
    "16:30 - 17:30": dt.time(16, 30),
    "17:40 - 18:40": dt.time(17, 40)
}

def obtener_eventos_del_dia(fecha):
    # Convertir fecha en rango completo del día
    inicio_dia = dt.datetime.combine(fecha, dt.time.min).isoformat() + "Z"
    fin_dia = dt.datetime.combine(fecha, dt.time.max).isoformat() + "Z"

    eventos = calendar_manager.service.events().list(
        calendarId="primary",
        timeMin=inicio_dia,
        timeMax=fin_dia,
        singleEvents=True,
        orderBy="startTime"
    ).execute().get("items", [])

    ocupados = []
    for evento in eventos:
        inicio = evento["start"].get("dateTime")
        if inicio:
            start_dt = parser.isoparse(inicio).astimezone()
            ocupados.append(start_dt.time())
    return ocupados

def hora_ocupada(hora_bloque, lista_ocupados):
    for ocupado in lista_ocupados:
        if hora_bloque.hour == ocupado.hour and hora_bloque.minute == ocupado.minute:
            return True
    return False

ocupados = obtener_eventos_del_dia(fecha_seleccionada)
for bloque, hora in bloques_fijos.items():
    if hora_ocupada(hora, ocupados):
        estado = "⛔ Ocupado"
        clase = "occupied"
    else:
        estado = "✅ Disponible"
        clase = "available"
    st.markdown(f'<div class="{clase}">{bloque} - {estado}</div>', unsafe_allow_html=True)

# --- 3. Crear evento ---
st.header("📌 Reserva una hora")
nombre = st.text_input("Tu nombre completo")
correo = st.text_input("Ingrese Correo electrónico")
nombre_responsable = st.text_input("Ingrese nombre de profesor/a o persona responsable")
correo_responsable = st.text_input("Ingrese Correo electrónico de profesor/a o persona responsable")

mediciones = st.multiselect(
    "Selecciona qué mediciones deseas realizar:",
    [
        "Frecuencia cardiaca", "Conductancia de la piel", "Respiración",
        "Pletismografía / Cambios en volumen sanguíneo", "Seguimiento ocular",
        "Reconocimiento facial de emociones", "Grabación de interacción/conducta",
        "Uso de computadores", "Otro"
    ]
)

motivo = st.selectbox(
    "Motivo de uso del laboratorio",
    [
        "Capacitación",
        "Investigación",
        "Testeo de equipos"
    ]
)

fecha = st.date_input("Fecha de reserva", dt.date.today())
bloques_disponibles = {
    "08:30 - 09:30": (dt.time(8, 30), 60),
    "09:40 - 10:40": (dt.time(9, 40), 60),
    "10:50 - 11:50": (dt.time(10, 50), 60),
    "12:00 - 13:00": (dt.time(12, 00), 60),
    "14:10 - 15:10": (dt.time(14, 10), 60),
    "15:20 - 16:20": (dt.time(15, 20), 60),
    "16:30 - 17:30": (dt.time(16, 30), 60),
    "17:40 - 18:40": (dt.time(17, 40), 60)
}
bloques_seleccionados = st.multiselect("Selecciona uno o más bloques horarios", list(bloques_disponibles.keys()))

# --- Documentos éticos (opcional) ---
st.header("📄 Documentación requerida si hace investigación")
st.caption("Inserte protocolo/ documentos éticos aprobados por el CEC")
archivo = st.file_uploader("Sube tu protocolo (PDF, Word, etc.)", type=["pdf", "docx", "doc"])
archivo_nombre = archivo.name if archivo else "No se subió archivo"

# --- Subir archivo a Drive si se cargó ---
archivo_link_drive = None
if archivo:
    archivo_link_drive = calendar_manager.upload_file_to_drive(archivo, archivo.name)
    if archivo_link_drive:
        st.success(f"Archivo '{archivo.name}' cargado correctamente. Link en Drive: {archivo_link_drive}")
    else:
        st.error(f"❌ No se pudo subir el archivo '{archivo.name}' a Drive.")

# --- Validación antes de agendar ---
if not nombre or not correo:
    st.warning("Por favor, ingresa tu nombre y correo antes de agendar.")
else:
    if st.button("Agendar hora"):
        errores = []
        for bloque in bloques_seleccionados:
            hora, duracion = bloques_disponibles[bloque]
            if hora_ocupada(hora, ocupados):
                errores.append(f"❌ El bloque '{bloque}' ya está ocupado.")
                continue

            inicio = dt.datetime.combine(fecha, hora).isoformat()
            fin = (dt.datetime.combine(fecha, hora) + dt.timedelta(minutes=duracion)).isoformat()
            resumen = f"{nombre} - {motivo}"
            descripcion = (
                f"Correo: {correo}\n"
                f"Responsable: {nombre_responsable} ({correo_responsable})\n"
                f"Motivo: {motivo}"
            )

            link = calendar_manager.create_event(
                summary=resumen,
                description=descripcion,
                start_time=inicio,
                end_time=fin
            )

            if link and link.startswith("http"):
                calendar_manager.append_to_sheet([
                    dt.datetime.now().isoformat(),
                    nombre,
                    correo,
                    nombre_responsable,
                    correo_responsable,
                    ", ".join(mediciones), 
                    motivo,
                    fecha.strftime("%Y-%m-%d"),
                    hora.strftime("%H:%M"),
                    f"{duracion} minutos",
                    archivo_link_drive if archivo_link_drive else "No se subió archivo",
                    link
                ])
            else:
                errores.append(f"❌ Error al agendar el bloque '{bloque}'.")

        if errores:
            for err in errores:
                st.error(err)
        else:
            st.success("✅ ¡Todos los bloques fueron reservados correctamente!")
            st.balloons()
        

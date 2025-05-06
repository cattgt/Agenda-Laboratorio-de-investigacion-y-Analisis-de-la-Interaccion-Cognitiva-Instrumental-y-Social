import streamlit as st
import datetime as dt
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuración de credenciales desde secrets
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/calendar"]
)

# Inicialización de la API de Google Calendar
calendar_id = st.secrets["calendar_id"]
calendar = build("calendar", "v3", credentials=credentials)

# Título de la app
st.title("🗕 C-LAB Agenda")

# --- 1. Subir archivo: Protocolo del CEC ---
st.header("📄 Ingresar Protocolo del CEC")
archivo = st.file_uploader("Sube tu protocolo (PDF, Word, etc.)", type=["pdf", "docx", "doc"])

if archivo is not None:
    st.success(f"Archivo '{archivo.name}' cargado correctamente.")
    # Aquí podrías subirlo a Google Drive si deseas

# --- 2. Ver horas disponibles tipo agenda médica ---
st.header("🕒 Ver horas disponibles")
fecha_seleccionada = st.date_input("Selecciona una fecha", dt.date.today())

# Crear bloques de 30 minutos entre 9:00 y 18:00
bloques_horarios = [dt.time(h, m) for h in range(9, 18) for m in (0, 30)]

# Función para obtener eventos del día seleccionado
def obtener_eventos_del_dia(fecha):
    inicio = dt.datetime.combine(fecha, dt.time(0, 0)).isoformat() + 'Z'
    fin = dt.datetime.combine(fecha, dt.time(23, 59)).isoformat() + 'Z'
    eventos_resultado = calendar.events().list(
        calendarId=calendar_id,
        timeMin=inicio,
        timeMax=fin,
        singleEvents=True,
        orderBy="startTime"
    ).execute()
    eventos = eventos_resultado.get("items", [])
    ocupados = []
    for evento in eventos:
        start = evento["start"].get("dateTime")
        if start:
            start_dt = dt.datetime.fromisoformat(start)
            ocupados.append(start_dt.time())
    return ocupados

ocupados = obtener_eventos_del_dia(fecha_seleccionada)

# Mostrar disponibilidad
for hora in bloques_horarios:
    estado = "⛔ Ocupado" if hora in ocupados else "✅ Disponible"
    st.write(f"{hora.strftime('%H:%M')} - {estado}")

# --- 3. Crear evento (reserva) ---
st.header("📌 Reserva una hora")
nombre = st.text_input("Tu nombre completo")
motivo = st.text_input("Motivo de uso del laboratorio")
fecha = st.date_input("Fecha de reserva", dt.date.today())
hora = st.time_input("Hora de inicio", dt.time(9, 0))
duracion = st.slider("Duración (en minutos)", 30, 180, 60, step=30)

if st.button("Agendar hora"):
    inicio = dt.datetime.combine(fecha, hora)
    fin = inicio + dt.timedelta(minutes=duracion)

    evento = {
        "summary": f"{nombre} - {motivo}",
        "start": {"dateTime": inicio.isoformat(), "timeZone": "America/Santiago"},
        "end": {"dateTime": fin.isoformat(), "timeZone": "America/Santiago"}
    }

    creado = calendar.events().insert(calendarId=calendar_id, body=evento).execute()
    st.success("✅ Reserva realizada correctamente!")
    st.balloons()

import os
import datetime as dt
import pytz
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Función para guardar en Google Sheets ---
def guardar_en_google_sheets(datos_reserva):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)

    hoja = client.open("Reservas C-LAB").sheet1

    fila = [
        datos_reserva["Nombre"],
        datos_reserva["Correo"],
        datos_reserva["Fecha"],
        datos_reserva["Hora de inicio"],
        datos_reserva["Hora de término"],
        datos_reserva["Implementos"],
        datos_reserva["Motivo"]
    ]

    hoja.append_row(fila)

# --- Clase para gestionar Google Calendar ---
SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendarManager:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        if os.path.exists("service_account.json"):
            creds = service_account.Credentials.from_service_account_file(
                "service_account.json", scopes=SCOPES
            )
        else:
            raise FileNotFoundError("El archivo service_account.json no se encontró")

        return build("calendar", "v3", credentials=creds)

    def create_event(self, summary, start_time, end_time, timezone='America/Santiago'):
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': timezone},
            'end': {'dateTime': end_time, 'timeZone': timezone}
        }

        try:
            event = self.service.events().insert(
                calendarId="c-lab-agenda@c-lab-app.iam.gserviceaccount.com", body=event).execute()
            return event.get('htmlLink')
        except HttpError as error:
            return f"Ocurrió un error al crear el evento: {error}"

# --- Interfaz de Streamlit ---
st.image("logo_11.png", width=180)
st.title("Reserva de Horas C-LAB")
st.markdown("Gracias por ingresar a la agenda de uso del laboratorio C-LAB. Por favor completa los datos para reservar.")

calendar = GoogleCalendarManager()

with st.form(key='appointment_form'):
    nombre = st.text_input("Ingresa tu nombre")
    correo = st.text_input("Ingresa tu correo electrónico")  # Opcional pero útil
    motivo = st.text_input("Motivo de reserva")
    equipos = st.multiselect(
        "Selecciona los equipos que vas a utilizar:",
        [
            "MediaRecorder", "FaceReader", "The Observer XT", 
            "Tobii Glasses 3", "Tobii Glasses 2", "Tobii Spectrum", 
            "Biopac Acqknowledge", "Computadores", "Otro/no lo sé", "Ninguno"
        ]
    )
    fecha = st.date_input("Selecciona el día de tu reserva", dt.date.today())
    hora_inicio = st.time_input("Hora de inicio", dt.time(9, 0))
    hora_fin = st.time_input("Hora de fin", dt.time(10, 0))
    
    submitted = st.form_submit_button("Agendar hora")

if submitted:
    if not nombre or not motivo or not correo:
        st.error("Por favor, completa todos los campos obligatorios.")
    else:
        tz = pytz.timezone('America/Santiago')
        start_datetime = tz.localize(dt.datetime.combine(fecha, hora_inicio))
        end_datetime = tz.localize(dt.datetime.combine(fecha, hora_fin))

        if start_datetime < dt.datetime.now(tz):
            st.warning("No puedes agendar en una hora pasada.")
        else:
            resumen = f"{nombre} - {motivo} | Equipos: {', '.join(equipos)}"
            event_link = calendar.create_event(
                summary=resumen,
                start_time=start_datetime.isoformat(),
                end_time=end_datetime.isoformat()
            )
            if isinstance(event_link, str) and event_link.startswith("http"):
                st.success("✅ Reserva creada exitosamente. Recuerda asistir y ¡ten un buen día!")
                st.markdown(f"[Ver evento en Google Calendar]({event_link})")

                datos_reserva = {
                    "Nombre": nombre,
                    "Correo": correo,
                    "Fecha": str(fecha),
                    "Hora de inicio": hora_inicio.strftime("%H:%M"),
                    "Hora de término": hora_fin.strftime("%H:%M"),
                    "Implementos": ", ".join(equipos),
                    "Motivo": motivo
                }
                guardar_en_google_sheets(datos_reserva)
            else:
                st.error(f"❌ Error al crear la reserva: {event_link}")

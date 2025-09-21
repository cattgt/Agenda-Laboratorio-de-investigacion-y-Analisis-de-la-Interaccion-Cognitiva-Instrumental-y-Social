# clabcalendar.py
import datetime as dt
import pytz
import streamlit as st
import io
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ Permisos necesarios para Google Calendar , Google Sheets y Google Drive
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

#  ID del calendario compartido del laboratorio
CALENDAR_ID = '088ad85ef8fdcb937ac7b19749449e0b20f331220495d55f5952394af31f1f30@group.calendar.google.com'
TIMEZONE = 'America/Santiago'

#  ID de la hoja de cálculo y nombre de la hoja
SPREADSHEET_ID = '15l1xB9SyZPFPsQPA9b_xLBAaZLvvcNWXc0K12QEtlo8'
SHEET_NAME = 'C-LAB RESERVA'

# ID de la carpeta de archivos 
DRIVE_FOLDER_ID = '1j0bgnibm9RW4-bsceulsZxw_sCXNiGTA'
DRIVE_NAME = 'C-LAB RESERVA'


class GoogleCalendarManager:
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        self.calendar_service = build("calendar", "v3", credentials=self.creds)
        self.sheets_service = build("sheets", "v4", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds) 

    def list_upcoming_events(self, max_results=10):
        chile_tz = pytz.timezone(TIMEZONE)
        now = dt.datetime.now(chile_tz).isoformat()
        end = (dt.datetime.now(chile_tz) + dt.timedelta(days=6)).replace(
            hour=23, minute=59, second=0, microsecond=0
        ).isoformat()
        try:
            events_result = self.calendar_service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=now,
                timeMax=end,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except HttpError as error:
            st.error(f"❌ Error al listar eventos: {error}")
            return []

    def create_event(self, summary, start_time, end_time, attendees=None, description=""):
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': TIMEZONE},
            'end': {'dateTime': end_time, 'timeZone': TIMEZONE}
        }
        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]
        try:
            created_event = self.calendar_service.events().insert(
                calendarId=CALENDAR_ID,
                body=event
            ).execute()
            return created_event.get('htmlLink')
        except HttpError as error:
            st.error(f"❌ Error al crear el evento: {error}")
            return None

    def append_to_sheet(self, row_data):
        """
        row_data: lista con los siguientes campos:
        [fecha_inscripcion, nombre, correo, nombre_responsable, correo_responsable, mediciones,
         motivo, fecha_reserva, hora, duracion, archivo_nombre, link]
        """
        try:
            body = {"values": [row_data]}
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            return result
        except HttpError as error:
            st.error(f"❌ Error al registrar en Google Sheets: {error}")
            return None
            
            # --- NUEVO: subir archivo a Drive ---
    def upload_file_to_drive(self, file, filename, folder_id=DRIVE_FOLDER_ID):
        """
        file: archivo subido por Streamlit (st.file_uploader)
        filename: nombre del archivo
        folder_id: ID de la carpeta donde guardar
        """
        try:
            file_metadata = {
                'name': filename,
                'parents': [folder_id]
            }
            media = MediaIoBaseUpload(io.BytesIO(file.getvalue()), mimetype=file.type)
            uploaded_file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            return uploaded_file.get('webViewLink')  # link para abrir el archivo
        except Exception as e:
            st.error(f"❌ Error al subir archivo a Drive: {e}")
            return None
        


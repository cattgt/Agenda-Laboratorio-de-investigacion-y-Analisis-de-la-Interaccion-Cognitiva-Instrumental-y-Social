# clabcalendar.py

import datetime as dt
import pytz
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ Permisos necesarios para Google Calendar y Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ✅ ID del calendario compartido del laboratorio
CALENDAR_ID = '1e2385c410653a58928207f870002e8a4a03683d51de7b0c3ae768fd98e88e73@group.calendar.google.com'
TIMEZONE = 'America/Santiago'

# ✅ ID de la hoja de cálculo y nombre de la hoja
SPREADSHEET_ID = '1uZ2-EKjvWFKTo8V7VtQEN26Vgce6kccXy3yzX2le06w'
SHEET_NAME = 'C-LAB RESERVA'

class GoogleCalendarManager:
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        self.calendar_service = build("calendar", "v3", credentials=self.creds)
        self.sheets_service = build("sheets", "v4", credentials=self.creds)

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
        [fecha_inscripcion, nombre, correo, nombre_responsable, correo_responsable,
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


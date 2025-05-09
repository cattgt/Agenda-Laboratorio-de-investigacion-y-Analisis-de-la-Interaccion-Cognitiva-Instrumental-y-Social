# clabcalendar.py

import datetime as dt
import pytz
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CALENDAR_ID = '1e2385c410653a58928207f870002e8a4a03683d51de7b0c3ae768fd98e88e73@group.calendar.google.com'
TIMEZONE = 'America/Santiago'
SPREADSHEET_ID = '1uZ2-EKjvWFKTo8V7VtQEN26Vgce6kccXy3yzX2le06w'
SHEET_NAME = 'Reservas'

class GoogleCalendarManager:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        return build("calendar", "v3", credentials=creds)

    def list_upcoming_events(self, max_results=10):
        chile_tz = pytz.timezone(TIMEZONE)
        now = dt.datetime.now(chile_tz).isoformat()
        end = (dt.datetime.now(chile_tz) + dt.timedelta(days=5)).replace(
            hour=23, minute=59, second=0, microsecond=0
        ).isoformat()

        try:
            events_result = self.service.events().list(
                calendarId=CALENDAR_ID,
                timeMin=now,
                timeMax=end,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])
        except HttpError as error:
            print(f"❌ Error al listar eventos: {error}")
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
            created_event = self.service.events().insert(
                calendarId=CALENDAR_ID,
                body=event
            ).execute()
            return created_event.get('htmlLink')
        except HttpError as error:
            return f"❌ Error al crear el evento: {error}"

    def update_event(self, event_id, summary=None, start_time=None, end_time=None):
        try:
            event = self.service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
            if summary:
                event['summary'] = summary
            if start_time:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time:
                event['end']['dateTime'] = end_time.isoformat()

            updated_event = self.service.events().update(
                calendarId=CALENDAR_ID, eventId=event_id, body=event).execute()
            return updated_event
        except HttpError as error:
            print(f"❌ Error al actualizar el evento: {error}")

    def delete_event(self, event_id):
        try:
            self.service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
            return True
        except HttpError as error:
            print(f"❌ Error al eliminar el evento: {error}")
            return False

    def append_to_sheet(self, values):
        try:
            sheets_service = build("sheets", "v4", credentials=self.service._http.credentials)
            body = {"values": [values]}
            result = sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{SHEET_NAME}!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            return result
        except HttpError as error:
            print(f"❌ Error al escribir en Google Sheets: {error}")
            return None

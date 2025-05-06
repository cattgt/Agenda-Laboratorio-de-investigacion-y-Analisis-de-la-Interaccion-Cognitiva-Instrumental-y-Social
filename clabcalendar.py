import os.path
import datetime as dt
import pytz
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class GoogleCalendarManager:
    def __init__(self):
        self.service = self._authenticate()

    def _authenticate(self):
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        return build("calendar", "v3", credentials=creds)

    def list_upcoming_events(self, max_results=10):
        chile_tz = pytz.timezone('America/Santiago')
        now = dt.datetime.now(chile_tz).isoformat()
        end = (dt.datetime.now(chile_tz) + dt.timedelta(days=5)).replace(
            hour=23, minute=59, second=0, microsecond=0
        ).isoformat()

        try:
            events_result = self.service.events().list(
                calendarId='c-lab-agenda@c-lab-app.iam.gserviceaccount.com',
                timeMin=now,
                timeMax=end,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            if not events:
                print('No hay eventos próximos.')
            else:
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    print(start, event.get('summary', 'Sin título'), event.get('id', 'Sin ID'))

            return events

        except HttpError as error:
            print(f"Ocurrió un error al listar eventos: {error}")
            return []

    def create_event(self, summary, start_time, end_time, timezone, attendees=None):
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': timezone},
            'end': {'dateTime': end_time, 'timeZone': timezone}
        }

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        try:
            event = self.service.events().insert(calendarId="c-lab-agenda@c-lab-app.iam.gserviceaccount.com", body=event).execute()
            print(f"Evento creado: {event.get('htmlLink')}")
        except HttpError as error:
            print(f"Ocurrió un error al crear el evento: {error}")

    def update_event(self, event_id, summary=None, start_time=None, end_time=None):
        try:
            event = self.service.events().get(calendarId='c-lab-agenda@c-lab-app.iam.gserviceaccount.com', eventId=event_id).execute()

            if summary:
                event['summary'] = summary
            if start_time:
                event['start']['dateTime'] = start_time.strftime('%Y-%m-%dT%H:%M:%S')
            if end_time:
                event['end']['dateTime'] = end_time.strftime('%Y-%m-%dT%H:%M:%S')

            updated_event = self.service.events().update(
                calendarId='c-lab-agenda@c-lab-app.iam.gserviceaccount.com', eventId=event_id, body=event).execute()
            print("Evento actualizado.")
            return updated_event

        except HttpError as error:
            print(f"Ocurrió un error al actualizar el evento: {error}")

    def delete_event(self, event_id):
        try:
            self.service.events().delete(calendarId='c-lab-agenda@c-lab-app.iam.gserviceaccount.com', eventId=event_id).execute()
            print("Evento eliminado.")
            return True
        except HttpError as error:
            print(f"Ocurrió un error al eliminar el evento: {error}")
            return False

if __name__ == "__main__":
    calendar = GoogleCalendarManager()
    calendar.list_upcoming_events()

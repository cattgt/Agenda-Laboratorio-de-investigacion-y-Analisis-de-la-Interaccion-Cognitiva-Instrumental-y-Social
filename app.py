import streamlit as st
import datetime as dt
from clabcalendar import GoogleCalendarManager, CALENDAR_ID
from dateutil import parser
import pytz  # NECESARIO PARA ZONA HORARIA

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
            color: #4BA6FF;
            text-align: center;
            font-weight: bold;
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

st.markdown(
    '<div class="title">AGENDA LABORATORIO DE INVESTIGACION Y ANALISIS DE LA INTERACCION COGNITIVA, INSTRUMENTAL Y SOCIAL </div>',
    unsafe_allow_html=True
)

# --- 1. Ver horas disponibles ---

bloques_fijos = {
    "08:00 - 08:59": dt.time(8, 0),
    "09:00 - 09:59": dt.time(9, 0),
    "10:00 - 10:59": dt.time(10, 0),
    "11:00 - 11:59": dt.time(11, 0),
    "12:00 - 12:59": dt.time(12, 0),
    "13:00 - 13:59": dt.time(13, 0),
    "14:00 - 14:59": dt.time(14, 0),
    "15:00 - 15:59": dt.time(15, 0),
    "16:00 - 16:59": dt.time(16, 0),
    "17:00 - 17:59": dt.time(17, 0),
    "18:00 - 18:59": dt.time(18, 0),
    "19:00 - 19:59": dt.time(19, 0)
}
# --- FUNCIÓN PARA VER EVENTOS DEL DÍA ---
def obtener_eventos_del_dia(fecha):
    chile_tz = pytz.timezone("America/Santiago")

    inicio_dia = chile_tz.localize(dt.datetime.combine(fecha, dt.time.min)).isoformat()
    fin_dia = chile_tz.localize(dt.datetime.combine(fecha, dt.time.max)).isoformat()

    eventos = calendar_manager.calendar_service.events().list(
        calendarId=CALENDAR_ID,   # ✔ USAR LA CONSTANTE REAL
        timeMin=inicio_dia,
        timeMax=fin_dia,
        singleEvents=True,
        orderBy="startTime"
    ).execute().get("items", [])

    ocupados = []
    for evento in eventos:
        inicio = evento["start"].get("dateTime")
        if inicio:
            start_dt = parser.isoparse(inicio).astimezone(chile_tz)
            if start_dt.date() == fecha:
                descripcion = evento.get("description", "")
                sector = None
                if "Sector: Sala de control/ Sector 3" in descripcion:
                    sector = "Sala de control/ Sector 3"

                elif "Sector: Sala de observación/ Sector 4" in descripcion:
                    sector = "Sala de observación/ Sector 4" 

                elif "Sector: Ambos sectores" in descripcion:
                    sector = "Ambos sectores"
                if sector:
                    ocupados.append({
                        "hora": start_dt.time(),
                        "sector": sector
                    })
    return ocupados

# --- Salas ocupadas ---

def hora_ocupada(hora_bloque, sector, lista_ocupados):
    for ocupado in lista_ocupados:

        if ocupado["hora"].hour == hora_bloque.hour:
            if ocupado["hora"].minute == hora_bloque.minute:

                if ocupado["sector"] == sector:
                    return True

                if ocupado["sector"] == "Ambos sectores":
                    return True

    return False

# --- 3. Crear evento ---
st.header("🗓️ Reserva una sala del laboratorio")
nombre = st.text_input("Tu nombre completo")
correo = st.text_input("Ingrese Correo electrónico")
nombre_responsable = st.text_input("Ingrese nombre de profesor/a o persona responsable")
correo_responsable = st.text_input("Ingrese Correo electrónico de profesor/a o persona responsable")
#Apartado de documentos éticos
st.markdown(
    '<span style="color:#98FB98; font-size:14px;">'
    'Documentos éticos<br>'
    'El uso de consentimientos informados debe estar aprobado por el CEC o comité ético de la facultad
    y ser enviados a este correo: cicc.utalca@gmail.com'
    '</span>',
    unsafe_allow_html=True
)
# ---4. Reservar según sala diferenciada ---

Sector = st.selectbox(
    "¿Que sectores del laboratorio deseas recervar?",
    [
        "Sala de control/ Sector 3",
        "Sala de observación/ Sector 4",
        "Ambos sectores"
    ]
)

mediciones = st.multiselect(
    "Selecciona qué mediciones deseas realizar:",
    [
        "Frecuencia cardiaca", "Conductancia de la piel", "Respiración",
        "Pletismografía / Cambios en volumen sanguíneo", "Seguimiento ocular de pantalla", 
        "Seguimiento ocular dispositivo portatil",
        "Reconocimiento facial de emociones", "Grabación de interacción/conducta",
        "Uso de computadores"
    ]
)

motivo = st.selectbox(
    "Motivo de uso del laboratorio",
    [
        "Capacitación",
        "Investigación",
        "Pilotaje de experimentos",
        "Soporte Técnico"
    ]
)

fecha = st.date_input("Fecha de reserva", dt.date.today())

# Obtener las reservas de Google Calendar
ocupados = obtener_eventos_del_dia(fecha)


# Guardar los horarios que el usuario va seleccionando
if "bloques_seleccionados" not in st.session_state:
    st.session_state.bloques_seleccionados = []


st.subheader("🕐 Selecciona tus horarios")

columnas = st.columns(2)

for indice, (bloque, hora) in enumerate(bloques_fijos.items()):

    # DETERMINAR SI EL BLOQUE ESTÁ OCUPADO---------------------

    if Sector == "Ambos sectores":

        ocupado = (
            hora_ocupada(
                hora,
                "Sala de control/ Sector 3",
                ocupados
            )
            or
            hora_ocupada(
                hora,
                "Sala de observación/ Sector 4",
                ocupados
            )
        )

    else:


        ocupado = hora_ocupada(
            hora,
            Sector,
            ocupados
        )


    columna = columnas[indice % 2]
    
    # SI ESTÁ OCUPADO---------------------

    if ocupado:

        columna.button(
            f"🔴 {bloque}\nOcupado",
            disabled=True,
            key=f"ocupado_{bloque}"
        )

    # SI ESTÁ DISPONIBLE---------------------

    else:

        seleccionado = (
            bloque in st.session_state.bloques_seleccionados
        )

        if seleccionado:
            texto_boton = f"🔵 {bloque}\nSeleccionado"
        else:
            texto_boton = f"🟢 {bloque}\nDisponible"

        if columna.button(
            texto_boton,
            key=f"boton_{bloque}"
        ):

            if seleccionado:

                st.session_state.bloques_seleccionados.remove(
                    bloque
                )

            else:

                st.session_state.bloques_seleccionados.append(
                    bloque
                )

# --- Validación ---
if not nombre or not correo:
    st.warning("Por favor, ingresa tu nombre y correo antes de agendar.")
else:
    if st.button("Agendar hora"):
        ocupados = obtener_eventos_del_dia(fecha)
        errores = []

        for bloque in st.session_state.bloques_seleccionados:

            hora = bloques_fijos[bloque]
            duracion = 60

            # Volver a comprobar disponibilidad antes de reservar
            if Sector == "Ambos sectores":

                sector_a_reservar = [
                    "Sala de control/ Sector 3",
                    "Sala de observación/ Sector 4"
                ]

            else:

                sector_a_reservar = [Sector]

            # Crear un evento por cada sector que se va a reservar
            for sector in sector_a_reservar:

                if hora_ocupada(hora, sector, ocupados):
                    errores.append(
                        f"❌ El bloque '{bloque}' ya está ocupado en {sector}."
                    )
                    continue

                inicio = dt.datetime.combine(
                    fecha,
                    hora
                ).isoformat()

                fin = (
                    dt.datetime.combine(fecha, hora)
                    + dt.timedelta(minutes=duracion)
                ).isoformat()

                resumen = f"{nombre} - {motivo}"

                descripcion = (
                    f"Correo: {correo}\n"
                    f"Responsable: {nombre_responsable} "
                    f"({correo_responsable})\n"
                    f"Motivo: {motivo}\n"
                    f"Sector: {sector}"
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
                        sector,
                        fecha.strftime("%Y-%m-%d"),
                        hora.strftime("%H:%M"),
                        f"{duracion} minutos",
                        link
                    ])

                else:
                    errores.append(
                        f"❌ Error al agendar el bloque "
                        f"'{bloque}' en {sector}."
                    )

        if errores:
            for err in errores:
                st.error(err)
        else:
            st.success(
                "✅ ¡Todos los bloques fueron reservados correctamente!"
            )
            st.balloons()

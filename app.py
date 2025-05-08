import streamlit as st
import datetime as dt
from clabcalendar import GoogleCalendarManager

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

# --- 1. Subir archivo: Protocolo del CEC ---
st.header("📄 Ingresar Protocolo del CEC")
archivo = st.file_uploader("Sube tu protocolo (PDF, Word, etc.)", type=["pdf", "docx", "doc"])
if archivo:
    st.success(f"Archivo '{archivo.name}' cargado correctamente.")

# --- 2. Ver horas disponibles ---
st.header("🕒 Ver horas disponibles")
fecha_seleccionada = st.date_input("Selecciona una fecha", dt.date.today())
bloques_horarios = [dt.time(h, m) for h in range(9, 18) for m in (0, 30)]

# Obtener eventos existentes del día
def obtener_eventos_del_dia(fecha):
    eventos = calendar_manager.list_upcoming_events(50)
    ocupados = []
    for evento in eventos:
        inicio = evento["start"].get("dateTime")
        if inicio:
            start_dt = dt.datetime.fromisoformat(inicio)
            if start_dt.date() == fecha:
                ocupados.append(start_dt.time())
    return ocupados

ocupados = obtener_eventos_del_dia(fecha_seleccionada)

for hora in bloques_horarios:
    estado = "⛔ Ocupado" if hora in ocupados else "✅ Disponible"
    clase = "occupied" if hora in ocupados else "available"
    st.markdown(f'<div class="{clase}">{hora.strftime("%H:%M")} - {estado}</div>', unsafe_allow_html=True)

# --- 3. Crear evento ---
st.header("📌 Reserva una hora")
nombre = st.text_input("Tu nombre completo")
motivo = st.text_input("Motivo de uso del laboratorio")
fecha = st.date_input("Fecha de reserva", dt.date.today())
hora = st.time_input("Hora de inicio", dt.time(9, 0))
duracion = st.slider("Duración (en minutos)", 30, 180, 60, step=30)

# --- Verificación robusta de tipos ---
if isinstance(fecha, str):
    fecha = dt.datetime.strptime(fecha, "%Y-%m-%d").date()
if isinstance(hora, str):
    hora = dt.datetime.strptime(hora, "%H:%M:%S").time()

if st.button("Agendar hora"):
    inicio = dt.datetime.combine(fecha, hora).isoformat()
    fin = (dt.datetime.combine(fecha, hora) + dt.timedelta(minutes=duracion)).isoformat()
    resumen = f"{nombre} - {motivo}"

    link = calendar_manager.create_event(summary=resumen, start_time=inicio, end_time=fin)
    if link.startswith("http"):
        st.success("✅ Reserva realizada correctamente!")
        st.balloons()
    else:
        st.error(link)

import streamlit as st
import pandas as pd
from datetime import date, datetime

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Hybrid Training Hub",
    page_icon="🏋️",
    layout="wide"
)

# 2. BASE DE DATOS SIMULADA (Para que la app funcione mientras no subas archivos)
# En el futuro, esto se guardará en archivos locales del servidor
if 'entrenamientos' not in st.session_state:
    st.session_state['entrenamientos'] = {
        "Lunes": {"Fuerza": "Empuje (Pecho/Hombro/Tríceps)", "Resistencia": "🏃‍♂️ 45 min Carrera Z2"},
        "Martes": {"Fuerza": "Tracción (Espalda/Bíceps)", "Resistencia": "🚴‍♂️ 60 min Ciclismo Z2"},
        "Miércoles": {"Fuerza": "Pierna (Énfasis Cuádriceps)", "Resistencia": "Descanso Activo"},
        "Jueves": {"Fuerza": "Torso Recordatorio", "Resistencia": "🏃‍♂️ Series de velocidad 5x1000m"},
        "Viernes": {"Fuerza": "Pierna (Énfasis Cadena Posterior)", "Resistencia": "🏃‍♂️ 30 min Carrera Z1"},
        "Sábado": {"Fuerza": "Descanso", "Resistencia": "🏃‍♂️ Tirada Larga 90 min"},
        "Domingo": {"Fuerza": "Descanso Total", "Resistencia": "Descanso Total"}
    }

# Días de la semana en español para emparejar con la fecha actual
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dia_actual_texto = dias_semana[datetime.today().weekday()]

# 3. NAVEGACIÓN
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Ir a:",
    ["🏠 Inicio (Entreno del Día)", "📥 Ingresar Datos Semanales", "📈 Dashboard de Métricas"]
)

# --- PÁGINA 1: INICIO ---
if opcion_navegacion == "🏠 Inicio (Entreno del Día)":
    st.title("🏋️ Tu Plan para Hoy")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    # Extraemos el entreno del diccionario según el día de la semana
    entreno_hoy = st.session_state['entrenamientos'].get(dia_actual_texto, {"Fuerza": "Descanso", "Resistencia": "Descanso"})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💪 Sesión de Fuerza")
        st.info(entreno_hoy["Fuerza"])
        
    with col2:
        st.markdown("### 🏃‍♂️ Sesión de Resistencia")
        st.success(entreno_hoy["Resistencia"])

# --- PÁGINA 2: INGRESO DE DATOS ---
elif opcion_navegacion == "📥 Ingresar Datos Semanales":
    st.title("Registro de Datos Semanales")
    
    # SECCIÓN A: Actualizar el plan de la semana (Texto de Gemini)
    st.header("1. Actualizar Plan de Entrenamiento")
    st.write("Modifica el entrenamiento de cada día de la semana según lo pautado:")
    
    # Creamos pestañas para no saturar la pantalla
    pestanas = st.tabs(dias_semana)
    
    for i, dia in enumerate(dias_semana):
        with pestanas[i]:
            st.write(f"Editar entrenamiento para el **{dia}**")
            # Cajas de texto que se rellenan con el valor actual
            fuerza_edit = st.text_area(f"Fuerza - {dia}", value=st.session_state['entrenamientos'][dia]["Fuerza"], key=f"f_{dia}")
            resistencia_edit = st.text_area(f"Resistencia - {dia}", value=st.session_state['entrenamientos'][dia]["Resistencia"], key=f"r_{dia}")
            
            # Guardamos los cambios en el estado temporal de la app
            st.session_state['entrenamientos'][dia]["Fuerza"] = fuerza_edit
            st.session_state['entrenamientos'][dia]["Resistencia"] = resistencia_edit

    st.success("Plan semanal actualizado en la memoria de la aplicación.")
    
    st.write("---")
    
    # SECCIÓN B: Carga del CSV de Garmin
    st.header("2. Cargar Métricas de Garmin")
    archivo_garmin = st.file_uploader("Sube el CSV de actividades de Garmin Connect", type=["csv"])
    
    if archivo_garmin is not None:
        try:
            # Leemos el CSV
            df = pd.read_csv(archivo_garmin)
            
            st.success("¡Archivo leído correctamente!")
            
            # Mostramos un resumen de lo que contiene el CSV para comprobar las columnas
            st.write("### Vista previa de tus datos de Garmin:")
            st.dataframe(df.head(5))
            
            st.write("### Columnas detectadas en tu archivo:")
            st.write(list(df.columns))
            
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# --- PÁGINA 3: DASHBOARD ---
elif opcion_navegacion == "📈 Dashboard de Métricas":
    st.title("Métricas y Progresión")
    st.info("Próximo paso: Aquí crearemos las gráficas automáticas en cuanto confirmemos las columnas de tu CSV de Garmin.")

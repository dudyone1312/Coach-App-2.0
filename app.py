import streamlit as st
import pandas as pd
from datetime import date

# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
# Esto debe ser lo primero que se ejecuta en Streamlit. Define el título y el ancho.
st.set_page_config(
    page_title="Hybrid Training Hub",
    page_icon="🏋️",
    layout="wide"
)

# 2. SISTEMA DE NAVEGACIÓN
# Creamos un menú desplegable en la barra lateral
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Ir a:",
    ["🏠 Inicio (Entreno del Día)", "📥 Ingresar Datos Semanales", "📈 Dashboard de Métricas"]
)

# 3. LÓGICA DE LAS PÁGINAS

# --- PÁGINA 1: INICIO ---
if opcion_navegacion == "🏠 Inicio (Entreno del Día)":
    st.title("Entrenamiento del Día")
    st.subheader(f"Fecha: {date.today().strftime('%d/%m/%Y')}")
    
    # Aquí simularemos la lectura del entreno que te ha pautado Gemini
    # Más adelante, esto lo leeremos de un archivo donde guardes tus rutinas
    st.info("💡 Consejo del bloque: Estás en un microciclo de carga (Semana 3). Prioriza el RPE indicado sobre los ritmos absolutos.")
    
    # Dividimos la pantalla en dos columnas para separar Fuerza y Resistencia (Híbrido)
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🏋️ Fuerza")
        st.write("**Bloque principal:** 5/3/1 Back Squat")
        st.write("- Serie 1: 5 x 65%")
        st.write("- Serie 2: 5 x 75%")
        st.write("- Serie 3: 5+ x 85%")
        st.write("**Accesorios:**")
        st.checkbox("Zancadas Búlgaras 3x10")
        st.checkbox("Plancha abdominal 3x1 min")

    with col2:
        st.header("🏃‍♂️ Resistencia (Garmin)")
        st.write("**Tipo de sesión:** Series Z4 (Umbral)")
        st.write("**Estructura:**")
        st.write("- Calentamiento: 15 min Z1/Z2")
        st.write("- Principal: 4 x 5 min en Z4 (Recuperación 2 min trote suave)")
        st.write("- Enfriamiento: 10 min Z1")
        st.checkbox("Sesión completada y sincronizada en Garmin")

# --- PÁGINA 2: INGRESO DE DATOS ---
elif opcion_navegacion == "📥 Ingresar Datos Semanales":
    st.title("Registro de Datos Semanales")
    st.write("Sube tus archivos CSV de Garmin o introduce tus RMs y métricas de fuerza.")
    
    # Zona de subida de archivos
    archivo_garmin = st.file_uploader("Sube tu CSV de Garmin Connect", type=["csv"])
    
    if archivo_garmin is not None:
        # Si se sube un archivo, pandas lo lee y Streamlit lo muestra
        df_garmin = pd.read_csv(archivo_garmin)
        st.success("Archivo subido con éxito.")
        st.dataframe(df_garmin.head()) # Muestra solo las primeras filas

# --- PÁGINA 3: DASHBOARD ---
elif opcion_navegacion == "📈 Dashboard de Métricas":
    st.title("Métricas y Progresión")
    st.write("Aquí irán las gráficas de volumen, carga aguda/crónica y distribución de zonas.")
    st.warning("Módulo en construcción. Se implementará en el siguiente paso de programación.")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from PIL import Image
import os

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Hybrid Training Hub",
    page_icon="🏋️",
    layout="wide"
)

# Nombres de los archivos locales donde se guardará tu histórico de forma persistente
FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"
FILE_PLAN = "datos_plan.csv"

# 2. FUNCIÓN PARA CARGAR DATOS HISTÓRICOS AL INICIAR
def cargar_historico(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# Inicializamos el estado de la aplicación con lo que haya guardado en el servidor
if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_historico(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_historico(FILE_SUENO)
if 'plan_entrenamiento' not in st.session_state:
    st.session_state['plan_entrenamiento'] = cargar_historico(FILE_PLAN)
if 'imagenes_capturas' not in st.session_state:
    st.session_state['imagenes_capturas'] = []

# Configuración del calendario
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dia_actual_texto = dias_semana[datetime.today().weekday()]

# 3. NAVEGACIÓN LATERAL
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Ir a:",
    ["🏠 Inicio (Entreno del Día)", "📥 Ingresar Datos", "📈 Métricas y Evolución", "📜 Históricos"]
)

# --- PÁGINA: INGRESSAR DATOS ---
if opcion_navegacion == "📥 Ingresar Datos":
    st.title("📥 Ingresar Datos")
    st.write("Sube tus archivos para alimentar la base de datos histórica de tu entrenamiento.")
    
    # Cuadro de importación en el inicio absoluto de la pestaña
    archivos_subidos = st.file_uploader(
        "Arrastra o selecciona tus archivos aquí (CSV de Garmin, Planes, Capturas de pantalla)", 
        type=["csv", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    if archivos_subidos:
        for archivo in archivos_subidos:
            nombre = archivo.name.lower()
            
            # A. Procesamiento de IMÁGENES
            if nombre.endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(archivo)
                if archivo.name not in [x['name'] for x in st.session_state['imagenes_capturas']]:
                    st.session_state['imagenes_capturas'].append({"name": archivo.name, "image": img})
                    st.success(f"📷 Imagen temporal guardada: {archivo.name}")
            
            # B. Procesamiento de CSVs con acumulación histórica
            elif nombre.endswith('.csv'):
                try:
                    df_nuevo = pd.read_csv(archivo)
                    columnas_str = "".join(df_nuevo.columns).lower()
                    
                    # Identificar si es Sueño/Salud
                    if "sueño" in nombre or "sleep" in nombre or "vfc" in columnas_str or "hrv" in columnas_str:
                        if not st.session_state['df_sueno'].empty:
                            # Combinar nuevo con viejo y eliminar duplicados exactos
                            df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates().reset_index(drop=True)
                        else:
                            df_total = df_nuevo
                        st.session_state['df_sueno'] = df_total
                        df_total.to_csv(FILE_SUENO, index=False) # Guardado persistente en el servidor
                        st.success(f"💤 Datos de sueño acumulados y guardados de forma persistente.")
                    
                    # Identificar si es Actividades
                    elif "actividad" in nombre or "activity" in nombre or "distancia" in columnas_str or "ritmo" in columnas_str:
                        if not st.session_state['df_actividades'].empty:
                            df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True)
                        else:
                            df_total = df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False) # Guardado persistente en el servidor
                        st.success(f"🏃‍♂️ Historial de actividades acumulado y guardado de forma persistente.")
                    
                    # Identificar si es el Plan de Entrenamiento enviado por Gemini
                    else:
                        st.session_state['plan_entrenamiento'] = df_nuevo
                        df_nuevo.to_csv(FILE_PLAN, index=False) # Sobrescribe el plan actual
                        st.success(f"📋 Nueva planificación de entrenamientos fijada con éxito.")
                        
                except Exception as e:
                    st.error(f"Error al procesar el archivo CSV {archivo.name}: {e}")

    # Visualizador discreto de imágenes al final
    if st.session_state['imagenes_capturas']:
        with st.expander("Ver imágenes adjuntas en esta sesión"):
            for item in st.session_state['imagenes_capturas']:
                st.write(f"Archivo: {item['name']}")
                st.image(item['image'], use_column_width=True)


# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio (Entreno del Día)":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    col_izquierda, col_derecha = st.columns([3, 2])
    
    # COLUMNA IZQUIERDA: Sesión del día extraída del CSV del plan
    with col_izquierda:
        st.markdown("### 📋 Sesión Planificada")
        df_plan = st.session_state['plan_entrenamiento']
        
        if not df_plan.empty:
            # Estandarizamos columnas a minúsculas
            df_plan.columns = [c.lower() for c in df_plan.columns]
            # Buscamos si alguna celda contiene el nombre del día de hoy
            filtro_dia = df_plan[df_plan.astype(str).sum(axis=1).str.lower().str.contains(dia_actual_texto.lower())]
            
            if not filtro_dia.empty:
                st.dataframe(filtro_dia, use_container_width=True)
            else:
                st.info(f"No se detectaron entrenamientos pautados para el día **{dia_actual_texto}** en tu archivo de planificación.")
        else:
            st.warning("⚠️ No hay ninguna rutina activa en el sistema. Sube el CSV con tu programación en la pestaña 'Ingresar Datos'.")

    # COLUMNA DERECHA: Semáforo de predisposición (Cero absoluto inicial)
    with col_derecha:
        st.markdown("### 🚦 Predisposición para Entrenar")
        df_sueno = st.session_state['df_sueno']
        
        if not df_sueno.empty:
            st.info("🔄 Procesando últimas métricas de salud detectadas...")
            # Aquí se inyectará el algoritmo exacto del semáforo en cuanto conozca tus columnas de sueño
        else:
            st.warning("⚠️ Semáforo inactivo. Sube tus métricas de sueño y VFC para calcular tu predisposición diaria.")


# --- PÁGINA: MÉTRICAS Y EVOLUCIÓN ---
elif opcion_navegacion == "📈 Métricas y Evolución":
    st.title("📈 Métricas y Evolución")
    
    df_act = st.session_state['df_actividades']
    df_sueno = st.session_state['df_sueno']
    
    if df_act.empty and df_sueno.empty:
        st.info("📊 Panel limpio. Las 6 gráficas de evolución se activarán automáticamente en cuanto se detecten datos históricos en el sistema.")
    
    # 1. Gráfica de FC Reposo y VFC (Quincena)
    st.markdown("#### 1. Evolución Quincenal: FC Reposo vs VFC")
    if not df_sueno.empty:
        st.caption("Falta mapear las columnas exactas de tu archivo de sueño para dibujar la línea temporal.")
    else:
        st.caption("Esperando datos de salud...")

    # 2. Gráfica del Estado de Entrenamiento
    st.markdown("#### 2. Estado de Entrenamiento actual")
    if not df_act.empty:
        st.caption("Falta definir las variables de carga de tu archivo de actividades.")
    else:
        st.caption("Esperando datos de actividades...")

    # 3. Ritmo medio min/km en las 5 zonas de FC de carrera
    st.markdown("#### 3. Ritmo Medio (min/km) por Zonas de Frecuencia Cardíaca")
    if not df_act.empty:
        st.caption("Falta configurar los rangos de tus zonas de FC.")
    else:
        st.caption("Esperando datos de carrera...")

    # 4. Tabla de cargas máximas de Fuerza (RM Actual vs Medio Anterior)
    st.markdown("#### 4. Control de Cargas de Fuerza")
    df_fuerza_vacio = pd.DataFrame(columns=["Ejercicio", "Peso Máximo Levantado (RM)", "Peso Anterior Medio"])
    st.dataframe(df_fuerza_vacio, use_container_width=True)

    # 5. Km recorridos por semana en un mes
    st.markdown("#### 5. Volumen Semanal de Carrera (Mes Actual)")
    if not df_act.empty:
        st.caption("Falta estructurar el contador de kilómetros semanales.")
    else:
        st.caption("Esperando kilometraje...")

    # 6. Gráfico de Grado Máximo de Escalada (Vía y Bloque)
    st.markdown("#### 6. Progresión en Escalada (Grado Máximo por Semana)")
    df_escalada_vacio = pd.DataFrame(columns=["Semana", "Escalada Interior", "Escalada Exterior", "Bloque / Boulder"])
    st.dataframe(df_escalada_vacio, use_container_width=True)


# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")
    st.info("Sección preparada y limpia. Sin datos simulados.")

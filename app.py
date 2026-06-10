import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from PIL import Image
import os
import io

# Intento de importar fitparse (se requiere añadir 'fitparse' a requirements.txt)
try:
    import fitparse
except ImportError:
    fitparse = None

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Hybrid Training Hub", page_icon="🏋️", layout="wide")

FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"

def cargar_historico(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# 2. ESTADO DE LA APP Y ALMACENAMIENTO
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_historico(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_historico(FILE_SUENO)
if 'imagenes_capturas' not in st.session_state:
    st.session_state['imagenes_capturas'] = []
    
# Diccionario estructurado para la planificación semanal (Microciclo)
if 'plan_semanal' not in st.session_state:
    st.session_state['plan_semanal'] = {
        dia: {"Fuerza": "Sin asignar", "Resistencia": "Sin asignar"} for dia in dias_semana
    }

dia_actual_texto = dias_semana[datetime.today().weekday()]

# 3. NAVEGACIÓN
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Navegación:",
    [
        "🏠 Inicio", 
        "🗓️ Microciclo", 
        "🗺️ Macrociclo", 
        "📥 Ingresar Datos", 
        "📈 Métricas y Evolución", 
        "📜 Históricos"
    ]
)

# --- PÁGINA: INGRESAR DATOS ---
if opcion_navegacion == "📥 Ingresar Datos":
    st.title("📥 Ingresar y Modificar Datos")
    
    # 1. SUBIDA DE ARCHIVOS
    st.header("1. Carga de Archivos")
    st.write("Soporta: .csv (sueño/vfc/actividades), .fit (actividad Garmin), .jpg/.png (capturas)")
    archivos_subidos = st.file_uploader(
        "Arrastra aquí tus archivos", 
        type=["csv", "fit", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    if archivos_subidos:
        for archivo in archivos_subidos:
            nombre = archivo.name.lower()
            
            # Imágenes
            if nombre.endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(archivo)
                st.session_state['imagenes_capturas'].append({"name": archivo.name, "image": img})
                st.success(f"📷 Captura guardada: {archivo.name}")
            
            # Archivos FIT de Garmin
            elif nombre.endswith('.fit'):
                if fitparse is None:
                    st.error("Librería 'fitparse' no encontrada. Añádela al requirements.txt")
                else:
                    try:
                        # Leer el archivo binario
                        fitfile = fitparse.FitFile(archivo.getvalue())
                        records = []
                        for record in fitfile.get_messages('record'):
                            datos = {data.name: data.value for data in record}
                            records.append(datos)
                        df_fit = pd.DataFrame(records)
                        st.success(f"⏱️ Archivo .fit ({archivo.name}) procesado. {len(df_fit)} registros encontrados.")
                        # Aquí se integraría con df_actividades una vez definamos tus columnas clave
                    except Exception as e:
                        st.error(f"Error leyendo {archivo.name}: {e}")

            # Archivos CSV
            elif nombre.endswith('.csv'):
                try:
                    df_nuevo = pd.read_csv(archivo)
                    columnas_str = "".join(df_nuevo.columns).lower()
                    
                    if "sueño" in nombre or "sleep" in nombre or "vfc" in nombre or "vfc" in columnas_str:
                        df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates() if not st.session_state['df_sueno'].empty else df_nuevo
                        st.session_state['df_sueno'] = df_total
                        df_total.to_csv(FILE_SUENO, index=False)
                        st.success(f"💤 Datos de sueño/VFC actualizados: {archivo.name}")
                    
                    elif "activities" in nombre or "activity" in nombre:
                        df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates() if not st.session_state['df_actividades'].empty else df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"🏃‍♂️ Actividades actualizadas: {archivo.name}")
                        
                except Exception as e:
                    st.error(f"Error con el CSV {archivo.name}: {e}")

    st.write("---")
    
    # 2. EDITOR MANUAL DE RUTINAS (Recuperado)
    st.header("2. Modificar Entrenamientos de la Semana")
    st.write("Cualquier cambio aquí se reflejará automáticamente en el Microciclo y en la pantalla de Inicio.")
    
    pestanas = st.tabs(dias_semana)
    for i, dia in enumerate(dias_semana):
        with pestanas[i]:
            f_val = st.text_area(f"💪 Fuerza - {dia}", value=st.session_state['plan_semanal'][dia]["Fuerza"], key=f"f_{dia}")
            r_val = st.text_area(f"🏃‍♂️ Resistencia - {dia}", value=st.session_state['plan_semanal'][dia]["Resistencia"], key=f"r_{dia}")
            
            # Guardado automático en el diccionario de la sesión
            st.session_state['plan_semanal'][dia]["Fuerza"] = f_val
            st.session_state['plan_semanal'][dia]["Resistencia"] = r_val
            
    st.success("Cambios en la rutina guardados en memoria.")

# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    col_izq, col_der = st.columns([3, 2])
    
    with col_izq:
        st.markdown("### 📋 Sesión Planificada")
        # Leemos los datos directamente de lo que se haya escrito en la pestaña Ingresar Datos
        entreno_hoy = st.session_state['plan_semanal'][dia_actual_texto]
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**💪 Fuerza:**\n\n{entreno_hoy['Fuerza']}")
        with c2:
            st.success(f"**🏃‍♂️ Resistencia:**\n\n{entreno_hoy['Resistencia']}")

    with col_der:
        st.markdown("### 🚦 Predisposición (Semáforo)")
        if not st.session_state['df_sueno'].empty:
            st.info("🔄 Procesando últimas métricas de salud (Esperando mapeo de columnas)...")
        else:
            st.warning("⚠️ Sin datos de sueño/VFC para calcular estado.")

# --- PÁGINA: MICROCICLO ---
elif opcion_navegacion == "🗓️ Microciclo":
    st.title("🗓️ Programación Semanal (Microciclo)")
    st.write("Vista completa de la semana. Edita estos ejercicios en la pestaña 'Ingresar Datos'.")
    
    # Creamos un diseño de cuadrícula (3 columnas arriba, 4 abajo para distribuir los 7 días)
    cols_top = st.columns(3)
    cols_bottom = st.columns(4)
    
    for i, dia in enumerate(dias_semana):
        # Seleccionamos la columna correspondiente
        col = cols_top[i] if i < 3 else cols_bottom[i-3]
        
        with col:
            # Creamos una "caja sombreada" usando contenedores y markdown
            st.markdown(f"#### {dia}")
            st.markdown(
                f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444;">
                    <span style="color: #4da6ff;"><b>💪 Fuerza:</b></span><br>
                    <span style="font-size: 0.9em;">{st.session_state['plan_semanal'][dia]['Fuerza']}</span><br><br>
                    <span style="color: #5cd65c;"><b>🏃‍♂️ Resistencia:</b></span><br>
                    <span style="font-size: 0.9em;">{st.session_state['plan_semanal'][dia]['Resistencia']}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.write("") # Espaciado

# --- PÁGINA: MACROCICLO ---
elif opcion_navegacion == "🗺️ Macrociclo":
    st.title("🗺️ Visión Global (Macrociclo)")
    
    # Matriz estructurada en tabla
    st.write("### Objetivos de la Fase Actual")
    
    # Datos en crudo para renderizar una tabla limpia
    datos_macro = {
        "Semana": ["Semana 1", "Semana 2", "Semana 3", "Semana 4 (Descarga)"],
        "Fase Entrenamiento": ["Acumulación", "Intensificación", "Realización (Pico)", "Descarga / Tapering"],
        "Objetivo Fuerza": ["Volumen (Hipertrofia/Fuerza base)", "Fuerza Máxima (Subida de % RM)", "Mantenimiento / Potencia", "Recuperación activa"],
        "Objetivo Resistencia": ["Base aeróbica (Z2)", "Umbral y Series (Z4)", "Especificidad ritmo carrera", "Trote suave (Z1)"]
    }
    
    st.table(pd.DataFrame(datos_macro))
    st.caption("Esta tabla puede adaptarse para mostrar periodizaciones anuales más adelante.")

# --- PÁGINA: MÉTRICAS Y EVOLUCIÓN ---
elif opcion_navegacion == "📈 Métricas y Evolución":
    st.title("📈 Métricas y Evolución")
    st.info("📊 Panel de gráficas. Esperando a definir las columnas de tus CSV.")

# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")
    st.info("Sección preparada para cruzar datos anuales.")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from PIL import Image
import os

# Intento de importar fitparse de forma segura
try:
    import fitparse
except ImportError:
    fitparse = None

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Hybrid Training Hub", page_icon="🏋️", layout="wide")

# Rutas de archivos físicos en el servidor para persistencia real
FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"
FILE_PLAN = "datos_plan.json"  # Cambiado a JSON para guardar estructuras complejas de texto

# 2. FUNCIONES DE CARGA Y GUARDADO SEGURO
def cargar_csv_persistente(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_plan_json(plan):
    import json
    with open(FILE_PLAN, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=4)

def cargar_plan_json():
    import json
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    if os.path.exists(FILE_PLAN):
        try:
            with open(FILE_PLAN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {dia: {"Fuerza": "Sin asignar", "Resistencia": "Sin asignar"} for dia in dias}

# Inicialización de datos cargando directamente desde los archivos del servidor
if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_csv_persistente(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_csv_persistente(FILE_SUENO)
if 'plan_semanal' not in st.session_state:
    st.session_state['plan_semanal'] = cargar_plan_json()
if 'imagenes_capturas' not in st.session_state:
    st.session_state['imagenes_capturas'] = []

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dia_actual_texto = dias_semana[datetime.today().weekday()]

# 3. NAVEGACIÓN
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Navegación:",
    ["🏠 Inicio", "🗓️ Microciclo", "🗺️ Macrociclo", "📥 Ingresar Datos", "📈 Métricas y Evolución", "📜 Históricos"]
)

# --- PÁGINA: INGRESAR DATOS ---
if opcion_navegacion == "📥 Ingresar Datos":
    st.title("📥 Ingresar y Modificar Datos")
    
    st.header("1. Carga de Archivos")
    st.write("Sube tus archivos. Se guardarán de forma permanente en el servidor.")
    
    archivos_subidos = st.file_uploader(
        "Arrastra aquí tus archivos (.csv, .fit, .jpg, .png)", 
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
                st.success(f"📷 Captura procesada temporalmente: {archivo.name}")
            
            # Archivos FIT
            elif nombre.endswith('.fit'):
                if fitparse is not None:
                    try:
                        fitfile = fitparse.FitFile(archivo.getvalue())
                        records = []
                        for record in fitfile.get_messages('record'):
                            datos = {data.name: data.value for data in record}
                            records.append(datos)
                        df_fit = pd.DataFrame(records)
                        
                        # Guardamos o acumulamos en el archivo persistente de actividades
                        if not st.session_state['df_actividades'].empty:
                            df_total = pd.concat([st.session_state['df_actividades'], df_fit]).drop_duplicates().reset_index(drop=True)
                        else:
                            df_total = df_fit
                        
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"⏱️ Archivo FIT procesado y guardado permanentemente: {archivo.name}")
                    except Exception as e:
                        st.error(f"Error procesando archivo FIT {archivo.name}: {e}")
                else:
                    st.error("Instala 'fitparse' en tu requirements.txt para leer archivos .fit")

            # Archivos CSV
            elif nombre.endswith('.csv'):
                try:
                    df_nuevo = pd.read_csv(archivo)
                    columnas_str = "".join(df_nuevo.columns).lower()
                    
                    # Identificar tipo de CSV (Sueño / VFC)
                    if "sueño" in nombre or "sleep" in nombre or "vfc" in nombre or "vfc" in columnas_str or "hrv" in columnas_str:
                        if not st.session_state['df_sueno'].empty:
                            df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates().reset_index(drop=True)
                        else:
                            df_total = df_nuevo
                        st.session_state['df_sueno'] = df_total
                        df_total.to_csv(FILE_SUENO, index=False)
                        st.success(f"💤 Datos de Salud/Sueño guardados permanentemente: {archivo.name}")
                    
                    # Identificar tipo de CSV (Actividades generales)
                    elif "activities" in nombre or "activity" in nombre or "distancia" in columnas_str:
                        if not st.session_state['df_actividades'].empty:
                            df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True)
                        else:
                            df_total = df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"🏃‍♂️ Actividades guardadas permanentemente: {archivo.name}")
                        
                except Exception as e:
                    st.error(f"Error con el CSV {archivo.name}: {e}")

    st.write("---")
    
    # 2. EDITOR MANUAL RESTAURADO Y PERSISTENTE
    st.header("2. Modificar Entrenamientos de la Semana")
    st.write("Los cambios realizados aquí quedan grabados en el servidor de forma fija.")
    
    pestanas = st.tabs(dias_semana)
    for i, dia in enumerate(dias_semana):
        with pestanas[i]:
            f_val = st.text_area(f"💪 Fuerza - {dia}", value=st.session_state['plan_semanal'][dia]["Fuerza"], key=f"f_{dia}")
            r_val = st.text_area(f"🏃‍♂️ Resistencia - {dia}", value=st.session_state['plan_semanal'][dia]["Resistencia"], key=f"r_{dia}")
            
            # Si el usuario modifica el texto, lo guardamos inmediatamente en el archivo físico
            if f_val != st.session_state['plan_semanal'][dia]["Fuerza"] or r_val != st.session_state['plan_semanal'][dia]["Resistencia"]:
                st.session_state['plan_semanal'][dia]["Fuerza"] = f_val
                st.session_state['plan_semanal'][dia]["Resistencia"] = r_val
                guardar_plan_json(st.session_state['plan_semanal'])

# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    col_izq, col_der = st.columns([3, 2])
    with col_izq:
        st.markdown("### 📋 Sesión Planificada")
        entreno_hoy = st.session_state['plan_semanal'].get(dia_actual_texto, {"Fuerza": "Sin asignar", "Resistencia": "Sin asignar"})
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**💪 Fuerza:**\n\n{entreno_hoy['Fuerza']}")
        with c2:
            st.success(f"**🏃‍♂️ Resistencia:**\n\n{entreno_hoy['Resistencia']}")

    with col_der:
        st.markdown("### 🚦 Predisposición (Semáforo)")
        if not st.session_state['df_sueno'].empty:
            st.success("🟢 Datos persistentes de salud detectados en el servidor. Listos para activar el algoritmo gráfico.")
        else:
            st.warning("⚠️ Sin datos de salud guardados. Sube un CSV de sueño para activar.")

# --- PÁGINA: MICROCICLO ---
elif opcion_navegacion == "🗓️ Microciclo":
    st.title("🗓️ Programación Semanal (Microciclo)")
    
    cols_top = st.columns(3)
    cols_bottom = st.columns(4)
    
    for i, dia in enumerate(dias_semana):
        col = cols_top[i] if i < 3 else cols_bottom[i-3]
        with col:
            st.markdown(f"#### {dia}")
            st.markdown(
                f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444; min-height: 180px;">
                    <span style="color: #4da6ff;"><b>💪 Fuerza:</b></span><br>
                    <span style="font-size: 0.9em;">{st.session_state['plan_semanal'][dia]['Fuerza']}</span><br><br>
                    <span style="color: #5cd65c;"><b>🏃‍♂️ Resistencia:</b></span><br>
                    <span style="font-size: 0.9em;">{st.session_state['plan_semanal'][dia]['Resistencia']}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.write("")

# --- PÁGINA: MACROCICLO ---
elif opcion_navegacion == "🗺️ Macrociclo":
    st.title("🗺️ Visión Global (Macrociclo)")
    datos_macro = {
        "Semana": ["Semana 1", "Semana 2", "Semana 3", "Semana 4 (Descarga)"],
        "Fase Entrenamiento": ["Acumulación", "Intensificación", "Realización (Pico)", "Descarga / Tapering"],
        "Objetivo Fuerza": ["Volumen (Hipertrofia/Fuerza base)", "Fuerza Máxima (Subida de % RM)", "Mantenimiento / Potencia", "Recuperación activa"],
        "Objetivo Resistencia": ["Base aeróbica (Z2)", "Umbral y Series (Z4)", "Especificidad ritmo carrera", "Taper suave (Z1)"]
    }
    st.table(pd.DataFrame(datos_macro))

# --- PÁGINA: MÉTRICAS Y EVOLUCIÓN ---
elif opcion_navegacion == "📈 Métricas y Evolución":
    st.title("📈 Métricas y Evolución")
    st.write(f"Registros de actividad guardados: {len(st.session_state['df_actividades'])}")
    st.write(f"Registros de salud guardados: {len(st.session_state['df_sueno'])}")
    st.info("Estructura de datos persistente lista. Siguiente paso: Dibujar las 6 gráficas.")

# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")

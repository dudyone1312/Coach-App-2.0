import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from PIL import Image
import os
import json

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Hybrid Training Hub", page_icon="🏋️", layout="wide")

FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"
FILE_PLAN = "datos_plan.json"

# 2. FUNCIONES DE PERSISTENCIA REAL
def cargar_csv_persistente(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_plan_json(plan):
    with open(FILE_PLAN, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=4)

def cargar_plan_json():
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    # Plantilla de entrenamiento estructurada por defecto (Sustituye al 'Sin asignar')
    plantilla_base = {
        "Lunes": {"Fuerza": "Empuje (Pecho/Hombro/Tríceps) - Enfoque Hipertrofia", "Resistencia": "Carrera Continua: 45 min en Zona 2 (Ritmo cómodo)"},
        "Martes": {"Fuerza": "Tracción (Espalda/Bíceps) + Core Estable", "Resistencia": "Series de Velocidad: Calentamiento + 5x1000m (Ritmo Umbral) + Enfriamiento"},
        "Miércoles": {"Fuerza": "Pierna Completa (Sentadilla/Fuerza Máxima)", "Resistencia": "Descanso Activo / Movilidad articular y estiramientos"},
        "Jueves": {"Fuerza": "Torso General / Enfoque Escalada (Core y Agarre)", "Resistencia": "Carrera de Tempo: 20 min Z2 + 20 min Z3/Z4 + 10 min Z1"},
        "Viernes": {"Fuerza": "Full Body (Potencia / Transferencia)", "Resistencia": "Trote regenerativo: 30 min en Zona 1"},
        "Sábado": {"Fuerza": "Sesión de Escalada en Bloque (Progresión de grado)", "Resistencia": "Tirada Larga: 75-90 min en Zona 2 (Acumulación de volumen)"},
        "Domingo": {"Fuerza": "Descanso Total - Recuperación muscular", "Resistencia": "Descanso Total - Monitorizar VFC y Sueño"}
    }
    
    if os.path.exists(FILE_PLAN):
        try:
            with open(FILE_PLAN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Si no existe el archivo, guardamos la plantilla base inmediatamente para que sea retenida
    guardar_plan_json(plantilla_base)
    return plantilla_base

# Inicialización de estados y carga desde servidor
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

# 3. NAVEGACIÓN LATERAL
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Navegación:",
    ["🏠 Inicio", "🗓️ Microciclo", "🗺️ Macrociclo", "📥 Ingresar Datos", "📈 Métricas y Evolución", "📜 Históricos"]
)

# --- PÁGINA: INGRESAR DATOS ---
if opcion_navegacion == "📥 Ingresar Datos":
    st.title("📥 Ingresar y Modificar Datos")
    
    st.header("1. Carga de Archivos")
    archivos_subidos = st.file_uploader(
        "Arrastra aquí tus archivos (.csv, .fit, .jpg, .png)", 
        type=["csv", "fit", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    if archivos_subidos:
        for archivo in archivos_subidos:
            nombre = archivo.name.lower()
            
            if nombre.endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(archivo)
                st.session_state['imagenes_capturas'].append({"name": archivo.name, "image": img})
                st.success(f"📷 Captura guardada en la sesión: {archivo.name}")
            
            elif nombre.endswith('.csv'):
                try:
                    df_nuevo = pd.read_csv(archivo)
                    columnas_str = "".join(df_nuevo.columns).lower()
                    
                    if "sueño" in nombre or "sleep" in nombre or "vfc" in nombre or "vfc" in columnas_str or "hrv" in columnas_str:
                        df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_sueno'].empty else df_nuevo
                        st.session_state['df_sueno'] = df_total
                        df_total.to_csv(FILE_SUENO, index=False)
                        st.success(f"💤 Datos de Salud/Sueño sincronizados y guardados ({len(df_total)} filas).")
                    
                    elif "activities" in nombre or "activity" in nombre or "distancia" in columnas_str or "distance" in columnas_str:
                        df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_actividades'].empty else df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"🏃‍♂️ Actividades sincronizadas y guardadas ({len(df_total)} filas).")
                        
                except Exception as e:
                    st.error(f"Error procesando el CSV {archivo.name}: {e}")

    st.write("---")
    
    # 2. EDITOR MANUAL CON RETENCIÓN REFORZADA
    st.header("2. Modificar Entrenamientos de la Semana")
    st.write("Modifica los bloques de texto abajo y presiona el botón 'Guardar Cambios Semanales' para consolidar.")
    
    # Creamos un diccionario temporal en base a lo que ya existe
    plan_editado = {}
    pestanas = st.tabs(dias_semana)
    
    for i, dia in enumerate(dias_semana):
        with pestanas[i]:
            f_val = st.text_area(f"💪 Fuerza - {dia}", value=st.session_state['plan_semanal'][dia]["Fuerza"], key=f"f_input_{dia}")
            r_val = st.text_area(f"🏃‍♂️ Resistencia - {dia}", value=st.session_state['plan_semanal'][dia]["Resistencia"], key=f"r_input_{dia}")
            plan_editado[dia] = {"Fuerza": f_val, "Resistencia": r_val}
            
    if st.button("💾 Guardar Cambios Semanales", type="primary"):
        st.session_state['plan_semanal'] = plan_editado
        guardar_plan_json(plan_editado)
        st.success("✅ ¡Rutina actualizada con éxito! Se reflejará de inmediato en Inicio y Microciclo.")

# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    col_izq, col_der = st.columns([3, 2])
    with col_izq:
        st.markdown("### 📋 Sesión Planificada para Hoy")
        entreno_hoy = st.session_state['plan_semanal'].get(dia_actual_texto, {"Fuerza": "No pautado", "Resistencia": "No pautado"})
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**💪 Fuerza:**\n\n{entreno_hoy['Fuerza']}")
        with c2:
            st.success(f"**🏃‍♂️ Resistencia:**\n\n{entreno_hoy['Resistencia']}")

    with col_der:
        st.markdown("### 🚦 Predisposición (Semáforo)")
        if not st.session_state['df_sueno'].empty:
            st.success(f"🟢 {len(st.session_state['df_sueno'])} registros de salud cargados. Esperando nombres de columna para pintar el indicador.")
        else:
            st.warning("⚠️ Sin datos de salud guardados. Sube un archivo CSV de sueño para activar el cálculo dinámico.")

# --- PÁGINA: MICROCICLO ---
elif opcion_navegacion == "🗓️ Microciclo":
    st.title("🗓️ Programación Semanal (Microciclo)")
    st.write("Cajas de entrenamiento consolidadas para esta semana:")
    
    cols_top = st.columns(3)
    cols_bottom = st.columns(4)
    
    for i, dia in enumerate(dias_semana):
        col = cols_top[i] if i < 3 else cols_bottom[i-3]
        with col:
            st.markdown(f"#### {dia}")
            st.markdown(
                f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444; min-height: 200px;">
                    <span style="color: #4da6ff;"><b>💪 Fuerza:</b></span><br>
                    <span style="font-size: 0.9em; color: #dddddd;">{st.session_state['plan_semanal'][dia]['Fuerza']}</span><br><br>
                    <span style="color: #5cd65c;"><b>🏃‍♂️ Resistencia:</b></span><br>
                    <span style="font-size: 0.9em; color: #dddddd;">{st.session_state['plan_semanal'][dia]['Resistencia']}</span>
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
    
    df_act = st.session_state['df_actividades']
    df_sueno = st.session_state['df_sueno']
    
    st.metric("Registros de Actividad Detectados", len(df_act))
    st.metric("Registros de Salud/Sueño Detectados", len(df_sueno))
    
    st.markdown("### 🔍 Inspector de Columnas en Servidor")
    st.write("Escríbeme los nombres que aparecen aquí abajo para activar el graficado automatizado:")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Columnas de Actividades:**")
        if not df_act.empty:
            st.code(list(df_act.columns))
        else:
            st.caption("Aún no has subido archivos de actividad.")
    with c2:
        st.write("**Columnas de Sueño/Salud:**")
        if not df_sueno.empty:
            st.code(list(df_sueno.columns))
        else:
            st.caption("Aún no has subido archivos de salud.")

# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")
    st.info("Módulo preparado para las analíticas macro-anuales.")

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

# 2. FUNCIONES DE PERSISTENCIA REAL (SIN DATOS FALSOS)
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
    # Inicialización rigurosamente vacía, sin ejemplos del sistema
    plantilla_limpia = {dia: {"Fuerza": "", "Resistencia": ""} for dia in dias}
    
    if os.path.exists(FILE_PLAN):
        try:
            with open(FILE_PLAN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
            
    guardar_plan_json(plantilla_limpia)
    return plantilla_limpia

# Inicialización de estados leyendo el servidor
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
                        st.success(f"💤 Datos de Salud/Sueño sincronizados ({len(df_total)} filas totales).")
                    
                    elif "activities" in nombre or "activity" in nombre or "distancia" in columnas_str or "distance" in columnas_str:
                        df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_actividades'].empty else df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"🏃‍♂️ Actividades sincronizadas ({len(df_total)} filas totales).")
                        
                except Exception as e:
                    st.error(f"Error procesando el CSV {archivo.name}: {e}")

    st.write("---")
    
    st.header("2. Modificar Entrenamientos de la Semana")
    st.write("Escribe o modifica libremente los entrenamientos. Déjalos vacíos si no hay actividad programada.")
    
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
        st.success("✅ Rutina actualizada. Cambios aplicados en Microciclo e Inicio.")

# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    col_izq, col_der = st.columns([3, 2])
    with col_izq:
        st.markdown("### 📋 Sesión Planificada para Hoy")
        entreno_hoy = st.session_state['plan_semanal'].get(dia_actual_texto, {"Fuerza": "", "Resistencia": ""})
        
        c1, c2 = st.columns(2)
        with c1:
            if entreno_hoy['Fuerza'].strip():
                st.info(f"**💪 Fuerza:**\n\n{entreno_hoy['Fuerza']}")
            else:
                st.caption("No hay entrenamiento de Fuerza registrado para hoy.")
        with c2:
            if entreno_hoy['Resistencia'].strip():
                st.success(f"**🏃‍♂️ Resistencia:**\n\n{entreno_hoy['Resistencia']}")
            else:
                st.caption("No hay entrenamiento de Resistencia registrado para hoy.")

    with col_der:
        st.markdown("### 🚦 Predisposición (Semáforo)")
        df_sueno = st.session_state['df_sueno']
        if not df_sueno.empty:
            st.success("🟢 Datos de salud detectados. Ve a 'Métricas y Evolución' para enlazar las columnas y activar los indicadores.")
        else:
            st.warning("⚠️ Sin datos de salud guardados.")

# --- PÁGINA: MICROCICLO ---
elif opcion_navegacion == "🗓️ Microciclo":
    st.title("🗓️ Programación Semanal (Microciclo)")
    
    cols_top = st.columns(3)
    cols_bottom = st.columns(4)
    
    for i, dia in enumerate(dias_semana):
        col = cols_top[i] if i < 3 else cols_bottom[i-3]
        with col:
            st.markdown(f"#### {dia}")
            fuerza_txt = st.session_state['plan_semanal'][dia]['Fuerza']
            res_txt = st.session_state['plan_semanal'][dia]['Resistencia']
            
            # Solo pintamos si contienen texto real
            fuerza_html = f"<span style='color: #4da6ff;'><b>💪 Fuerza:</b></span><br><span style='font-size: 0.9em;'>{fuerza_txt}</span><br><br>" if fuerza_txt.strip() else "<span style='color: #666;'>Fuerza: Vacío</span><br><br>"
            res_html = f"<span style='color: #5cd65c;'><b>🏃‍♂️ Resistencia:</b></span><br><span style='font-size: 0.9em;'>{res_txt}</span>" if res_txt.strip() else "<span style='color: #666;'>Resistencia: Vacío</span>"
            
            st.markdown(
                f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444; min-height: 180px;">
                    {fuerza_html}
                    {res_html}
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
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Registros de Actividades (Histórico)", len(df_act))
    col_m2.metric("Registros de Salud/Sueño (Histórico)", len(df_sueno))
    
    st.write("---")
    
    # ASIGNADOR DINÁMICO DE COLUMNAS (Para que no falle ninguna gráfica)
    st.sidebar.markdown("## ⚙️ Mapeo de Variables")
    st.sidebar.write("Selecciona qué columna corresponde a cada métrica de tus archivos:")
    
    col_fecha_act, col_dist, col_ritmo = None, None, None
    col_fecha_sueno, col_vfc, col_reposo = None, None, None
    
    if not df_act.empty:
        col_fecha_act = st.sidebar.selectbox("Fecha (Actividades)", list(df_act.columns), key="c_f_a")
        col_dist = st.sidebar.selectbox("Distancia / Volumen", list(df_act.columns), key="c_d_a")
        col_ritmo = st.sidebar.selectbox("Ritmo / Velocidad Media", list(df_act.columns), key="c_r_a")
        
    if not df_sueno.empty:
        col_fecha_sueno = st.sidebar.selectbox("Fecha (Sueño)", list(df_sueno.columns), key="c_f_s")
        col_vfc = st.sidebar.selectbox("VFC / HRV", list(df_sueno.columns), key="c_v_s")
        col_reposo = st.sidebar.selectbox("FC Reposo", list(df_sueno.columns), key="c_r_s")

    # RENDERIZADO DE LAS GRÁFICAS EN BASE A TU SELECCIÓN SIDEBAR
    
    # Gráfica 1: FC Reposo vs VFC
    st.subheader("1. Evolución de Salud: FC Reposo vs VFC (Histórico)")
    if not df_sueno.empty and col_vfc and col_reposo and col_fecha_sueno:
        try:
            df_sueno_sorted = df_sueno.sort_values(by=col_fecha_sueno)
            fig1 = px.line(df_sueno_sorted, x=col_fecha_sueno, y=[col_vfc, col_reposo], markers=True, title="Tendencia de Recuperación")
            st.plotly_chart(fig1, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo generar el gráfico 1: {e}")
    else:
        st.info("Configura las columnas de Sueño en el menú lateral para activar esta gráfica.")

    # Gráfica 2: Volumen Semanal de Carrera
    st.subheader("2. Volumen Acumulado (Distancia)")
    if not df_act.empty and col_dist and col_fecha_act:
        try:
            df_act_sorted = df_act.sort_values(by=col_fecha_act)
            fig2 = px.bar(df_act_sorted, x=col_fecha_act, y=col_dist, title="Carga por Sesión")
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo generar el gráfico 2: {e}")
    else:
        st.info("Configura las columnas de Actividades en el menú lateral para activar esta gráfica.")
        
    # Gráfica 3: Ritmo Medio
    st.subheader("3. Análisis de Ritmo Medio")
    if not df_act.empty and col_ritmo and col_fecha_act:
        try:
            df_act_sorted = df_act.sort_values(by=col_fecha_act)
            fig3 = px.line(df_act_sorted, x=col_fecha_act, y=col_ritmo, markers=True, title="Evolución de Ritmos")
            st.plotly_chart(fig3, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo generar el gráfico 3: {e}")
    else:
        st.info("Configura la columna de Ritmo en el menú lateral para visualizar la evolución.")

    # Gráficas de control manual (Fuerza y Escalada)
    st.subheader("4. Control de Cargas de Fuerza Máxima")
    st.caption("Se alimentará dinámicamente de tus inputs de fuerza guardados.")
    
    st.subheader("5. Progresión en Escalada (Grado Máximo)")
    st.caption("Se alimentará dinámicamente en base a tus registros de bloque y vía.")

# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")
    st.info("Sección preparada para almacenar los cierres de temporada.")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime, timedelta
from PIL import Image
import os
import json

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Hybrid Training Hub", page_icon="🏋️", layout="wide")

FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"
FILE_PLAN = "datos_plan.json"
FILE_FUERZA = "datos_fuerza.json"
FILE_ESCALADA = "datos_escalada.json"

# 2. FUNCIONES DE PERSISTENCIA COMPLETAMENTE LIMPIAS (SIN EJEMPLOS FALSOS)
def cargar_csv_persistente(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def guardar_json(datos, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

def cargar_json(file_path, defecto):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return defecto

# Inicialización rigurosamente vacía
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_csv_persistente(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_csv_persistente(FILE_SUENO)
if 'plan_semanal' not in st.session_state:
    st.session_state['plan_semanal'] = cargar_json(FILE_PLAN, {dia: {"Fuerza": "", "Resistencia": ""} for dia in dias_semana})
if 'datos_fuerza' not in st.session_state:
    st.session_state['datos_fuerza'] = cargar_json(FILE_FUERZA, [])
if 'datos_escalada' not in st.session_state:
    st.session_state['datos_escalada'] = cargar_json(FILE_ESCALADA, [])
if 'imagenes_capturas' not in st.session_state:
    st.session_state['imagenes_capturas'] = []

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
    
    # Bloque 1: Carga de archivos de Garmin
    st.header("1. Carga de Archivos Garmin (.csv, .fit)")
    archivos_subidos = st.file_uploader(
        "Arrastra aquí tus archivos", 
        type=["csv", "fit", "png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    
    if archivos_subidos:
        for archivo in archivos_subidos:
            nombre = archivo.name.lower()
            if nombre.endswith(('.png', '.jpg', '.jpeg')):
                img = Image.open(archivo)
                st.session_state['imagenes_capturas'].append({"name": archivo.name, "image": img})
                st.success(f"📷 Captura procesada: {archivo.name}")
            elif nombre.endswith('.csv'):
                try:
                    df_nuevo = pd.read_csv(archivo)
                    columnas_str = "".join(df_nuevo.columns).lower()
                    if "sueño" in nombre or "sleep" in nombre or "vfc" in nombre or "vfc" in columnas_str or "hrv" in columnas_str:
                        df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_sueno'].empty else df_nuevo
                        st.session_state['df_sueno'] = df_total
                        df_total.to_csv(FILE_SUENO, index=False)
                        st.success(f"💤 Archivo de Salud guardado de forma persistente.")
                    elif "activities" in nombre or "activity" in nombre or "distancia" in columnas_str or "distance" in columnas_str:
                        df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_actividades'].empty else df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"🏃‍♂️ Archivo de Actividades guardado de forma persistente.")
                except Exception as e:
                    st.error(f"Error con el CSV {archivo.name}: {e}")

    st.write("---")
    
    # Bloque 2: Editor de planificación semanal
    st.header("2. Modificar Planificación del Microciclo")
    plan_editado = {}
    pestanas = st.tabs(dias_semana)
    for i, dia in enumerate(dias_semana):
        with pestanas[i]:
            f_val = st.text_area(f"💪 Fuerza - {dia}", value=st.session_state['plan_semanal'][dia]["Fuerza"], key=f"f_in_{dia}")
            r_val = st.text_area(f"🏃‍♂️ Resistencia - {dia}", value=st.session_state['plan_semanal'][dia]["Resistencia"], key=f"r_in_{dia}")
            plan_editado[dia] = {"Fuerza": f_val, "Resistencia": r_val}
            
    if st.button("💾 Guardar Planificación Semanal"):
        st.session_state['plan_semanal'] = plan_editado
        guardar_json(plan_editado, FILE_PLAN)
        st.success("✅ Planificación guardada correctamente.")

    st.write("---")

    # Bloque 3: Inputs manuales para Fuerza y Escalada (Necesarios para las gráficas 4 y 6)
    st.header("3. Registrar Marcas de Fuerza y Escalada")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.subheader("🏋️‍♂️ Añadir Récord de Fuerza (PR)")
        ejercicio = st.text_input("Ejercicio (ej. Sentadilla, Press Banca)")
        rec_act = st.text_input("Récord Actual (ej. 120 kg (4x5))")
        rec_ant = st.text_input("Récord Anterior (ej. 115 kg)")
        if st.button("➕ Guardar PR Fuerza"):
            if ejercicio and rec_act:
                # Filtrar si ya existe para actualizarlo
                st.session_state['datos_fuerza'] = [x for x in st.session_state['datos_fuerza'] if x['ejercicio'] != ejercicio]
                st.session_state['datos_fuerza'].append({"ejercicio": ejercicio, "actual": rec_act, "anterior": rec_ant})
                guardar_json(st.session_state['datos_fuerza'], FILE_FUERZA)
                st.success(f"PR de {ejercicio} registrado.")

    with col_f2:
        st.subheader("🧗‍♂️ Añadir Progresión de Escalada")
        fecha_esc = st.date_input("Fecha del Registro", value=date.today())
        tipo_esc = st.selectbox("Modalidad", ["Bloque Interior", "Bloque Exterior", "Vía Interior", "Vía Exterior"])
        grado = st.number_input("Grado Alcanzado (Formato numérico, ej. 6.5 para 6b+ o 7.0 para 7a)", min_value=1.0, max_value=10.0, step=0.1)
        if st.button("➕ Guardar Grado Escalada"):
            st.session_state['datos_escalada'].append({"fecha": str(fecha_esc), "tipo": tipo_esc, "grado": grado})
            guardar_json(st.session_state['datos_escalada'], FILE_ESCALADA)
            st.success("Grado de escalada guardado.")

# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    entreno_hoy = st.session_state['plan_semanal'].get(dia_actual_texto, {"Fuerza": "", "Resistencia": ""})
    col_izq, col_der = st.columns([3, 2])
    
    with col_izq:
        st.markdown("### 📋 Sesión Planificada para Hoy")
        c1, c2 = st.columns(2)
        with c1:
            if entreno_hoy['Fuerza'].strip():
                st.info(f"**💪 Fuerza:**\n\n{entreno_hoy['Fuerza']}")
            else:
                st.caption("No tienes programado entrenamiento de Fuerza para hoy.")
        with c2:
            if entreno_hoy['Resistencia'].strip():
                st.success(f"**🏃‍♂️ Resistencia:**\n\n{entreno_hoy['Resistencia']}")
            else:
                st.caption("No tienes programado entrenamiento de Resistencia para hoy.")

    with col_der:
        st.markdown("### 🚦 Predisposición (Semáforo)")
        if not st.session_state['df_sueno'].empty:
            st.success("🟢 Datos fisiológicos detectados en el servidor de forma estable.")
        else:
            st.warning("⚠️ Sin registros de salud en el sistema.")

# --- PÁGINA: MICROCICLO ---
elif opcion_navegacion == "🗓️ Microciclo":
    st.title("🗓️ Programación Semanal (Microciclo)")
    cols_top = st.columns(3)
    cols_bottom = st.columns(4)
    
    for i, dia in enumerate(dias_semana):
        col = cols_top[i] if i < 3 else cols_bottom[i-3]
        with col:
            st.markdown(f"#### {dia}")
            f_txt = st.session_state['plan_semanal'][dia]['Fuerza']
            r_txt = st.session_state['plan_semanal'][dia]['Resistencia']
            
            f_html = f"<span style='color: #4da6ff;'><b>💪 Fuerza:</b></span><br><span style='font-size: 0.9em;'>{f_txt}</span><br><br>" if f_txt.strip() else "<span style='color: #555;'>Fuerza: Vacío</span><br><br>"
            r_html = f"<span style='color: #5cd65c;'><b>🏃‍♂️ Resistencia:</b></span><br><span style='font-size: 0.9em;'>{r_txt}</span>" if r_txt.strip() else "<span style='color: #555;'>Resistencia: Vacío</span>"
            
            st.markdown(
                f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444; min-height: 180px;">
                    {f_html}
                    {r_html}
                </div>
                """, 
                unsafe_allow_html=True
            )

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
    st.title("📈 Cuadro de Mando de Adaptaciones Fisiológicas")
    
    df_act = st.session_state['df_actividades']
    df_sueno = st.session_state['df_sueno']
    
    # Selectores automáticos en la barra lateral para evitar errores de nombres de columna
    st.sidebar.markdown("## ⚙️ Mapeo de Columnas Reales")
    c_f_sueno, c_vfc, c_reposo = None, None, None
    c_f_act, c_dist, c_ritmo = None, None, None
    
    if not df_sueno.empty:
        c_f_sueno = st.sidebar.selectbox("Columna Fecha (Salud)", list(df_sueno.columns))
        c_vfc = st.sidebar.selectbox("Columna VFC/HRV", list(df_sueno.columns))
        c_reposo = st.sidebar.selectbox("Columna FC Reposo", list(df_sueno.columns))
    if not df_act.empty:
        c_f_act = st.sidebar.selectbox("Columna Fecha (Actividades)", list(df_act.columns))
        c_dist = st.sidebar.selectbox("Columna Kilómetros", list(df_act.columns))
        c_ritmo = st.sidebar.selectbox("Columna Ritmo Medio", list(df_act.columns))

    # DISTRIBUCIÓN DEL DASHBOARD EN MATRIZ (IGUAL A LA CAPTURA)
    bloque_1, bloque_2 = st.columns(2)
    
    with bloque_1:
        # GRAFICÓ 1: FC Reposo vs VFC Basal (Quincena)
        st.markdown("#### 1. FC Reposo vs VFC Basal (Últimos 15 días)")
        if not df_sueno.empty and c_f_sueno and c_vfc and c_reposo:
            try:
                df_sueno[c_f_sueno] = pd.to_datetime(df_sueno[c_f_sueno])
                df_q = df_sueno.sort_values(by=c_f_sueno).tail(15)
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=df_q[c_f_sueno], y=df_q[c_vfc], name="VFC (ms)", mode='lines+markers', line=dict(color='#4da6ff')))
                fig1.add_trace(go.Scatter(x=df_q[c_f_sueno], y=df_q[c_reposo], name="FC Reposo (ppm)", mode='lines+markers', line=dict(color='#ff4d4d')))
                fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250, template="plotly_dark")
                st.plotly_chart(fig1, use_container_width=True)
            except Exception as e:
                st.caption(f"Configura las columnas de salud en el lateral: {e}")
        else:
            st.info("Sube datos de salud para activar la gráfica 1.")

        # GRAFICÓ 3: Ritmo Medio por Zonas
        st.markdown("#### 3. Ritmo Medio por Zonas (min/km)")
        if not df_act.empty and c_f_act and c_ritmo:
            try:
                df_act[c_f_act] = pd.to_datetime(df_act[c_f_act])
                df_r_sorted = df_act.sort_values(by=c_f_act).tail(20)
                fig3 = px.line(df_r_sorted, x=c_f_act, y=c_ritmo, markers=True, template="plotly_dark")
                fig3.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250)
                st.plotly_chart(fig3, use_container_width=True)
            except Exception:
                st.caption("Revisa la columna de ritmo asignada en la barra lateral.")
        else:
            st.info("Sube datos de actividades para activar la gráfica 3.")

    with bloque_2:
        # GRAFICÓ 2: Túnel de Carga Aguda vs Crónica
        st.markdown("#### 2. Túnel de Carga Aguda vs Crónica")
        if not df_act.empty and c_f_act and c_dist:
            try:
                df_act[c_f_act] = pd.to_datetime(df_act[c_f_act])
                df_diario = df_act.groupby(df_act[c_f_act].dt.date)[c_dist].sum().reset_index()
                df_diario.columns = ['Fecha', 'Volumen']
                df_diario = df_diario.sort_values(by='Fecha')
                
                df_diario['Aguda'] = df_diario['Volumen'].rolling(window=7, min_periods=1).mean()
                df_diario['Cronica'] = df_diario['Volumen'].rolling(window=28, min_periods=1).mean()
                df_diario['Tunel_Min'] = df_diario['Cronica'] * 0.8
                df_diario['Tunel_Max'] = df_diario['Cronica'] * 1.3
                
                df_vis = df_diario.tail(30)
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Tunel_Max'], name="Túnel Máx", line=dict(color='rgba(0,255,0,0.2)', width=1)))
                fig2.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Tunel_Min'], name="Túnel Mín", line=dict(color='rgba(0,255,0,0.2)', width=1), fill='tonexty'))
                fig2.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Aguda'], name="Carga Real (Aguda)", line=dict(color='#ffcc00', width=2)))
                fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250, template="plotly_dark")
                st.plotly_chart(fig2, use_container_width=True)
            except Exception:
                st.caption("Esperando mapeo correcto de kilómetros.")
        else:
            st.info("Requiere datos de volumen/kilómetros.")

        # GRAFICÓ 5: KM recorridos por semana (Mes)
        st.markdown("#### 5. Volumen de Carrera Semanal (KM)")
        if not df_act.empty and c_f_act and c_dist:
            try:
                df_act[c_f_act] = pd.to_datetime(df_act[c_f_act])
                df_sem = df_act.resample('W', on=c_f_act)[c_dist].sum().reset_index().tail(4)
                df_sem[c_f_act] = df_sem[c_f_act].dt.strftime('Semana %V')
                fig5 = px.bar(df_sem, x=c_f_act, y=c_dist, labels={c_dist: "Kilómetros"}, template="plotly_dark", color_discrete_sequence=['#0084ff'])
                fig5.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250)
                st.plotly_chart(fig5, use_container_width=True)
            except Exception:
                st.caption("Error agrupando por semanas.")
        else:
            st.info("Sube datos de carrera para ver el histórico de kms.")

    st.write("---")
    bloque_3, bloque_4 = st.columns(2)
    
    with bloque_3:
        # GRAFICÓ 6: Evolución Grado Máximo Escalada
        st.markdown("#### 6. Evolución Grado Máximo Escalada")
        df_esc = pd.DataFrame(st.session_state['datos_escalada'])
        if not df_esc.empty:
            try:
                df_esc['fecha'] = pd.to_datetime(df_esc['fecha'])
                df_esc = df_esc.sort_values(by='fecha')
                fig6 = px.line(df_esc, x='fecha', y='grado', color='tipo', markers=True, template="plotly_dark")
                fig6.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=250)
                st.plotly_chart(fig6, use_container_width=True)
            except Exception:
                st.caption("Error generando líneas de escalada.")
        else:
            st.caption("No has registrado grados de escalada todavía en la pestaña de ingreso.")

    with bloque_4:
        # TABLA 4: Registro de Fuerza Máxima (PR)
        st.markdown("#### 4. Registro de Fuerza Máxima y Récords Personales (PR)")
        df_fz = pd.DataFrame(st.session_state['datos_fuerza'])
        if not df_fz.empty:
            df_fz.columns = ["Ejercicio de Fuerza", "Récord Actual", "Récord Anterior"]
            st.dataframe(df_fz, use_container_width=True, hide_index=True)
        else:
            st.caption("No has registrado récords de fuerza todavía en la pestaña de ingreso.")

# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")
    st.caption("Sección limpia lista para el cierre de datos.")

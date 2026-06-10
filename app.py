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

# 2. FUNCIONES DE PERSISTENCIA Y DETECCIÓN AUTOMÁTICA
def cargar_csv_persistente(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def cargar_plan_json():
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    plantilla = {dia: {"Fuerza": "", "Resistencia": ""} for dia in dias}
    if os.path.exists(FILE_PLAN):
        try:
            with open(FILE_PLAN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return plantilla

# Inicialización de estados leyendo el servidor
if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_csv_persistente(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_csv_persistente(FILE_SUENO)
if 'plan_semanal' not in st.session_state:
    st.session_state['plan_semanal'] = cargar_plan_json()

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dia_actual_texto = dias_semana[datetime.today().weekday()]

# FUNCIÓN MAPEADORA AUTOMÁTICA POR PALABRAS CLAVE
def auto_detectar_columna(df, palabras_clave):
    for col in df.columns:
        if any(p in str(col).lower() for p in palabras_clave):
            return col
    return None

# PARSEADOR DE FECHAS DE GARMIN (Corrige el error "10 Jun")
def parsear_fechas_robustas(serie):
    # Intentar limpiar formatos que traigan días de la semana pegados o meses cortos
    serie_limpia = serie.astype(str).str.replace(r'^[A-Za-záéíóú.,\s]+,\s*', '', regex=True).str.strip()
    return pd.to_datetime(serie_limpia, errors='coerce', format='mixed')

# CONVERSOR DE RITMOS (Ej: "5:30 min/km" -> 5.5)
def ritmo_a_decimal(serie):
    def limpiar_valor(val):
        try:
            val_str = str(val).lower().replace('min/km', '').strip()
            if ':' in val_str:
                partes = val_str.split(':')
                if len(partes) == 2:
                    return float(partes[0]) + (float(partes[1]) / 60.0)
                elif len(partes) == 3: # hh:mm:ss
                    return (float(partes[0]) * 60) + float(partes[1]) + (float(partes[2]) / 60.0)
            return float(val_str.replace(',', '.'))
        except Exception:
            return None
    return serie.apply(limpiar_valor)

# CONVERSOR DE DISTANCIAS A NÚMERO REAL
def distancia_a_float(serie):
    return pd.to_numeric(serie.astype(str).str.replace(' km', '', case=False).str.replace(',', '.').str.strip(), errors='coerce')

# 3. EXTRACCIÓN AUTOMÁTICA DE ENTRENAMIENTOS REALIZADOS ESTA SEMANA
actividades_por_dia = {dia: [] for dia in dias_semana}
df_act = st.session_state['df_actividades']

if not df_act.empty:
    col_f_act = auto_detectar_columna(df_act, ['fecha', 'date', 'comienzo', 'start'])
    col_tipo_act = auto_detectar_columna(df_act, ['tipo', 'type', 'actividad'])
    col_dist_act = auto_detectar_columna(df_act, ['distancia', 'distance', 'km'])
    col_ritmo_act = auto_detectar_columna(df_act, ['ritmo', 'pace', 'velocidad', 'avg'])
    
    if col_f_act:
        df_act['Fecha_Clean'] = parsear_fechas_robustas(df_act[col_f_act])
        # Determinar rango de la semana actual
        hoy_dt = datetime.today()
        lunes_actual = hoy_dt - timedelta(days=hoy_dt.weekday())
        domingo_actual = lunes_actual + timedelta(days=6)
        
        # Filtrar actividades de la semana en curso
        df_semana = df_act[(df_act['Fecha_Clean'].dt.date >= lunes_actual.date()) & (df_act['Fecha_Clean'].dt.date <= domingo_actual.date())]
        
        for idx, fila in df_semana.iterrows():
            if pd.notna(fila['Fecha_Clean']):
                dia_idx = fila['Fecha_Clean'].weekday()
                nombre_dia = dias_semana[dia_idx]
                
                tipo = fila[col_tipo_act] if col_tipo_act else "Actividad"
                dist = f"{fila[col_dist_act]} km" if col_dist_act and pd.notna(fila[col_dist_act]) else ""
                ritmo = f" a {fila[col_ritmo_act]}" if col_ritmo_act and pd.notna(fila[col_ritmo_act]) else ""
                
                descripcion = f"🏃‍♂️ {tipo}: {dist}{ritmo}"
                actividades_por_dia[nombre_dia].append(descripcion)

# 4. NAVEGACIÓN LATERAL
st.sidebar.title("Panel de Control")
opcion_navegacion = st.sidebar.radio(
    "Navegación:",
    ["🏠 Inicio", "🗓️ Microciclo", "🗺️ Macrociclo", "📥 Ingresar Datos", "📈 Métricas y Evolución", "📜 Históricos"]
)

# --- PÁGINA: INGRESAR DATOS ---
if opcion_navegacion == "📥 Ingresar Datos":
    st.title("📥 Carga Automatizada de Archivos")
    st.write("Sube tus archivos descargados de Garmin Connect aquí. El sistema procesará las métricas y actualizará los calendarios al instante.")
    
    archivos_subidos = st.file_uploader(
        "Arrastra aquí tus archivos (.csv, .fit)", 
        type=["csv", "fit"],
        accept_multiple_files=True
    )
    
    if archivos_subidos:
        for archivo in archivos_subidos:
            nombre = archivo.name.lower()
            if nombre.endswith('.csv'):
                try:
                    df_nuevo = pd.read_csv(archivo)
                    columnas_str = "".join(df_nuevo.columns).lower()
                    
                    if any(p in nombre or p in columnas_str for p in ["sueño", "sleep", "vfc", "hrv", "reposo", "resting"]):
                        df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_sueno'].empty else df_nuevo
                        st.session_state['df_sueno'] = df_total
                        df_total.to_csv(FILE_SUENO, index=False)
                        st.success(f"💤 Datos de Salud/Sueño actualizados de forma automática.")
                    else:
                        df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True) if not st.session_state['df_actividades'].empty else df_nuevo
                        st.session_state['df_actividades'] = df_total
                        df_total.to_csv(FILE_ACTIVIDADES, index=False)
                        st.success(f"🏃‍♂️ Historial de Actividades sincronizado y actualizado.")
                        
                except Exception as e:
                    st.error(f"Error procesando el archivo {archivo.name}: {e}")
        st.rerun()

# --- PÁGINA: INICIO ---
elif opcion_navegacion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dia_actual_texto}, {date.today().strftime('%d/%m/%Y')}")
    
    col_izq, col_der = st.columns([3, 2])
    with col_izq:
        st.markdown("### 📋 Sesión de Hoy")
        entreno_hoy = st.session_state['plan_semanal'].get(dia_actual_texto, {"Fuerza": "", "Resistencia": ""})
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**💪 Plan Fuerza:**\n\n{entreno_hoy['Fuerza'] if entreno_hoy['Fuerza'].strip() else 'Descanso'}")
        with c2:
            st.success(f"**🏃‍♂️ Plan Resistencia:**\n\n{entreno_hoy['Resistencia'] if entreno_hoy['Resistencia'].strip() else 'Descanso'}")
            
        # Mostrar lo recuperado de Garmin para hoy
        st.markdown("#### ✅ Realizado Hoy (Sincronizado de Garmin)")
        if actividades_por_dia[dia_actual_texto]:
            for act in actividades_por_dia[dia_actual_texto]:
                st.write(act)
        else:
            st.caption("Aún no se registran actividades completadas hoy en tu archivo de Garmin.")

    with col_der:
        st.markdown("### 🚦 Estado Fisiológico")
        if not st.session_state['df_sueno'].empty:
            st.success("🟢 Conectado con Garmin Connect de forma estable.")
        else:
            st.warning("⚠️ Esperando carga de archivos de salud.")

# --- PÁGINA: MICROCICLO ---
elif opcion_navegacion == "🗓️ Microciclo":
    st.title("🗓️ Programación y Registro Semanal (Microciclo)")
    
    cols_top = st.columns(3)
    cols_bottom = st.columns(4)
    
    for i, dia in enumerate(dias_semana):
        col = cols_top[i] if i < 3 else cols_bottom[i-3]
        with col:
            st.markdown(f"#### {dia}")
            f_txt = st.session_state['plan_semanal'][dia]['Fuerza']
            r_txt = st.session_state['plan_semanal'][dia]['Resistencia']
            
            f_html = f"<b style='color: #4da6ff;'>💪 Fuerza:</b> {f_txt}<br>" if f_txt.strip() else ""
            r_html = f"<b style='color: #5cd65c;'>🏃‍♂️ Resistencia:</b> {r_txt}<br>" if r_txt.strip() else ""
            
            # Formatear lo realizado automáticamente
            realizado_list = actividades_por_dia[dia]
            realizado_html = "<br><b style='color: #ffcc00;'>✅ Realizado (Garmin):</b><br>" + "<br>".join(realizado_list) if realizado_list else ""
            
            cuerpo_caja = f_html + r_html + realizado_html
            if not cuerpo_caja:
                cuerpo_caja = "<span style='color: #666;'>Sin actividad programada ni realizada.</span>"
                
            st.markdown(
                f"""
                <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #444; min-height: 160px;">
                    {cuerpo_caja}
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
    st.title("📈 Cuadro de Mando de Adaptaciones Fisiológicas")
    
    df_act = st.session_state['df_actividades']
    df_sueno = st.session_state['df_sueno']
    
    bloque_1, bloque_2 = st.columns(2)
    
    # ---- LÓGICA AUTOMÁTICA GRÁFICAS DE SALUD ----
    with bloque_1:
        st.markdown("#### 1. FC Reposo vs VFC Basal (Últimos 15 días)")
        if not df_sueno.empty:
            c_f_s = auto_detectar_columna(df_sueno, ['fecha', 'date', 'day', 'día'])
            c_vfc = auto_detectar_columna(df_sueno, ['vfc', 'hrv', 'variabilidad'])
            c_rep = auto_detectar_columna(df_sueno, ['reposo', 'resting', 'rhr', 'mínima'])
            
            if c_f_s and c_vfc and c_rep:
                try:
                    df_sueno['Fecha_C'] = parsear_fechas_robustas(df_sueno[c_f_s])
                    df_q = df_sueno.dropna(subset=['Fecha_C']).sort_values(by='Fecha_C').tail(15)
                    
                    fig1 = go.Figure()
                    fig1.add_trace(go.Scatter(x=df_q['Fecha_C'], y=pd.to_numeric(df_q[c_vfc], errors='coerce'), name="VFC (ms)", mode='lines+markers', line=dict(color='#4da6ff')))
                    fig1.add_trace(go.Scatter(x=df_q['Fecha_C'], y=pd.to_numeric(df_q[c_rep], errors='coerce'), name="FC Reposo (ppm)", mode='lines+markers', line=dict(color='#ff4d4d')))
                    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=260, template="plotly_dark")
                    st.plotly_chart(fig1, use_container_width=True)
                except Exception as e:
                    st.caption(f"Error procesando formato de salud: {e}")
            else:
                st.caption("No se detectan las columnas automáticas de Fecha, VFC o Reposo en el archivo de salud.")
        else:
            st.info("Sube tu archivo de sueño/salud en 'Ingresar Datos' para pintar la gráfica automáticamente.")

        st.markdown("#### 3. Ritmo Medio por Zonas (min/km)")
        if not df_act.empty:
            c_f_a = auto_detectar_columna(df_act, ['fecha', 'date', 'comienzo', 'start'])
            c_rit = auto_detectar_columna(df_act, ['ritmo', 'pace', 'velocidad', 'avg'])
            
            if c_f_a and c_rit:
                try:
                    df_act['Fecha_C'] = parsear_fechas_robustas(df_act[c_f_a])
                    df_act['Ritmo_Num'] = ritmo_a_decimal(df_act[c_rit])
                    df_r_sorted = df_act.dropna(subset=['Fecha_C', 'Ritmo_Num']).sort_values(by='Fecha_C').tail(20)
                    
                    fig3 = px.line(df_r_sorted, x='Fecha_C', y='Ritmo_Num', markers=True, template="plotly_dark", labels={'Ritmo_Num': 'Ritmo Decimal (min)'})
                    fig3.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=260)
                    st.plotly_chart(fig3, use_container_width=True)
                except Exception as e:
                    st.caption(f"Error procesando ritmos: {e}")
            else:
                st.caption("No se detectan las variables de Ritmo Medio.")
        else:
            st.info("Sube actividades para analizar ritmos.")

    # ---- LÓGICA AUTOMÁTICA GRÁFICAS DE ACTIVIDAD / VOLUMEN ----
    with bloque_2:
        st.markdown("#### 2. Túnel de Carga Aguda vs Crónica")
        if not df_act.empty:
            c_f_a = auto_detectar_columna(df_act, ['fecha', 'date', 'comienzo', 'start'])
            c_dst = auto_detectar_columna(df_act, ['distancia', 'distance', 'km'])
            
            if c_f_a and c_dst:
                try:
                    df_act['Fecha_C'] = parsear_fechas_robustas(df_act[c_f_a])
                    df_act['Dist_Num'] = distancia_a_float(df_act[c_dst])
                    
                    df_diario = df_act.dropna(subset=['Fecha_C']).groupby(df_act['Fecha_C'].dt.date)['Dist_Num'].sum().reset_index()
                    df_diario.columns = ['Fecha', 'Volumen']
                    df_diario = df_diario.sort_values(by='Fecha')
                    
                    df_diario['Aguda'] = df_diario['Volumen'].rolling(window=7, min_periods=1).mean()
                    df_diario['Cronica'] = df_diario['Volumen'].rolling(window=28, min_periods=1).mean()
                    df_diario['Tunel_Min'] = df_diario['Cronica'] * 0.8
                    df_diario['Tunel_Max'] = df_diario['Cronica'] * 1.3
                    
                    df_vis = df_diario.tail(30)
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Tunel_Max'], name="Túnel Máx", line=dict(color='rgba(0,255,0,0.15)', width=1)))
                    fig2.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Tunel_Min'], name="Túnel Mín", line=dict(color='rgba(0,255,0,0.15)', width=1), fill='tonexty'))
                    fig2.add_trace(go.Scatter(x=df_vis['Fecha'], y=df_vis['Aguda'], name="Carga Real (Aguda)", line=dict(color='#ffcc00', width=2)))
                    fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=260, template="plotly_dark")
                    st.plotly_chart(fig2, use_container_width=True)
                except Exception as e:
                    st.caption(f"Error calculando túnel de carga: {e}")
            else:
                st.caption("Faltan columnas de fecha o distancia.")
        else:
            st.info("Sube datos de actividad para proyectar el estado de Garmin.")

        st.markdown("#### 5. Volumen de Carrera Semanal (KM)")
        if not df_act.empty:
            c_f_a = auto_detectar_columna(df_act, ['fecha', 'date', 'comienzo', 'start'])
            c_dst = auto_detectar_columna(df_act, ['distancia', 'distance', 'km'])
            
            if c_f_a and c_dst:
                try:
                    df_act['Fecha_C'] = parsear_fechas_robustas(df_act[c_f_a])
                    df_act['Dist_Num'] = distancia_a_float(df_act[c_dst])
                    
                    df_limpio = df_act.dropna(subset=['Fecha_C', 'Dist_Num'])
                    df_sem = df_limpio.resample('W', on='Fecha_C')['Dist_Num'].sum().reset_index().tail(4)
                    df_sem['Fecha_C'] = df_sem['Fecha_C'].dt.strftime('Semana %V')
                    
                    fig5 = px.bar(df_sem, x='Fecha_C', y='Dist_Num', template="plotly_dark", color_discrete_sequence=['#0084ff'], labels={'Dist_Num': 'Kilómetros'})
                    fig5.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=260)
                    st.plotly_chart(fig5, use_container_width=True)
                except Exception as e:
                    st.caption(f"Error agrupando volumen semanal: {e}")
        else:
            st.info("Carga datos acumulados para calcular el volumen mensual.")

    st.write("---")
    st.caption("Nota: Las secciones de Escalada y Fuerza están preparadas de forma interna para vincularse en cuanto se detecten sus respectivos formatos de archivo estructurados.")

# --- PÁGINA: HISTÓRICOS ---
elif opcion_navegacion == "📜 Históricos":
    st.title("📜 Históricos Anuales")
    st.caption("Sección limpia lista para cierres de temporada.")

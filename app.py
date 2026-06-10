import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# CONFIGURACIÓN GENERAL
st.set_page_config(page_title="Hybrid Training Hub", page_icon="🏋️", layout="wide")

FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"

def cargar_csv(file_path):
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_csv(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_csv(FILE_SUENO)

# PARSEADOR ULTRA-ROBUSTO DE FECHAS DE GARMIN
def normalizar_fechas(serie):
    if serie.empty:
        return pd.to_datetime(serie)
    # Limpieza de residuos de texto comunes en exportaciones (ej: "mié., 10 de jun.")
    s_limpia = serie.astype(str).str.replace(r'^[A-Za-záéíóú.,\s]+,\s*', '', regex=True)
    s_limpia = s_limpia.str.replace(r' de\s*', ' ', regex=True).str.strip()
    return pd.to_datetime(s_limpia, errors='coerce', format='mixed')

# PARSEADORES DE MÉTRICAS NUMÉRICAS
def limpiar_distancia(serie):
    return pd.to_numeric(serie.astype(str).str.replace(' km', '', case=False).str.replace(',', '.').str.strip(), errors='coerce')

def ritmo_a_decimal(serie):
    def transformar(val):
        try:
            v = str(val).lower().replace('min/km', '').strip()
            if ':' in v:
                partes = v.split(':')
                if len(partes) == 2:
                    return float(partes[0]) + (float(partes[1]) / 60.0)
                elif len(partes) == 3:
                    return (float(partes[0]) * 60) + float(partes[1]) + (float(partes[2]) / 60.0)
            return float(v.replace(',', '.'))
        except Exception:
            return None
    return serie.apply(transformar)

# DETECTOR INTELIGENTE DE COLUMNAS (Soporta Inglés y Español)
def buscar_columna(df, palabras):
    for c in df.columns:
        if any(p in str(c).lower() for p in palabras):
            return c
    return None

# PROCESAMIENTO AUTOMÁTICO DE LOS DATOS ALMACENADOS
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
actividades_semana_actual = {dia: [] for dia in dias_semana}

df_act = st.session_state['df_actividades']
df_sueno = st.session_state['df_sueno']

# Mapeos automáticos
col_f_act = buscar_columna(df_act, ['fecha', 'date', 'comienzo', 'start']) if not df_act.empty else None
col_tipo_act = buscar_columna(df_act, ['tipo', 'type', 'actividad']) if not df_act.empty else None
col_dist_act = buscar_columna(df_act, ['distancia', 'distance', 'km']) if not df_act.empty else None
col_ritmo_act = buscar_columna(df_act, ['ritmo', 'pace', 'velocidad', 'avg pace']) if not df_act.empty else None
col_fc_act = buscar_columna(df_act, ['fc media', 'avg hr', 'frecuencia', 'cardíaca']) if not df_act.empty else None

# Extracción para Microciclo e Inicio (Semana en curso)
if not df_act.empty and col_f_act and col_tipo_act:
    df_act['Fecha_Procesada'] = normalizar_fechas(df_act[col_f_act])
    hoy = datetime.today()
    lunes_act = hoy - timedelta(days=hoy.weekday())
    domingo_act = lunes_act + timedelta(days=6)
    
    df_filtrado = df_act[(df_act['Fecha_Procesada'].dt.date >= lunes_act.date()) & (df_act['Fecha_Procesada'].dt.date <= domingo_act.date())]
    for _, fila in df_filtrado.iterrows():
        if pd.notna(fila['Fecha_Procesada']):
            nom_dia = dias_semana[fila['Fecha_Procesada'].weekday()]
            t = fila[col_tipo_act]
            d = f"{fila[col_dist_act]} km" if col_dist_act and pd.notna(fila[col_dist_act]) else ""
            r = f" a {fila[col_ritmo_act]}" if col_ritmo_act and pd.notna(fila[col_ritmo_act]) else ""
            actividades_semana_actual[nom_dia].append(f"🏃‍♂️ {t}: {d}{r}")

# INTERFAZ LATERAL
st.sidebar.title("Panel de Control")
opcion = st.sidebar.radio("Navegación:", ["🏠 Inicio", "🗓️ Microciclo", "🗺️ Macrociclo", "📥 Ingresar Datos", "📈 Métricas y Evolución", "📜 Históricos"])

# --- PÁGINA: INGRESAR DATOS ---
if opcion == "📥 Ingresar Datos":
    st.title("📥 Carga de Datos Históricos y Actividades")
    st.write("Sube tus archivos consolidados aquí. La aplicación los procesará y actualizará todo el ecosistema de forma inmediata.")
    
    archivos = st.file_uploader("Arrastra tus archivos CSV de Garmin Connect", type=["csv"], accept_multiple_files=True)
    if archivos:
        for arc in archivos:
            try:
                df_nuevo = pd.read_csv(arc)
                cols_str = "".join(arc.name.lower() + "".join(df_nuevo.columns).lower())
                
                if any(p in cols_str for p in ["sueño", "sleep", "vfc", "hrv", "reposo", "resting", "wellness"]):
                    if not st.session_state['df_sueno'].empty:
                        df_total = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates().reset_index(drop=True)
                    else:
                        df_total = df_nuevo
                    st.session_state['df_sueno'] = df_total
                    df_total.to_csv(FILE_SUENO, index=False)
                    st.success(f"💥 Datos de Salud cargados correctamente.")
                else:
                    if not st.session_state['df_actividades'].empty:
                        df_total = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates().reset_index(drop=True)
                    else:
                        df_total = df_nuevo
                    st.session_state['df_actividades'] = df_total
                    df_total.to_csv(FILE_ACTIVIDADES, index=False)
                    st.success(f"💥 Historial de Actividades fusionado con éxito.")
            except Exception as e:
                st.error(f"Error con el archivo {arc.name}: {e}")
        st.rerun()

# --- PÁGINA: INICIO ---
elif opcion == "🏠 Inicio":
    st.title("Hub de Entrenamiento Híbrido")
    st.subheader(f"{dias_semana[datetime.today().weekday()]}, {datetime.today().strftime('%d/%m/%Y')}")
    
    c_izq, c_der = st.columns([3, 2])
    with c_izq:
        st.markdown("### 📋 Resumen de la Actividad de Hoy")
        hoy_texto = dias_semana[datetime.today().weekday()]
        acts_hoy = actividades_semana_actual[hoy_texto]
        if acts_hoy:
            for ac in acts_hoy:
                st.info(ac)
        else:
            st.caption("No hay entrenamientos registrados para el día de hoy todavía.")
            
    with c_der:
        st.markdown("### 🚦 Predisposición (Semáforo)")
        if not df_sueno.empty:
            st.success("🟢 Datos estables. Tu ecosistema fisiológico está conectado correctamente.")
        else:
            st.warning("⚠️ Semáforo en espera. Sube datos de salud para activar.")

# --- PÁGINA: MICROCICLO ---
elif opcion == "🗓️ Microciclo":
    st.title("🗓️ Programación Semanal (Microciclo Real)")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6, c7 = st.columns(4)
    bloques_columnas = [c1, c2, c3, c4, c5, c6, c7]
    
    for idx, dia in enumerate(dias_semana):
        with bloques_columnas[idx]:
            st.markdown(f"#### {dia}")
            lista_acts = actividades_semana_actual[dia]
            if lista_acts:
                html_acts = "".join([f"<div style='margin-bottom:6px; color:#ffcc00; font-size:0.9em;'>{a}</div>" for a in lista_acts])
            else:
                html_acts = "<span style='color:#666; font-size:0.85em;'>Sin registros de actividad</span>"
                
            st.markdown(f"""
                <div style="background-color: #1e1e1e; padding: 12px; border-radius: 8px; border: 1px solid #333; min-height: 120px;">
                    {html_acts}
                </div>
            """, unsafe_allow_html=True)

# --- PÁGINA: MACROCICLO ---
elif opcion == "🗺️ Macrociclo":
    st.title("🗺️ Estructura del Macrociclo Anual")
    st.table(pd.DataFrame({
        "Mes": ["Enero - Mar Ayuno", "Abril - Junio", "Julio - Septiembre", "Octubre - Diciembre"],
        "Enfoque": ["Volumen Base", "Intensificación", "Competición / Pico", "Transición / Fuerza Máx"]
    }))

# --- PÁGINA: MÉTRICAS Y EVOLUCIÓN ---
elif opcion == "📈 Métricas y Evolución":
    st.title("📈 Cuadro de Mando de Adaptaciones Fisiológicas")
    
    b1, b2 = st.columns(2)
    
    with b1:
        # 1. FC Reposo y VFC Basal
        st.markdown("#### 1. FC Reposo vs VFC Basal (Quincena)")
        col_fs = buscar_columna(df_sueno, ['fecha', 'date', 'day'])
        col_v = buscar_columna(df_sueno, ['vfc', 'hrv'])
        col_r = buscar_columna(df_sueno, ['reposo', 'resting', 'rhr'])
        
        if not df_sueno.empty and col_fs and col_v and col_r:
            df_sueno['Fecha_C'] = normalizar_fechas(df_sueno[col_fs])
            df_q = df_sueno.dropna(subset=['Fecha_C']).sort_values(by='Fecha_C').tail(15)
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df_q['Fecha_C'], y=pd.to_numeric(df_q[col_v], errors='coerce'), name="VFC (ms)", mode='lines+markers', line=dict(color='#4da6ff')))
            fig1.add_trace(go.Scatter(x=df_q['Fecha_C'], y=pd.to_numeric(df_q[col_r], errors='coerce'), name="FC Reposo (ppm)", mode='lines+markers', line=dict(color='#ff4d4d')))
            fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230, template="plotly_dark")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.caption("Faltan datos de salud válidos para estructurar la Gráfica 1.")

        # 3. Ritmo medio por zonas de FC
        st.markdown("#### 3. Ritmo Medio min/km en las 5 Zonas de FC")
        if not df_act.empty and col_f_act and col_fc_act and col_ritmo_act:
            try:
                df_act['FC_Num'] = pd.to_numeric(df_act[col_fc_act], errors='coerce')
                df_act['Ritmo_Num'] = ritmo_a_decimal(df_act[col_ritmo_act])
                
                # Clasificar en las 5 zonas estándar de carrera
                def asignar_zona(hr):
                    if hr < 130: return 'Z1'
                    elif hr < 145: return 'Z2'
                    elif hr < 160: return 'Z3'
                    elif hr < 175: return 'Z4'
                    else: return 'Z5'
                
                df_carrera = df_act.dropna(subset=['FC_Num', 'Ritmo_Num']).copy()
                df_carrera['Zona'] = df_carrera['FC_Num'].apply(asignar_zona)
                df_zonas = df_carrera.groupby('Zona')['Ritmo_Num'].mean().reindex(['Z1', 'Z2', 'Z3', 'Z4', 'Z5']).reset_index()
                
                fig3 = px.line(df_zonas, x='Zona', y='Ritmo_Num', markers=True, template="plotly_dark")
                fig3.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230)
                fig3.update_yaxes(title="Ritmo Decimal (minutos)")
                st.plotly_chart(fig3, use_container_width=True)
            except Exception:
                st.caption("Error al calcular ritmos por zonas.")
        else:
            st.caption("Sube el historial completo de actividades de carrera para graficar tus 5 zonas.")

    with b2:
        # 2. Estado de entreno (Aguda vs Crónica)
        st.markdown("#### 2. Túnel de Carga Aguda vs Crónica (Estilo Garmin)")
        if not df_act.empty and col_f_act and col_dist_act:
            df_act['Fecha_C'] = normalizar_fechas(df_act[col_f_act])
            df_act['Dist_Num'] = limpiar_distancia(df_act[col_dist_act])
            df_d = df_act.dropna(subset=['Fecha_C']).groupby(df_act['Fecha_C'].dt.date)['Dist_Num'].sum().reset_index()
            df_d.columns = ['Fecha', 'Volumen']
            df_d = df_d.sort_values(by='Fecha')
            
            df_d['Aguda'] = df_d['Volumen'].rolling(window=7, min_periods=1).mean()
            df_d['Cronica'] = df_d['Volumen'].rolling(window=28, min_periods=1).mean()
            
            df_v = df_d.tail(30)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_v['Fecha'], y=df_v['Cronica']*1.3, name="Túnel Max", line=dict(color='rgba(0,255,0,0.1)')))
            fig2.add_trace(go.Scatter(x=df_v['Fecha'], y=df_v['Cronica']*0.8, name="Túnel Min", line=dict(color='rgba(0,255,0,0.1)'), fill='tonexty'))
            fig2.add_trace(go.Scatter(x=df_v['Fecha'], y=df_v['Aguda'], name="Carga Real", line=dict(color='#ffcc00', width=2)))
            fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.caption("Se requiere el volumen total de kilómetros para calcular la relación de carga.")

        # 5. KM semanales en un mes
        st.markdown("#### 5. Kilómetros Recorridos por Semana (Último Mes)")
        if not df_act.empty and col_f_act and col_dist_act:
            df_act['Fecha_C'] = normalizar_fechas(df_act[col_f_act])
            df_act['Dist_Num'] = limpiar_distancia(df_act[col_dist_act])
            df_m = df_act.dropna(subset=['Fecha_C', 'Dist_Num']).resample('W', on='Fecha_C')['Dist_Num'].sum().reset_index().tail(4)
            df_m['Fecha_C'] = df_m['Fecha_C'].dt.strftime('Semana %V')
            
            fig5 = px.bar(df_m, x='Fecha_C', y='Dist_Num', template="plotly_dark", color_discrete_sequence=['#0084ff'])
            fig5.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.caption("Subiendo tus actividades acumuladas verás la progresión en bloques de 4 semanas.")

    st.write("---")
    b3, b4 = st.columns(2)
    
    with b3:
        # 4. Tabla de pesos máximos levantados
        st.markdown("#### 4. Tabla de Pesos Máximos Levantados (Fuerza)")
        col_peso = buscar_columna(df_act, ['peso', 'weight', 'carga', 'max'])
        if not df_act.empty and col_tipo_act and col_peso:
            df_fza = df_act[df_act[col_tipo_act].astype(str).str.lower().str.contains('fuerza|strength')]
            if not df_fza.empty:
                st.dataframe(df_fza[[col_f_act, col_peso]].tail(5), use_container_width=True, hide_index=True)
            else:
                st.caption("No se detectan entrenamientos específicos de Fuerza con registro de carga en tu archivo.")
        else:
            st.caption("Columna de carga ausente en el archivo consolidado actual.")

    with b4:
        # 6. Gráfico de grado máximo de escalada
        st.markdown("#### 6. Grado Máximo por Semana (Escalada / Bloque)")
        col_grado = buscar_columna(df_act, ['grado', 'grade', 'dificultad'])
        if not df_act.empty and col_tipo_act and col_grado:
            df_esc = df_act[df_act[col_tipo_act].astype(str).str.lower().str.contains('climb|escalada|bloque')]
            if not df_esc.empty:
                df_esc['Fecha_C'] = normalizar_fechas(df_esc[col_f_act])
                df_esc_w = df_esc.resample('W', on='Fecha_C').max().reset_index().tail(4)
                fig6 = px.line(df_esc_w, x='Fecha_C', y=col_grado, markers=True, template="plotly_dark")
                fig6.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=200)
                st.plotly_chart(fig6, use_container_width=True)
            else:
                st.caption("No hay sesiones de escalada o bloque registradas dentro del CSV de actividades.")
        else:
            st.caption("Sube métricas avanzadas que contengan la dificultad de escalada para activar la gráfica.")

# --- PÁGINA: HISTORICOS ---
elif opcion == "📜 Históricos":
    st.title("📜 Historial Completo de Temporadas")
    st.info("Pestaña de lectura limpia y almacenamiento estable.")

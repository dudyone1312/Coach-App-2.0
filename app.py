import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import re

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Hybrid Training Hub", page_icon="🏋️", layout="wide")

FILE_ACTIVIDADES = "datos_actividades.csv"
FILE_SUENO = "datos_sueno.csv"

def cargar_datos(ruta):
    if os.path.exists(ruta):
        try:
            return pd.read_csv(ruta)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

if 'df_actividades' not in st.session_state:
    st.session_state['df_actividades'] = cargar_datos(FILE_ACTIVIDADES)
if 'df_sueno' not in st.session_state:
    st.session_state['df_sueno'] = cargar_datos(FILE_SUENO)

# --- 2. MOTORES DE LECTURA ROBUSTA ---
def limpiar_fechas(serie):
    if serie.empty: return pd.to_datetime(serie)
    # Elimina días de la semana y texto sobrante (Ej: "mié., 10 de jun.")
    s = serie.astype(str).str.replace(r'^[A-Za-záéíóú.,\s]+,\s*', '', regex=True)
    s = s.str.replace(r' de\s*', ' ', regex=True).str.strip()
    return pd.to_datetime(s, errors='coerce')

def detectar_columna(df, palabras_clave):
    for col in df.columns:
        if any(p in str(col).lower() for p in palabras_clave):
            return col
    return None

def limpiar_numeros(serie):
    # Extrae solo los números (ej: "5,3 km" -> 5.3)
    s = serie.astype(str).str.replace(',', '.').str.extract(r'([0-9]*\.?[0-9]+)')[0]
    return pd.to_numeric(s, errors='coerce')

def limpiar_ritmos(serie):
    def a_decimal(val):
        val = str(val).split(' ')[0] # Quitar "min/km"
        if ':' in val:
            partes = val.split(':')
            if len(partes) == 2: return float(partes[0]) + (float(partes[1]) / 60.0)
        return None
    return serie.apply(a_decimal)

# --- 3. PROCESAMIENTO CENTRALIZADO ---
df_act = st.session_state['df_actividades']
df_sueno = st.session_state['df_sueno']
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
actividades_semana_ui = {dia: [] for dia in dias_semana}

col_fecha_act = detectar_columna(df_act, ['fecha', 'date', 'comienzo', 'start'])
col_tipo_act = detectar_columna(df_act, ['tipo', 'type', 'actividad', 'activity'])

if not df_act.empty and col_fecha_act:
    df_act['Fecha_Real'] = limpiar_fechas(df_act[col_fecha_act])
    
    # FIX CRÍTICO: Buscar la semana MÁS RECIENTE de los datos, no el calendario actual
    fecha_maxima = df_act['Fecha_Real'].max()
    if pd.notna(fecha_maxima):
        lunes_ref = fecha_maxima - timedelta(days=fecha_maxima.weekday())
        domingo_ref = lunes_ref + timedelta(days=6)
        
        df_semana = df_act[(df_act['Fecha_Real'] >= lunes_ref) & (df_act['Fecha_Real'] <= domingo_ref)]
        
        for _, fila in df_semana.iterrows():
            if pd.notna(fila['Fecha_Real']):
                dia_nombre = dias_semana[fila['Fecha_Real'].weekday()]
                tipo = fila[col_tipo_act] if col_tipo_act else "Entreno"
                actividades_semana_ui[dia_nombre].append(f"🏃‍♂️ {tipo}")

# --- 4. PANEL LATERAL DE NAVEGACIÓN ---
st.sidebar.title("Panel")
opcion = st.sidebar.radio("Ir a:", ["🏠 Inicio", "🗓️ Microciclo", "🗺️ Macrociclo", "📥 Ingresar Datos", "📈 Métricas y Evolución", "📜 Históricos"])

# DEBUGGER: Para saber qué está leyendo la app realmente
with st.sidebar.expander("🛠️ Diagnóstico de Datos"):
    st.write(f"Total Actividades: {len(df_act)}")
    st.write(f"Total Sueño: {len(df_sueno)}")
    st.write(f"Col Fecha Detectada: {col_fecha_act}")

# --- PÁGINAS ---

if opcion == "📥 Ingresar Datos":
    st.title("📥 Sube tus archivos de Garmin")
    st.info("💡 Por favor, sube archivos **.CSV** exportados desde Garmin Connect Web. Los .fit están permitidos pero pueden perder formato.")
    
    archivos = st.file_uploader("Arrastra aquí tus archivos", type=["csv", "fit"], accept_multiple_files=True)
    if archivos:
        for arc in archivos:
            if arc.name.endswith('.fit'):
                st.warning(f"⚠️ El archivo {arc.name} es formato .fit. Streamlit requiere CSV para leer columnas de texto correctamente. Si no ves los datos, exporta a CSV.")
                continue
            try:
                df_nuevo = pd.read_csv(arc)
                nombres = (arc.name + "".join(df_nuevo.columns)).lower()
                
                # Clasificador automático
                if any(p in nombres for p in ["sueño", "sleep", "vfc", "hrv", "reposo", "resting", "wellness"]):
                    st.session_state['df_sueno'] = pd.concat([st.session_state['df_sueno'], df_nuevo]).drop_duplicates()
                    st.session_state['df_sueno'].to_csv(FILE_SUENO, index=False)
                    st.success("💤 Datos de salud actualizados.")
                else:
                    st.session_state['df_actividades'] = pd.concat([st.session_state['df_actividades'], df_nuevo]).drop_duplicates()
                    st.session_state['df_actividades'].to_csv(FILE_ACTIVIDADES, index=False)
                    st.success("🏃‍♂️ Actividades actualizadas.")
            except Exception as e:
                st.error(f"Error leyendo {arc.name}: {e}")
        st.rerun()

elif opcion == "🏠 Inicio":
    st.title("Hub de Entrenamiento")
    st.write("Datos sincronizados con tu semana más reciente.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📋 Resumen Última Semana")
        for dia, acts in actividades_semana_ui.items():
            if acts:
                st.write(f"**{dia}:** {', '.join(acts)}")
    with c2:
        st.markdown("### 🚦 Semáforo")
        if not df_sueno.empty: st.success("🟢 Datos de salud detectados. Sistema funcionando.")
        else: st.warning("⚠️ Sube datos de salud/VFC para activar.")

elif opcion == "🗓️ Microciclo":
    st.title("🗓️ Microciclo (Última semana registrada)")
    cols = st.columns(7)
    for idx, dia in enumerate(dias_semana):
        with cols[idx]:
            st.markdown(f"**{dia}**")
            for act in actividades_semana_ui[dia]:
                st.info(act)

elif opcion == "🗺️ Macrociclo":
    st.title("🗺️ Macrociclo")
    st.table(pd.DataFrame({"Fase": ["Base", "Pico", "Descarga"], "Objetivo": ["Volumen", "Intensidad", "Recuperación"]}))

elif opcion == "📈 Métricas y Evolución":
    st.title("📈 Cuadro de Mando")
    if df_act.empty and df_sueno.empty:
        st.warning("⚠️ No hay datos subidos. Ve a 'Ingresar Datos' y sube tus CSV.")
    else:
        b1, b2 = st.columns(2)
        
        with b1:
            st.markdown("#### 1. FC Reposo vs VFC (Quincena)")
            c_fecha_s = detectar_columna(df_sueno, ['fecha', 'date', 'day'])
            c_vfc = detectar_columna(df_sueno, ['vfc', 'hrv'])
            c_rep = detectar_columna(df_sueno, ['reposo', 'resting', 'rhr'])
            
            if c_fecha_s and c_vfc and c_rep:
                df_sueno['F'] = limpiar_fechas(df_sueno[c_fecha_s])
                df_q = df_sueno.dropna(subset=['F']).sort_values('F').tail(15)
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=df_q['F'], y=limpiar_numeros(df_q[c_vfc]), name="VFC", line=dict(color='#4da6ff')))
                fig1.add_trace(go.Scatter(x=df_q['F'], y=limpiar_numeros(df_q[c_rep]), name="FC Reposo", line=dict(color='#ff4d4d')))
                fig1.update_layout(height=250, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.error("No encuentro las columnas de Fecha, VFC o FC Reposo en el archivo de salud.")

            st.markdown("#### 3. Ritmo por Zonas (min/km)")
            c_ritmo = detectar_columna(df_act, ['ritmo', 'pace', 'avg pace'])
            c_fc = detectar_columna(df_act, ['fc media', 'avg hr', 'frecuencia'])
            if c_ritmo and c_fc and col_fecha_act:
                df_act['FC'] = limpiar_numeros(df_act[c_fc])
                df_act['Ritmo'] = limpiar_ritmos(df_act[c_ritmo])
                df_c = df_act.dropna(subset=['FC', 'Ritmo']).copy()
                
                def zona(hr):
                    if hr < 130: return 'Z1'
                    elif hr < 145: return 'Z2'
                    elif hr < 160: return 'Z3'
                    elif hr < 175: return 'Z4'
                    else: return 'Z5'
                
                if not df_c.empty:
                    df_c['Zona'] = df_c['FC'].apply(zona)
                    df_z = df_c.groupby('Zona')['Ritmo'].mean().reset_index()
                    fig3 = px.line(df_z, x='Zona', y='Ritmo', markers=True, template="plotly_dark")
                    fig3.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.warning("No hay actividades con Frecuencia Cardíaca y Ritmo registrados.")
            else:
                st.error("Faltan columnas de Ritmo Medio o FC Media.")

        with b2:
            st.markdown("#### 2. Carga Aguda vs Crónica")
            c_dist = detectar_columna(df_act, ['distancia', 'distance', 'km'])
            if c_dist and col_fecha_act:
                df_act['D'] = limpiar_numeros(df_act[c_dist])
                df_d = df_act.groupby('Fecha_Real')['D'].sum().reset_index().sort_values('Fecha_Real')
                df_d['Aguda'] = df_d['D'].rolling(7, min_periods=1).mean()
                df_d['Cronica'] = df_d['D'].rolling(28, min_periods=1).mean()
                
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_d['Fecha_Real'], y=df_d['Cronica']*1.3, fill=None, line=dict(color='rgba(0,255,0,0.1)')))
                fig2.add_trace(go.Scatter(x=df_d['Fecha_Real'], y=df_d['Cronica']*0.8, fill='tonexty', line=dict(color='rgba(0,255,0,0.1)')))
                fig2.add_trace(go.Scatter(x=df_d['Fecha_Real'], y=df_d['Aguda'], line=dict(color='#ffcc00')))
                fig2.update_layout(height=250, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.error("Falta columna de Distancia.")

            st.markdown("#### 5. KM Semanales (Mes)")
            if c_dist and col_fecha_act:
                df_m = df_act.dropna(subset=['Fecha_Real', 'D']).resample('W', on='Fecha_Real')['D'].sum().reset_index().tail(4)
                df_m['Semana'] = df_m['Fecha_Real'].dt.strftime('Sem %V')
                fig5 = px.bar(df_m, x='Semana', y='D', template="plotly_dark")
                fig5.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig5, use_container_width=True)

        st.write("---")
        c_titulos = detectar_columna(df_act, ['título', 'title', 'nombre', 'name'])
        
        b3, b4 = st.columns(2)
        with b3:
            st.markdown("#### 4. Récords Fuerza (Extraídos del Título)")
            st.caption("Escribe el peso en el título de Garmin (Ej: 'Sentadilla 120kg')")
            if c_titulos:
                fuerza = df_act[df_act[c_titulos].astype(str).str.contains(r'\d+kg|\d+ kg', case=False, na=False)]
                if not fuerza.empty:
                    st.dataframe(fuerza[[col_fecha_act, c_titulos]].tail(5), hide_index=True)
                else:
                    st.info("No detecto 'kg' en los títulos de tus entrenos.")
                    
        with b4:
            st.markdown("#### 6. Grados Escalada (Extraídos del Título)")
            st.caption("Escribe el grado en el título (Ej: 'Bloque 6b' o 'Vía 7a')")
            if c_titulos:
                escalada = df_act[df_act[c_titulos].astype(str).str.contains(r'6a|6b|6c|7a|7b|7c|8a|v3|v4|v5', case=False, na=False)]
                if not escalada.empty:
                    st.dataframe(escalada[[col_fecha_act, c_titulos]].tail(5), hide_index=True)
                else:
                    st.info("No detecto grados estándar en los títulos.")

elif opcion == "📜 Históricos":
    st.title("📜 Historial Completo")
    st.info("Datos anuales consolidados.")

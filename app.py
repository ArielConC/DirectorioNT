import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
import pytesseract
from PIL import Image, ImageOps # <-- NUEVO: Importamos ImageOps para corregir celulares
import re
from fpdf import FPDF
from pillow_heif import register_heif_opener

# Habilitar soporte para formatos HEIC de iPhone
register_heif_opener()

# ==========================================
# 1. CONFIGURACIÓN SUPABASE Y TESSERACT
# ==========================================
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

import os # <-- Asegúrate de tener esta importación hasta arriba

# Si el sistema operativo es Windows (tu PC local), usa la ruta fija.
# Si está en la nube (Linux), se configurará de forma automática.
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
st.set_page_config(page_title="Directorio Corporativo", page_icon="📇", layout="wide")

# ==========================================
# 2. FUNCIONES BASE Y PDF
# ==========================================
def verificar_login(usuario, password):
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    res = supabase.table('usuarios').select('rol, puesto').eq('usuario', usuario).eq('password', pwd_hash).execute()
    if len(res.data) > 0:
        return res.data[0]['rol'], res.data[0]['puesto']
    return None

def generar_pdf(dataframe):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Directorio Corporativo", ln=True, align="C")
    pdf.ln(5)
    
    # Contenido
    pdf.set_font("Arial", "", 12)
    for index, fila in dataframe.iterrows():
        nombre = fila.get('nombre_completo', 'Sin nombre')
        puesto = fila.get('puesto', '')
        correo = fila.get('correo', 'Sin correo')
        tel = fila.get('telefono', 'Sin telefono')
        
        texto_linea1 = f"{nombre} - {puesto}" if puesto else nombre
        texto_linea2 = f"Correo: {correo} | Tel: {tel}"
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, texto_linea1.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 6, texto_linea2.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.ln(3) 
        
    return pdf.output(dest='S').encode('latin-1')

if 'autenticado' not in st.session_state:
    st.session_state.update({'autenticado': False, 'usuario': '', 'rol': '', 'puesto': ''})

# ==========================================
# 3. PANTALLA DE LOGIN
# ==========================================
if not st.session_state['autenticado']:
    st.title("🔒 Acceso al Directorio Digital NT Tools de México")
    with st.form("login_form"):
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar")
        
        if submit:
            datos_usuario = verificar_login(user, pwd)
            if datos_usuario:
                st.session_state.update({
                    'autenticado': True, 'usuario': user, 'rol': datos_usuario[0], 'puesto': datos_usuario[1]
                })
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# ==========================================
# 4. APLICACIÓN PRINCIPAL
# ==========================================
else:
    with st.sidebar:
        st.write(f"👤 **{st.session_state['usuario']}**")
        st.write(f"💼 {st.session_state['puesto']}")
        st.divider()
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.update({'autenticado': False, 'usuario': '', 'rol': '', 'puesto': ''})
            st.rerun()

    if st.session_state['rol'] == 'Admin':
        tabs = st.tabs(["📇 Directorio", "📸 Escanear Tarjeta", "⚙️ Panel Admin"])
    else:
        tabs = st.tabs(["📇 Directorio", "📸 Escanear Tarjeta"])

    # --- PESTAÑA 1: DIRECTORIO, EDICIÓN Y PDF ---
    with tabs[0]:
        st.header("Buscador de Contactos")
        col_busq, col_filt, col_btn = st.columns([2, 1, 1])
        
        with col_busq:
            busqueda = st.text_input("🔍 Buscar por nombre o correo...")
        with col_filt:
            tipo_filtro = st.selectbox("🌍 Ubicación", ["Todos", "Nacional", "Internacional"])
        
        # Descarga de catálogos
        res_emp = supabase.table('empresas').select('*').execute()
        df_emp = pd.DataFrame(res_emp.data) if len(res_emp.data) > 0 else pd.DataFrame()
        lista_empresas = ["Sin asignar"] + (df_emp['nombre'].tolist() if not df_emp.empty else [])
        
        res_ubi = supabase.table('ubicaciones').select('*').execute()
        df_ubi = pd.DataFrame(res_ubi.data) if len(res_ubi.data) > 0 else pd.DataFrame()
        if not df_ubi.empty:
            df_ubi['etiqueta'] = df_ubi['estado'] + ", " + df_ubi['pais']
        lista_ubicaciones = ["Sin asignar"] + (df_ubi['etiqueta'].tolist() if not df_ubi.empty else [])

        # Descarga de contactos
        res_contactos = supabase.table('contactos').select('*').execute()
        df = pd.DataFrame(res_contactos.data) if len(res_contactos.data) > 0 else pd.DataFrame()
        
        if not df.empty:
            df['nombre_empresa'] = "Empresa sin asignar"
            df['nombre_ubicacion'] = "Sin ubicación"
            df['tipo_ubicacion'] = ""
            
            for idx, row in df.iterrows():
                if pd.notna(row['id_empresa']) and not df_emp.empty:
                    m_emp = df_emp[df_emp['id_empresa'] == row['id_empresa']]
                    if not m_emp.empty:
                        df.at[idx, 'nombre_empresa'] = m_emp['nombre'].values[0]
                if pd.notna(row['id_ubicacion']) and not df_ubi.empty:
                    m_ubi = df_ubi[df_ubi['id_ubicacion'] == row['id_ubicacion']]
                    if not m_ubi.empty:
                        df.at[idx, 'nombre_ubicacion'] = m_ubi['etiqueta'].values[0]
                        df.at[idx, 'tipo_ubicacion'] = m_ubi['tipo'].values[0]

            if tipo_filtro != "Todos":
                df = df[df['tipo_ubicacion'] == tipo_filtro]
            if busqueda:
                df = df[df['nombre_completo'].str.contains(busqueda, case=False, na=False) | 
                        df['correo'].str.contains(busqueda, case=False, na=False) |
                        df['nombre_empresa'].str.contains(busqueda, case=False, na=False)]

        with col_btn:
            st.write("") 
            st.write("")
            if not df.empty:
                pdf_bytes = generar_pdf(df)
                st.download_button(label="📄 Exportar a PDF", data=pdf_bytes, file_name="Directorio_Colaboradores.pdf", mime="application/pdf", type="primary")

        if not df.empty:
            for index, fila in df.iterrows():
                puesto_v = fila.get('puesto', '')
                emp_v = fila.get('nombre_empresa', 'Empresa sin asignar')
                puesto_str = f" - {puesto_v}" if puesto_v else ""
                
                with st.expander(f"👤 {fila['nombre_completo']}{puesto_str} | 🏢 {emp_v}"):
                    colA, colB = st.columns(2)
                    colA.write(f"**📞 Teléfono 1:** {fila.get('telefono', 'N/A')}")
                    if 'telefono_2' in fila and pd.notna(fila['telefono_2']) and fila['telefono_2'] != "":
                        colA.write(f"**📱 Teléfono 2:** {fila['telefono_2']}")
                    colA.write(f"**✉️ Correo:** {fila.get('correo', 'N/A')}")
                    colA.write(f"**📍 Ubicación:** {fila.get('nombre_ubicacion', 'Sin ubicación')}")
                    
                    with colB:
                        editar_toggle = st.checkbox("✏️ Editar información", key=f"toggle_{fila['id_contacto']}")
                        if st.session_state['rol'] == 'Admin':
                            if st.button("🗑️ Borrar", key=f"del_{fila['id_contacto']}", type="primary"):
                                supabase.table('contactos').delete().eq('id_contacto', fila['id_contacto']).execute()
                                st.rerun()

                    if editar_toggle:
                        st.markdown("---")
                        with st.form(key=f"form_edit_{fila['id_contacto']}"):
                            st.caption("Modifica las propiedades del registro:")
                            v_nombre = st.text_input("Nombre Completo", value=fila['nombre_completo'])
                            v_puesto = st.text_input("Puesto", value=fila['puesto'] if pd.notna(fila['puesto']) else "")
                            v_correo = st.text_input("Correo", value=fila['correo'] if pd.notna(fila['correo']) else "")
                            
                            c_tel1, c_tel2 = st.columns(2)
                            with c_tel1:
                                v_tel1 = st.text_input("Teléfono Principal", value=fila['telefono'] if pd.notna(fila['telefono']) else "")
                            with c_tel2:
                                v_tel2 = st.text_input("Teléfono Alternativo", value=fila['telefono_2'] if 'telefono_2' in fila and pd.notna(fila['telefono_2']) else "")
                            
                            idx_emp = lista_empresas.index(fila['nombre_empresa']) if fila['nombre_empresa'] in lista_empresas else 0
                            idx_ubi = lista_ubicaciones.index(fila['nombre_ubicacion']) if fila['nombre_ubicacion'] in lista_ubicaciones else 0
                            
                            v_empresa = st.selectbox("Empresa", options=lista_empresas, index=idx_emp)
                            v_ubicacion = st.selectbox("Ubicación", options=lista_ubicaciones, index=idx_ubi)
                            
                            if st.form_submit_button("💾 Guardar Cambios"):
                                id_emp_n = None
                                if v_empresa != "Sin asignar" and not df_emp.empty:
                                    id_emp_n = int(df_emp[df_emp['nombre'] == v_empresa]['id_empresa'].values[0])
                                id_ubi_n = None
                                if v_ubicacion != "Sin asignar" and not df_ubi.empty:
                                    id_ubi_n = int(df_ubi[df_ubi['etiqueta'] == v_ubicacion]['id_ubicacion'].values[0])
                                
                                supabase.table('contactos').update({
                                    "nombre_completo": v_nombre, "puesto": v_puesto, "correo": v_correo,
                                    "telefono": v_tel1, "telefono_2": v_tel2, "id_empresa": id_emp_n, "id_ubicacion": id_ubi_n
                                }).eq('id_contacto', fila['id_contacto']).execute()
                                st.success("Registro modificado en la nube.")
                                st.rerun()
        else:
            st.info("No hay contactos registrados.")

    # --- PESTAÑA 2: ESCANEAR TARJETA (ROTACIÓN INTELIGENTE DETECTADA) ---
    with tabs[1]:
        st.header("📸 Digitalizar Nueva Tarjeta")
        archivo_subido = st.file_uploader("Sube o arrastra la foto de la tarjeta aquí", type=['jpg', 'jpeg', 'png', 'heic', 'HEIC'])
        
        if archivo_subido is not None:
            col_img1, col_img2 = st.columns(2)
            with col_img1:
                st.image(archivo_subido, caption="Imagen Original", width=350)
            
            if st.button("Procesar Tarjeta con IA"):
                with st.spinner('Procesando activos y ejecutando filtros...'):
                    # 1. Abrir imagen
                    imagen = Image.open(archivo_subido)
                    
                    # 2. TRUCO ULTRA: Ajustar orientación nativa del sensor del celular (EXIF)
                    imagen = ImageOps.exif_transpose(imagen)
                    
                    # 3. Redimensionamiento óptimo conservando la escala corregida
                    ancho_base = 1000
                    proporcion = (ancho_base / float(imagen.size[0]))
                    alto = int((float(imagen.size[1]) * float(proporcion)))
                    imagen = imagen.resize((ancho_base, alto), Image.Resampling.LANCZOS)
                    
                    # 4. INTELIGENCIA OSD: Detectar la orientación del TEXTO dentro de la tarjeta
                    try:
                        osd = pytesseract.image_to_osd(imagen)
                        rotacion = re.search(r'Rotate: (\d+)', osd)
                        if rotacion:
                            angulo = int(rotacion.group(1))
                            if angulo != 0:
                                # Si el texto está de lado, lo rotamos para dejarlo derecho
                                imagen = imagen.rotate(360 - angulo, expand=True)
                    except Exception:
                        # Si la tarjeta tiene muy poco texto, el OSD falla. Usamos el plan de respaldo:
                        # Si la foto sigue estando vertical, la acostamos (las tarjetas suelen ser horizontales)
                        if imagen.size[1] > imagen.size[0]:
                            imagen = imagen.rotate(270, expand=True)
                    
                    # 5. Tratamiento final: Escala de grises y binarización por umbral
                    imagen = imagen.convert('L')
                    imagen = imagen.point(lambda p: 255 if p > 140 else 0, mode='1')
                    
                    with col_img2:
                        st.image(imagen, caption="Máscara Limpia (Vista OCR)", width=350)
                    
                    # 6. Extracción por OCR y expresiones regulares
                    texto = pytesseract.image_to_string(imagen, config=r'--psm 6')
                    correos = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', texto)
                    telefonos = re.findall(r'\(?\+?\d{1,3}\)?[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{4}', texto)
                    
                    correo_l = correos[0] if correos else ""
                    telefono_1 = telefonos[0] if len(telefonos) > 0 else ""
                    telefono_2 = telefonos[1] if len(telefonos) > 1 else ""
                    
                    if correo_l or telefono_1:
                        nombre_temp = correo_l.split('@')[0] if correo_l else "Nuevo Contacto"
                        
                        supabase.table('contactos').insert({
                            "nombre_completo": nombre_temp, "correo": correo_l,
                            "telefono": telefono_1, "telefono_2": telefono_2
                        }).execute()
                        st.success(f"Guardado en la nube. Correo: {correo_l} | Tel 1: {telefono_1} | Tel 2: {telefono_2}")
                        st.rerun()
                    else:
                        st.warning("No se detectaron datos legibles. Intenta tomando la foto más cerca.")

    # --- PESTAÑA 3: PANEL ADMIN ---
    if st.session_state['rol'] == 'Admin':
        with tabs[2]:
            st.header("⚙️ Panel de Administración")
            c_izq, c_der = st.columns(2)
            
            with c_izq:
                st.subheader("👥 Accesos al Sistema")
                with st.form("nuevo_usuario"):
                    n_user = st.text_input("Nombre de Usuario")
                    n_pwd = st.text_input("Contraseña", type="password")
                    n_rol = st.selectbox("Nivel de Acceso", ["Usuario", "Admin"])
                    n_puesto = st.text_input("Puesto del Colaborador")
                    if st.form_submit_button("Registrar Colaborador"):
                        pwd_hash = hashlib.sha256(n_pwd.encode()).hexdigest()
                        try:
                            supabase.table('usuarios').insert({"usuario": n_user, "password": pwd_hash, "rol": n_rol, "puesto": n_puesto}).execute()
                            st.success(f"Usuario '{n_user}' creado.")
                            st.rerun() 
                        except Exception as e:
                            st.error("Error en el registro.")
            
            with c_der:
                st.subheader("🏢 Estructura de Catálogos")
                with st.expander("➕ Agregar Empresa"):
                    with st.form("f_emp"):
                        e_nom = st.text_input("Nombre corporativo")
                        e_sec = st.text_input("Sector")
                        if st.form_submit_button("Registrar Empresa"):
                            if e_nom:
                                supabase.table('empresas').insert({"nombre": e_nom, "sector": e_sec}).execute()
                                st.success("Empresa añadida."); st.rerun()
                
                with st.expander("➕ Agregar Ubicación"):
                    with st.form("f_ubi"):
                        u_tipo = st.selectbox("Tipo", ["Nacional", "Internacional"])
                        u_pais = st.text_input("País")
                        u_est = st.text_input("Estado / Región")
                        if st.form_submit_button("Registrar Ubicación"):
                            if u_pais and u_est:
                                supabase.table('ubicaciones').insert({"tipo": u_tipo, "pais": u_pais, "estado": u_est}).execute()
                                st.success("Ubicación añadida."); st.rerun()
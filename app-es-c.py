import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
import boto3
import re
import io
import time
import base64
import requests
from PIL import Image

# Pull your Apps Script URL from Streamlit Secrets
#SCRIPT_URL = st.secrets.get("gcp_service_account", {}).get("bucket_name")
SCRIPT_URL = st.secrets.get("GSCRIPT_URL")

def upload_to_drive(uploaded_file, original_filename):
    """Sends compressed image or raw PDF to Google Apps Script using its original filename"""
    if not SCRIPT_URL:
        st.error("Configura el URL del script en los Secrets para guardar documentos.")
        return None 
    try:
        uploaded_file.seek(0)
        
        # Determine file type by checking the extension
        is_pdf = original_filename.lower().endswith('.pdf')
        
        if is_pdf:
            # For PDFs, skip compression and grab the raw bytes directly
            file_bytes = uploaded_file.getvalue()
        else:
            # --- COMPRESIÓN DE IMAGEN (SÓLO PARA JPG/PNG) ---
            img = Image.open(uploaded_file)
            
            max_size = 1024
            if img.width > max_size:
                w_percent = (max_size / float(img.width))
                h_size = int((float(img.height) * float(w_percent)))
                img = img.resize((max_size, h_size), Image.Resampling.LANCZOS)
            
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70, optimize=True)
            file_bytes = buffer.getvalue()
            # --- END COMPRESIÓN DE IMAGEN ---
        
        # Encode whichever file type we processed into Base64
        file_base64 = base64.b64encode(file_bytes).decode()
        
        payload = {
            "image": file_base64, # Keeping "image" payload key so your Apps Script doesn't have to change
            "filename": original_filename 
        }
        
        for delay in [1, 2]:
            try:
                response = requests.post(SCRIPT_URL, json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    if "error" in res_json:
                        st.error(f"Error interno de Google Apps Script: {res_json['error']}")
                        return None
                    return res_json.get("url")
                else:
                    st.error(f"Error de red de Google (Código {response.status_code}): {response.text}")
            except Exception:
                time.sleep(delay)
        return None
    except Exception as e:
        # Generic update to reflect that both formats are supported
        st.error(f"Error al procesar o comprimir el archivo (PDF/Imagen): {e}")
        return None
        
def run_ocr_processor(file_bytes, category: str) -> dict:
    """
    Processes raw file bytes directly with AWS Textract without saving to S3,
    and parses out the document entity and expiration date.
    """
    # Initialize Textract client using Streamlit Secrets
    textract_client = boto3.client(
        'textract',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_REGION"]
    )
    
    # Initialize baseline structure
    extracted_data = {
        "issuing_entity": "",
        "expiration_date": "",
        "issue_date": ""
    }
    
    try:
        # Pass the memory bytes directly to AWS
        response = textract_client.analyze_document(
            Document={'Bytes': file_bytes},
            FeatureTypes=["FORMS"]
        )
        
        # Extract lines of text from the Textract blocks
        all_lines = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                all_lines.append(block['Text'])
                
        combined_text = " ".join(all_lines)
        
        # Basic context classification heuristics
        if "health" in combined_text or "sanitation" in combined_text:
            extracted_data["issuing_entity"] = "Department of State Health Services"
        elif "fire" in combined_text or "marshal" in combined_text:
            extracted_data["issuing_entity"] = "Fire Marshal Office"
        elif "comptroller" in combined_text or "tax" in combined_text:
            extracted_data["issuing_entity"] = "State Comptroller Office"
        else:
            extracted_data["issuing_entity"] = "City Regulatory Authority"
            

        # --- 2. REGEX DATE EXTRACTION ENGINE ---
        # A more robust date pattern that captures MM/DD/YYYY, M/D/YYYY, or YYYY-MM-DD
        date_pattern = r'(\b\d{1,2}[/\-]\d{1,2}[/\-]\d{4}\b|\b\d{4}-\d{2}-\d{2}\b)'
        
        # Look for "date issue" or "issued" followed by optional spaces, optional colons, and the date
        # re.IGNORECASE makes sure "Date Issue", "DATE ISSUE", and "date issue" all match perfectly
        issue_match = re.search(
            r'(?:date\s+issue|issued|emision|fecha\s+de\s+emision)\s*[:\-]?\s*' + date_pattern, 
            combined_text, 
            re.IGNORECASE
        )
        
        # Look for expiration labels with the same high tolerance for spacing/case
        expiry_match = re.search(
            r'(?:expiration|expires|vence|vencimiento|valid\s+thru)\s*[:\-]?\s*' + date_pattern, 
            combined_text, 
            re.IGNORECASE
        )
        
        # Helper to clean and format whatever string format regex captures
        def normalize_date_string(date_str):
            if not date_str:
                return ""
            date_str = date_str.strip()
            # If it's MM/DD/YYYY or M/D/YYYY, convert it to standard database YYYY-MM-DD
            if "/" in date_str or "-" in date_str and len(date_str.split("-")[0]) != 4:
                # Replace dashes with slashes temporarily if they used MM-DD-YYYY
                normalized = date_str.replace("-", "/")
                for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y"):
                    try:
                        return datetime.strptime(normalized, fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            return date_str # Return as-is if it's already YYYY-MM-DD
            
        # Assign extracted Issue Date
        if issue_match:
            extracted_data["issue_date"] = normalize_date_string(issue_match.group(1))
        else:
            # Fallback: look for the very first standalone date in the document if the label match missed
            all_dates = re.findall(date_pattern, combined_text)
            if all_dates:
                extracted_data["issue_date"] = normalize_date_string(all_dates[0])
            else:
                extracted_data["issue_date"] = date.today().strftime('%Y-%m-%d')
            
        # Assign extracted Expiration Date
        if expiry_match:
            extracted_data["expiration_date"] = normalize_date_string(expiry_match.group(1))
        else:
            # Fallback: pick the second standalone date found in the document
            all_dates = re.findall(date_pattern, combined_text)
            if len(all_dates) >= 2:
                extracted_data["expiration_date"] = normalize_date_string(all_dates[1])
            elif len(all_dates) == 1 and not issue_match:
                extracted_data["expiration_date"] = normalize_date_string(all_dates[0])
            else:
                extracted_data["expiration_date"] = date.today().strftime('%Y-%m-%d')
                
    except Exception as aws_error:
        st.error(f"Error de procesamiento en AWS Textract: {aws_error}")
        
    return extracted_data
    
# Global Translation Dictionary
CATEGORY_TRANSLATIONS = {
    "en": {
        "tax": "Tax",
        "health": "Health & Safety",
        "fire_safety": "Fire Safety",
        "business_license": "Business License",
        "other": "Other",
        "ui": {
            "document": "Document",
            "category": "Category",
            "expiry": "Expiration Date",
            "status": "Status",
            "aprobado": "Approved",
            "vencido": "Expired",
            "faltante": "Missing",
            "repo_title": "Document Repository",
            "score": "Compliance Score",
            "registered": "Registered Documents",
            "tasks": "Pending Tasks"
        }
    },
    "es": {
        "tax": "Impuestos",
        "health": "Salud e Higiene",
        "fire_safety": "Seguridad contra Incendios",
        "business_license": "Licencia de Negocio",
        "other": "Otro",
        "ui": {
            "document": "Documento",
            "category": "Categoría",
            "expiry": "Fecha de Vencimiento",
            "status": "Estado",
            "aprobado": "Aprobado",
            "vencido": "Vencido",
            "faltante": "Faltante",
            "repo_title": "Repositorio de Documentos",
            "score": "Puntaje de Cumplimiento",
            "registered": "Documentos Registrados",
            "tasks": "Tareas Pendientes"
        }
    }
}

# Page configuration
st.set_page_config(
    page_title="Panel de Control CompliancePro",
    page_icon="🚚",
    layout="wide"
)

# Initialize Supabase Client using Streamlit Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def load_data():
    try:
        # Fetch all records from your Supabase table
        response = supabase.table("vendors").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return []

# Custom CSS for status badges
st.markdown("""
<style>
    .status-box {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to render the license guide modal
@st.dialog("📜 Guía de Licencias y Permisos", width="large")
def show_license_directory():
    st.write("Consulte las licencias comerciales comunes, sus requisitos y el desglose de costos estimados.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏥 Salud", "🚒 Bomberos", "⚖️ Legal y Regulatorio", "🧱 Zonificación y Medio Ambiente"])
    
    with tab1:
        st.subheader("🏥 Departamento de Salud")
        st.markdown("**Permiso de Establecimiento de Servicio de Alimentos**")
        st.caption("Autoriza a un negocio a preparar y servir alimentos al público. Requiere aprobar una inspección sanitaria.")
        st.info("💰 Costo Estimado: $100 – $1,000+ anuales (varía según el tamaño del negocio).")
        st.divider()
        st.markdown("**Certificación de Manipulador / Gerente de Alimentos**")
        st.caption("Garantiza que los empleados y gerentes estén debidamente capacitados en prácticas seguras de manejo de alimentos.")
        st.info("💰 Costo Estimado: $10 – $150 por empleado.")
        st.divider()
        st.markdown("**Permiso de Salud y Saneamiento**")
        st.caption("Requerido para negocios de cuidado personal (salones, barberías, spas) para asegurar los estándares de esterilización.")
        st.info("💰 Costo Estimado: $50 – $300 anuales.")

    with tab2:
        st.subheader("🚒 Departamento de Bomberos")
        st.markdown("**Permiso de Bomberos / Certificado de Ocupación**")
        st.caption("Se otorga tras la inspección del alguacil de bomberos a las salidas, extintores, rociadores y límites de capacidad del lugar.")
        st.info("💰 Costo Estimado: $50 – $200.")
        st.divider()
        st.markdown("**Permiso de Materiales Peligrosos**")
        st.caption("Requerido si su negocio almacena o maneja productos químicos inflamables, tóxicos o peligrosos.")
        st.info("💰 Costo Estimado: $100 – $500 anuales.")

    with tab3:
        st.subheader("⚖️ Legal y Regulatorio General")
        st.markdown("**Licencia Comercial General**")
        st.caption("Licencia básica emitida por su ciudad o condado que otorga el derecho a operar un negocio dentro de las jurisdicciones locales.")
        st.info("💰 Costo Estimado: $50 – $400 anuales.")
        st.divider()
        st.markdown("**Registro de Nombre Comercial (DBA - Doing Business As)**")
        st.caption("Requerido si opera bajo un nombre comercial diferente de su nombre legal o nombre personal.")
        st.info("💰 Costo Estimado: $10 – $100.")
        st.divider()
        st.markdown("**Permiso de Impuestos sobre las Ventas / Permiso de Vendedor**")
        st.caption("Le permite recaudar impuestos sobre las ventas de bienes tangibles vendidos a los consumidores en nombre del estado.")
        st.info("💰 Costo Estimado: Generalmente Gratuito (o una tarifa de registro nominal de $10 – $50).")

    with tab4:
        st.subheader("🧱 Zonificación y Medio Ambiente")
        st.markdown("**Permiso de Zonificación / Permiso de Uso de Suelo**")
        st.caption("Verifica que la actividad de su negocio cumpla con las restricciones de diseño y zonificación regionales de la localidad.")
        st.info("💰 Costo Estimado: $50 – $300.")
        st.divider()
        st.markdown("**Permiso de Letreros y Anuncios**")
        st.caption("Regula el tamaño, ubicación e iluminación de los letreros comerciales exteriores de acuerdo con los códigos estéticos de la ciudad.")
        st.info("💰 Costo Estimado: $20 – $100.")
        
    st.caption("💡 *Nota: Tarifas varían significativamente según las ordenanzas del estado, condado y ciudad.*")

# Application Logic
def main():
    # =====================================================================
    # SECCIÓN MODIFICADA: Configuración de Idioma e Interfaz
    # =====================================================================
    # 1. Inicializar el estado por defecto si no existe
    if "lang" not in st.session_state:
        st.session_state.lang = "es"
        
    # Definir una función callback interna para manejar el cambio limpiamente
    def change_language():
        if st.session_state.lang_picker == "Español":
            st.session_state.lang = "es"
        else:
            st.session_state.lang = "en"

    # 2. El selector ahora usa una llave interna y un callback para evitar bucles de refresco
    lang_choice = st.sidebar.selectbox(
        "🌐 Idioma / Language", 
        ["Español", "English"], 
        index=0 if st.session_state.lang == "es" else 1,
        key="lang_picker",
        on_change=change_language
    )

    # 3. Asignar las variables globales de traducción basándose en el cambio de arriba
    user_lang = st.session_state.lang
    ui_labels = CATEGORY_TRANSLATIONS[user_lang]["ui"]
    # =====================================================================
    
    vendors = load_data()
    
    # Sidebar Navigation
    st.sidebar.title("🚚 CompliancePro")
    
    st.sidebar.markdown("---")
    search_query = st.sidebar.text_input("Buscar Vendedor", placeholder="Nombre o propietario...")
    
    filtered_vendors = [
        v for v in vendors 
        if search_query.lower() in v['name'].lower() or search_query.lower() in v['owner'].lower()
    ]
    
    vendor_names = [v['name'] for v in filtered_vendors]
    # selectbox for scalability with large client lists
    selected_name = st.sidebar.selectbox(
        "Seleccionar Vendedor", 
        options=vendor_names if vendor_names else ["No se encontraron resultados"],
        index=0 if vendor_names else None
    )
    
    st.sidebar.markdown("---")
    st.sidebar.write("💡 ¿Necesita información regulatoria?")
    if st.sidebar.button("📜 Ver Guía de Licencias", use_container_width=True):
        show_license_directory()

    # Form to Register a New Food Truck Client
    with st.sidebar.expander("➕ Registrar Nuevo Cliente"):
        with st.form("new_vendor_form", clear_on_submit=True):
            new_name = st.text_input("Nombre del Food Truck *")
            new_owner = st.text_input("Nombre del Propietario *")
            new_status = st.selectbox("Estado Inicial", ["Incompleto", "Cumple", "Vencido"])
            submitted = st.form_submit_button("Guardar Cliente")
            
            if submitted:
                if new_name and new_owner:
                    new_client = {
                        "name": new_name,
                        "owner": new_owner,
                        "status": new_status,
                        "last_audit": date.today().strftime('%Y-%m-%d'),
                        "score": 0
                    }
                    try:
                        result = supabase.table("vendors").insert(new_client).execute()
                        if result.data:
                            st.toast(f"¡{new_name} guardado permanentemente!", icon="✅")
                            st.rerun()
                        else:
                            st.error("La base de datos rechazó el registro de forma silenciosa.")
                    except Exception as e:
                        st.error(f"Error de base de datos: {e}")
                else:
                    st.error("Por favor complete los campos obligatorios (*)")
                    
    if not filtered_vendors or selected_name == "No se encontraron resultados":
        st.title("Gestión de Cumplimiento de Vendedores")
        st.info("Por favor, seleccione un vendedor de la barra lateral para ver sus registros detallados de cumplimiento.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Vendedores", len(vendors))
        col2.metric("En Regla / Cumplen", "33%", delta="5%")
        col3.metric("Problemas Detectados", "2", delta="-1", delta_color="inverse")
        return

    # Vendor Detail View
    vendor = next(v for v in vendors if v['name'] == selected_name)

    # -----------------------------------------------------------------
    # DATABASE QUERY: Fetch Permits for current vendor from new table
    # -----------------------------------------------------------------
    raw_permits = []
    
    try:
        permits_response = supabase.table("vendor_permits").select("*").eq("vendor_id", vendor["id"]).execute()
        if permits_response and hasattr(permits_response, 'data'):
            raw_permits = permits_response.data
    except Exception as e:
        st.error(f"Error loading permits from Supabase: {e}")
        raw_permits = []
        
    # Header Section
    col_title, col_status = st.columns([3, 1])
    with col_title:
        st.title(vendor['name'])
        st.caption(f"Propietario: {vendor['owner']} | Última Auditoría: {vendor['last_audit']}")
    
    with col_status:
        if vendor['status'] == "Cumple":
            st.success(f"Estado: {vendor['status']}")
        elif vendor['status'] == "Vencido":
            st.error(f"Estado: {vendor['status']}")
        else:
            st.warning(f"Estado: {vendor['status']}")

    st.markdown("---")

    # Metrics Row
    m1, m2, m3 = st.columns(3)
    
    # Calculate dynamic compliance score based on live permits
    today_str = date.today().strftime('%Y-%m-%d')
    total_permits = len(raw_permits)
    
    if total_permits > 0:
        # Count how many permits are NOT expired
        valid_permits = len([p for p in raw_permits if p['expiration_date'] >= today_str])
        # Calculate percentage
        dynamic_score = int((valid_permits / total_permits) * 100)
    else:
        dynamic_score = 0 # Default if they have no documents uploaded yet

    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(ui_labels["score"], f"{dynamic_score}%")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(ui_labels["registered"], len(raw_permits))
        st.markdown('</div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        today_str = date.today().strftime('%Y-%m-%d')
        missing = len([p for p in raw_permits if p['expiration_date'] < today_str])
        st.metric(ui_labels["tasks"], missing)
        st.markdown('</div>', unsafe_allow_html=True)

    # Document Table
    st.subheader(ui_labels["repo_title"])
    try:
        rules_response = supabase.table("permit_rules").select("id", "permit_name", "category", "is_required").execute()
        mandatory_permits = rules_response.data if rules_response.data else []
        
    except Exception as e:
        st.error(f"Error cargando reglas de cumplimiento: {e}")
        mandatory_permits = []

    if not mandatory_permits:
        st.info("No se encontraron permisos configurados en la base de datos.")
    else:
        processed_permits = []
        today_str = date.today().strftime('%Y-%m-%d')
    
        # Mapeamos los archivos cargados del vendedor usando su identificador 'permit_id'
        uploaded_dict = {p["permit_id"]: p for p in raw_permits if p.get("permit_id") is not None}
        
        # 2. Iterar sobre la lista de lo que DEBERÍA tener cada Food Truck
        for rule in mandatory_permits:
            rule_id = rule["id"]
            permit_name = rule["permit_name"]
            backend_key = rule["category"]
            is_required = rule.get("is_required", True)
            
            if permit_name in ['Generic Tax Document', 'Other Document Type', 'other']:
                continue
                
            translated_category = CATEGORY_TRANSLATIONS[user_lang].get(backend_key, backend_key)
            
            # Buscamos primero por ID de regla; si no hay registro, cae en el string de compatibilidad anterior
            #vendedor_permit = uploaded_dict.get(rule_id) or uploaded_by_name.get(permit_name)
            vendedor_permit = uploaded_dict.get(rule_id)
            
            if vendedor_permit:
                expiration_date = vendedor_permit["expiration_date"]
                if expiration_date < today_str:
                    status_text = "Vencido" if user_lang == "es" else "Expired"
                else:
                    status_text = "Aprobado" if user_lang == "es" else "Approved"
            else:
                status_text = "Faltante" if user_lang == "es" else "Missing"
                expiration_date = "-----"
                
            processed_permits.append({
                ui_labels["document"]: permit_name,
                ui_labels["category"]: translated_category,
                ui_labels["expiry"]: expiration_date,
                ui_labels["status"]: status_text
            })

        # 3. Generar el DataFrame y renderizar la tabla con estilos dinámicos
        df_display = pd.DataFrame(processed_permits)
        
        def style_status(val):
            if val in ['Aprobado', 'Approved']:
                return 'background-color: #d1fae5; color: #065f46; font-weight: bold; border-radius: 5px;'
            elif val in ['Vencido', 'Expired']:
                return 'background-color: #fee2e2; color: #991b1b; font-weight: bold; border-radius: 5px;'
            else: # Faltante / Missing
                return 'background-color: #fef3c7; color: #92400e; font-weight: bold; border-radius: 5px;'

        #st.table(df_display.style.map(style_status, subset=[ui_labels["status"]]))
        st.dataframe(
            df_display.style.map(style_status, subset=[ui_labels["status"]]), 
            use_container_width=True,
            hide_index=True
        )

    # Management Actions
    with st.expander("📤 Cargar y Escanear Nuevo Documento"):
        st.markdown("### 🤖 Sistema de Escaneo Automático (OCR)")

        # === CHANGE: Initialize Master Visibility Switch and Uploader ID ===
        if "show_verification_form" not in st.session_state:
            st.session_state.show_verification_form = True
        
        if "uploader_id" not in st.session_state:
            st.session_state.uploader_id = 1
        
        # Step 1: Force category selection first
        available_categories = {
            CATEGORY_TRANSLATIONS[user_lang][key]: key 
            for key in ["tax", "health", "fire_safety", "business_license", "other"]
        }
        
        selected_ui_category = st.selectbox(
            "1. Seleccione la categoría del documento *",
            options=["-- Seleccione una categoría --"] + list(available_categories.keys())
        )
        
        if selected_ui_category != "-- Seleccione una categoría --":
            backend_category_key = available_categories[selected_ui_category]
            
            # === CHANGE: File upload with dynamic ID controlled by session state ===
            uploaded_file = st.file_uploader(
                f"2. Suba el documento de {selected_ui_category} para escaneo automático", 
                type=['pdf', 'jpg', 'png'],
                key=f"file_uploader_key_{st.session_state.uploader_id}"
            )

            if uploaded_file is not None and st.session_state.get("current_file") != uploaded_file.name:
                st.session_state.show_verification_form = True
            
            if uploaded_file is not None:
                # Use session state to cache OCR results so they don't re-run on every click
                if "ocr_data" not in st.session_state or st.session_state.get("current_file") != uploaded_file.name:
                    with st.spinner("🤖 Analizando documento con AWS Textract... Leyendo datos..."):
                        
                        # Read the file bytes directly from Streamlit memory
                        file_bytes = uploaded_file.read()
                        
                        # ==========================================================
                        # PLACE THE NEW DIRECT-STREAM LINE HERE:
                        # ==========================================================
                        extracted_text = run_ocr_processor(file_bytes, backend_category_key)
                        # ==========================================================
                        
                        # Save to session state to prevent reprocessing loops
                        st.session_state.ocr_data = extracted_text
                        st.session_state.current_file = uploaded_file.name
                        st.success("¡Lectura de datos completada con éxito!")

                # Retrieve scanned data from state cache
                scanned = st.session_state.ocr_data

                # === CHANGE: INTERNAL SAFETY SWITCH (Halts rendering after saving) ===
                if not st.session_state.get("show_verification_form", True):
                    st.info("🔄 Proceso finalizado. El expediente del cliente ha sido actualizado.")
                    st.stop()
                # =====================================================================
                    
                with st.form("verificacion_documento_form"):
                    st.markdown("### 🔍 Verifique los Datos Extraídos")
                    st.caption("El sistema leyó la siguiente información. Corrija cualquier dato si es necesario antes de guardar.")
                
                    # Step 3: Prefill fields with OCR outputs.
                    review_entity = st.text_input(
                        "Entidad Emisora / Nombre del Documento Detectado *", 
                        value=scanned.get("issuing_entity", "")
                    )
                
                    # =====================================================================
                    from dateutil.relativedelta import relativedelta

                    # Determinar Fecha de Emisión
                    try:
                        default_issue_date = datetime.strptime(scanned.get("issue_date", ""), "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        try:
                            default_issue_date = datetime.strptime(scanned.get("issue_date", ""), "%m/%d/%Y").date()
                        except (ValueError, TypeError):
                            default_issue_date = date.today()

                    review_issue = st.date_input("Fecha de Emisión Detectada *", value=default_issue_date)

                    # Calcular o Determinar Fecha de Vencimiento
                    default_expiry_date = None

                    if scanned.get("expiration_date"):
                        try:
                            default_expiry_date = datetime.strptime(scanned.get("expiration_date", ""), "%Y-%m-%d").date()
                        except (ValueError, TypeError):
                            try:
                                default_expiry_date = datetime.strptime(scanned.get("expiration_date", ""), "%m/%d/%Y").date()
                            except (ValueError, TypeError):
                                default_expiry_date = None

                    # Si el OCR no detectó vencimiento, consultamos a Supabase con la estrategia de doble capa
                    if not scanned.get("expiration_date") or default_expiry_date is None:
                        try:
                            # Capa 1: Buscar por el nombre específico del documento (ej: 'Food Manager Certificate')
                            rule_response = supabase.table("permit_rules").select("validity_months").eq("permit_name", review_entity).execute()
        
                            if rule_response.data:
                                months_to_add = rule_response.data[0]["validity_months"]
                            else:
                                # Capa 2: Respaldo por categoría general
                                fallback_response = supabase.table("permit_rules").select("validity_months").eq("category", backend_category_key).limit(1).execute()
                                if fallback_response.data:
                                    months_to_add = fallback_response.data[0]["validity_months"]
                                else:
                                    months_to_add = 12 
                        except Exception as e:
                            months_to_add = 12
                            st.warning(f"Error al conectar con las reglas de Supabase: {e}")

                        # Calcular sumando los meses dinámicos a la fecha de emisión
                        default_expiry_date = review_issue + relativedelta(months=months_to_add)

                    review_expiry = st.date_input("Fecha de Vencimiento Detectada *", value=default_expiry_date)
                    # =====================================================================
                
                    # 3. EL BOTÓN DE SUBMIT AL FINAL (Controla la ejecución)
                    submitted = st.form_submit_button("Confirmar y Guardar en Expediente", type="primary", use_container_width=True)
                    
                    if submitted:

                  # # 2. El botón de confirmación que modificamos en el primer paso va inmediatamente después
                 #  if st.button("Confirmar y Guardar en Expediente", type="primary", use_container_width=True):
                        if review_entity and review_expiry and review_issue:
                            # 1. CLEAN THE VENDOR NAME (Lowercase, strip spaces, replace spaces with hyphens)
                            # Assumes your vendor dictionary has a "name" key (e.g., vendor["name"] = "Thai Spice")
                            vendor_name_clean = vendor["name"].strip().lower().replace(" ", "-")
                            
                            # 2. CREATE THE NEW FILENAME (e.g., thai-spice-Galaxy-SERVICES.pdf)
                            new_filename = f"{vendor_name_clean}-{uploaded_file.name}"
                            
                            # A. Los datos ya están verificados, AHORA subimos a Drive
                            with st.spinner("📤 Datos verificados. Subiendo archivo a Google Drive..."):
                                # We pass 'new_filename' instead of 'uploaded_file.name'
                                drive_url = upload_to_drive(uploaded_file, new_filename)
                            if not drive_url:
                                st.error("❌ El archivo no pudo ser subido a Google Drive. Revisa los permisos o el tamaño del archivo. Operación cancelada.")
                                st.stop() # Detiene la ejecución aquí para que el error no desaparezca
                                
                            # Buscamos el ID correspondiente de la regla para inyectarlo en la llave foránea
                            matched_rule_id = None
                            if mandatory_permits:
                                clean_review_entity = review_entity.strip().lower()
                                matched_rule = next((r for r in mandatory_permits if r["permit_name"] == review_entity), None)
                                if matched_rule:
                                    matched_rule_id = matched_rule["id"]
                                else:
                                    # Fallback opcional por si el nombre cambió un poco pero la categoría coincide
                                    fallback_rule = next((r for r in mandatory_permits if r["category"] == backend_category_key), None)
                                    if fallback_rule:
                                        matched_rule_id = fallback_rule["id"]
                                        
                            new_permit_row = {
                                 "vendor_id": vendor["id"],
                                 "permit_id": matched_rule_id,
                                 "category": backend_category_key,
                                 "issuing_entity": review_entity,
                                 "issue_date": review_issue.strftime('%Y-%m-%d'), 
                                 "expiration_date": review_expiry.strftime('%Y-%m-%d')
                            }
                            try:
                                result = supabase.table("vendor_permits").insert(new_permit_row).execute()
                                if result.data:
                                    # === CHANGES FOR ABSOLUTE FILE CLEARANCE ===
                                    # 1. Hide the form from the UI immediately
                                    st.session_state.show_verification_form = False
                                
                                    # 2. Increment ID to destroy and re-create the file uploader component empty
                                    st.session_state.uploader_id += 1
                                
                                    # 3. Delete old cached file metadata
                                    if "ocr_data" in st.session_state:
                                        del st.session_state.ocr_data
                                    if "current_file" in st.session_state:
                                        del st.session_state.current_file
                                    
                                    st.toast("¡Documento guardado y verificado con éxito!", icon="✅")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al guardar registros: {e}")
                        else:
                            st.error("Los campos requeridos no pueden estar vacíos.")

    # Critical Alerts
    if vendor['status'] == "Vencido":
        st.error(f"⚠️ **ACCION INMEDIATA REQUERIDA**: {vendor['name']} tiene permisos críticos vencidos. Se ha redactado un aviso de 'Suspensión de Servicio'.")
        if st.button("Enviar Notificación Formal"):
            st.info("Notificación enviada al correo electrónico del propietario.")

if __name__ == "__main__":
    main()

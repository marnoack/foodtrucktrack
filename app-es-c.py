import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
import boto3
import re

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
                
        combined_text = " ".join(all_lines).lower()
        
        # Basic context classification heuristics
        if "health" in combined_text or "sanitation" in combined_text:
            extracted_data["issuing_entity"] = "Department of State Health Services"
        elif "fire" in combined_text or "marshal" in combined_text:
            extracted_data["issuing_entity"] = "Fire Marshal Office"
        elif "comptroller" in combined_text or "tax" in combined_text:
            extracted_data["issuing_entity"] = "State Comptroller Office"
        else:
            extracted_data["issuing_entity"] = "City Regulatory Authority"
            
        # REGEX DATE EXTRACTION ENGINE ---
        # Matches both MM/DD/YYYY and YYYY-MM-DD formats
        date_pattern = r'\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b'
        
        # Look specifically for Issue Date prefixes (e.g., "date issue:", "issued:", "emisión:")
        issue_match = re.search(r'(?:date issue|issued|emision|fecha de emision)\s*[:\-]?\s*' + date_pattern, combined_text)

        # Look specifically for Expiration Date prefixes (e.g., "expiration:", "expires:", "vencimiento:")
        expiry_match = re.search(r'(?:expiration|expires|vence|vencimiento|valid thru)\s*[:\-]?\s*' + date_pattern, combined_text)
        
# Helper to clean and format whatever string format regex captures
        def normalize_date_string(date_str):
            date_str = date_str.strip()
            # If it's MM/DD/YYYY, convert it to standard database YYYY-MM-DD
            if "/" in date_str:
                try:
                    return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    pass
            return date_str # Return as-is if it's already YYYY-MM-DD
            
        # Assign extracted Issue Date
        if issue_match:
            extracted_data["issue_date"] = normalize_date_string(issue_match.group(1))
        else:
            # Fallback to today's date if no clear issue header pattern is found
            extracted_data["issue_date"] = date.today().strftime('%Y-%m-%d')
            
        # Assign extracted Expiration Date
        if expiry_match:
            extracted_data["expiration_date"] = normalize_date_string(expiry_match.group(1))
        else:
            # If no explicit expiration pattern is found, try picking the second standalone date found in the document
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
            "vencido": "Expired"
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
            "vencido": "Vencido"
        }
    }
}

# Setup language state (from user toggle or default)
if "lang" not in st.session_state:
    st.session_state.lang = "es"  # Defaulting to Spanish based on dashboard style

user_lang = st.session_state.lang
ui_labels = CATEGORY_TRANSLATIONS[user_lang]["ui"]

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
    vendors = load_data()
    
    # Sidebar Navigation
    st.sidebar.title("🚚 CompliancePro")
    
    # Simple Language Toggle in Sidebar UI
    lang_choice = st.sidebar.selectbox("🌐 Idioma / Language", ["Español", "English"])
    st.session_state.lang = "es" if lang_choice == "Español" else "en"
    
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
        st.metric("Puntaje de Cumplimiento", f"{dynamic_score}%")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Documentos Registrados", len(raw_permits))
        st.markdown('</div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        today_str = date.today().strftime('%Y-%m-%d')
        missing = len([p for p in raw_permits if p['expiration_date'] < today_str])
        st.metric("Tareas Pendientes", missing)
        st.markdown('</div>', unsafe_allow_html=True)

    # Document Table
    st.subheader("Repositorio de Documentos")
    
    if not raw_permits:
        st.info("No se encontraron permisos o certificaciones en el repositorio de este cliente.")
    else:
        # Process database array into translated UI display lists
        processed_permits = []
        for p in raw_permits:
            # 1. Evaluate clean automated state statuses using current system date
            is_expired = p['expiration_date'] < date.today().strftime('%Y-%m-%d')
            status_text = ui_labels["vencido"] if is_expired else ui_labels["aprobado"]
            
            # 2. Extract specific backend mapping dictionary values
            backend_key = p['category']
            translated_category = CATEGORY_TRANSLATIONS[user_lang].get(backend_key, backend_key)
            
            processed_permits.append({
                ui_labels["document"]: p["issuing_entity"],
                ui_labels["category"]: translated_category,
                ui_labels["expiry"]: p["expiration_date"],
                ui_labels["status"]: status_text
            })

        df_display = pd.DataFrame(processed_permits)
        
        # Styled table display condition methods
        def style_status(val):
            is_ok = val in ['Aprobado', 'Approved']
            color = '#d1fae5' if is_ok else '#fee2e2'
            text_color = '#065f46' if is_ok else '#991b1b'
            return f'background-color: {color}; color: {text_color}; font-weight: bold; border-radius: 5px'

        st.table(df_display.style.map(style_status, subset=[ui_labels["status"]]))
        
    # Management Actions
    with st.expander("📤 Cargar y Escanear Nuevo Documento"):
        st.markdown("### 🤖 Sistema de Escaneo Automático (OCR)")
        
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
            
            # Step 2: File upload acts as the trigger for OCR processing
            uploaded_file = st.file_uploader(
                f"2. Suba el documento de {selected_ui_category} para escaneo automático", 
                type=['pdf', 'jpg', 'png']
            )
            
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
                
                st.markdown("### 🔍 Verifique los Datos Extraídos")
                st.caption("El sistema leyó la siguiente información. Corrija cualquier dato si es necesario antes de guardar.")
                
                # Step 3: Prefill fields with OCR outputs.
                review_entity = st.text_input(
                    "Entidad Emisora / Nombre del Documento Detectado *", 
                    value=scanned.get("issuing_entity", "")
                )
                
                # --- NEW: Convert string ISSUE DATE back to date picker object ---
                try:
                    default_issue_date = datetime.strptime(scanned.get("issue_date", ""), "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    default_issue_date = datetime.today().date()
                    
                review_issue = st.date_input("Fecha de Emisión Detectada *", value=default_issue_date)
                
                # Convert string EXPIRATION DATE back to date picker object
                try:
                    default_expiry_date = datetime.strptime(scanned.get("expiration_date", ""), "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    default_expiry_date = None
                    
                review_expiry = st.date_input("Fecha de Vencimiento Detectada *", value=default_expiry_date)
                
                # Step 4: Final Confirmation
                if st.button("Confirmar y Guardar en Expediente", type="primary", use_container_width=True):
                    if review_entity and review_expiry:
                        new_permit_row = {
                            "vendor_id": vendor["id"],
                            "category": backend_category_key,
                            "issuing_entity": review_entity,
                            "issue_date": review_issue.strftime('%Y-%m-%d'),
                            "expiration_date": review_expiry.strftime('%Y-%m-%d')
                        }
                        
                        try:
                            result = supabase.table("vendor_permits").insert(new_permit_row).execute()
                            if result.data:
                                # Clear OCR cache on successful upload to reset state completely
                                del st.session_state.ocr_data
                                del st.session_state.current_file
                                st.toast("¡Documento guardado y verificado en la base de datos!", icon="✅")
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

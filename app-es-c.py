import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

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

#*****************************************************************
# Setup language state (from user toggle or default)
if "lang" not in st.session_state:
    st.session_state.lang = "es"  # Defaulting to Spanish based on dashboard style

user_lang = st.session_state.lang
ui_labels = CATEGORY_TRANSLATIONS[user_lang]["ui"]

#*****************************************************************

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

# 🔄 REPLACE YOUR OLD LOAD_DATA FUNCTION WITH THIS:
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
    # Dynamically pull fresh state from your database client
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
    selected_name = st.sidebar.radio("Seleccionar Vendedor", vendor_names if vendor_names else ["No se encontraron resultados"])
    
    # License Directory Action Button in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.write("💡 ¿Necesita información regulatoria?")
    if st.sidebar.button("📜 Ver Guía de Licencias", use_container_width=True):
        show_license_directory()

    # ---------------------------------------------------------
    # NEW: Form to Register a New Food Truck Client
    # ---------------------------------------------------------
    with st.sidebar.expander("➕ Registrar Nuevo Cliente"):
        with st.form("new_vendor_form", clear_on_submit=True):
            new_name = st.text_input("Nombre del Food Truck *")
            new_owner = st.text_input("Nombre del Propietario *")
            
            # Initial Status selection
            new_status = st.selectbox(
                "Estado Inicial", 
                ["Incompleto", "Cumple", "Vencido"]
            )
            
            # Form submission button
            submitted = st.form_submit_button("Guardar Cliente")
            
            if submitted:
                if new_name and new_owner:
                    # Create the basic dictionary structure matching your data
                    new_client = {
                        "id": str(len(vendors) + 1),
                        "name": new_name,
                        "owner": new_owner,
                        "status": new_status,
                        "last_audit": datetime.today().strftime('%Y-%m-%d'),
                        "score": 0,  # Starts at 0% until audited
                    }
                    
                    try:
                        # Perform the cloud execution
                        result = supabase.table("vendors").insert(new_client).execute()
                        
                        # Verify Supabase actually returned data confirming the save
                        if result.data:
                            st.toast(f"¡{new_name} guardado permanentemente!", icon="✅")
                            st.rerun()
                        else:
                            st.error("La base de datos rechazó el registro de forma silenciosa.")
                    except Exception as e:
                        # This will catch and print column name errors or type mismatches
                        st.error(f"Error de base de datos: {e}")
                else:
                    st.error("Por favor complete los campos obligatorios (*)")
                    
    # ---------------------------------------------------------
    if not filtered_vendors or selected_name == "No se encontraron resultados":
        st.title("Gestión de Cumplimiento de Vendedores")
        st.info("Por favor, seleccione un vendedor de la barra lateral para ver sus registros detallados de cumplimiento.")
        
        # Summary Overview for Dashboard Home
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Vendedores", len(vendors))
        col2.metric("En Regla / Cumplen", "33%", delta="5%")
        col3.metric("Problemas Detectados", "2", delta="-1", delta_color="inverse")
        return

    # Vendor Detail View
    vendor = next(v for v in vendors if v['name'] == selected_name)
    
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
    with m1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Puntaje de Cumplimiento", f"{vendor['score']}%")
        st.markdown('</div>', unsafe_allow_html=True)
    with m2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Documentos Registrados", len(vendor['permits']))
        st.markdown('</div>', unsafe_allow_html=True)
    with m3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        missing = len([p for p in vendor['permits'] if p['status'] in ["Faltante", "Vencido"]])
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
    with st.expander("Actualizar Registros y Notas"):
        note = st.text_area("Notas de Auditoría", placeholder="Ingrese las observaciones de la última visita al sitio...")
        uploaded_file = st.file_uploader("Subir Nuevo Documento", type=['pdf', 'jpg', 'png'])
        if st.button("Enviar Actualización"):
            st.toast("¡Registro actualizado con éxito!", icon="✅")

    # Critical Alerts
    if vendor['status'] == "Vencido":
        st.error(f"⚠️ **ACCION INMEDIATA REQUERIDA**: {vendor['name']} tiene permisos críticos vencidos. Se ha redactado un aviso de 'Suspensión de Servicio'.")
        if st.button("Enviar Notificación Formal"):
            st.info("Notificación enviada al correo electrónico del propietario.")

if __name__ == "__main__":
    main()

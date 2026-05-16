import streamlit as st
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Panel de Control CompliancePro",
    page_icon="🚚",
    layout="wide"
)

# Mock Data
def load_data():
    return [
        {
            "id": "1",
            "name": "The Rolling Taco",
            "owner": "Maria Garcia",
            "status": "Incompleto",
            "last_audit": "2024-05-10",
            "score": 65,
            "permits": [
                {"document": "Business License", "status": "Aprobado", "expiry": "2025-01-15"},
                {"document": "Health Dept Permit", "status": "Pendiente", "expiry": "2024-06-20"},
                {"document": "Fire Safety Cert", "status": "Faltante", "expiry": "N/A"},
                {"document": "Food Handler Cards", "status": "Aprobado", "expiry": "2024-12-01"}
            ]
        },
        {
            "id": "2",
            "name": "Burger Galaxy",
            "owner": "John Smith",
            "status": "Cumple",
            "last_audit": "2024-05-15",
            "score": 98,
            "permits": [
                {"document": "Business License", "status": "Aprobado", "expiry": "2025-03-22"},
                {"document": "Health Dept Permit", "status": "Aprobado", "expiry": "2025-05-01"},
                {"document": "Fire Safety Cert", "status": "Aprobado", "expiry": "2024-11-15"},
                {"document": "Food Handler Cards", "status": "Aprobado", "expiry": "2025-01-10"}
            ]
        },
        {
            "id": "3",
            "name": "Sushi Stop",
            "owner": "Kenji Sato",
            "status": "Vencido",
            "last_audit": "2024-04-20",
            "score": 42,
            "permits": [
                {"document": "Business License", "status": "Vencido", "expiry": "2024-04-01"},
                {"document": "Health Dept Permit", "status": "Aprobado", "expiry": "2024-09-12"},
                {"document": "Fire Safety Cert", "status": "Aprobado", "expiry": "2024-12-30"},
                {"document": "Food Handler Cards", "status": "Aprobado", "expiry": "2024-10-15"}
            ]
        }
    ]

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
    # Check if data is already in session memory; if not, load initial mock/database data
    if 'vendors_list' not in st.session_state:
        st.session_state.vendors_list = load_data()
        
    # Use the session data instead of a static variable
    vendors = st.session_state.vendors_list
    
    # Sidebar Navigation
    st.sidebar.title("🚚 CompliancePro")
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
                        "permits": [
                            {"document": "Business License", "status": "Faltante", "expiry": "N/A"},
                            {"document": "Health Dept Permit", "status": "Faltante", "expiry": "N/A"},
                            {"document": "Fire Safety Cert", "status": "Faltante", "expiry": "N/A"},
                            {"document": "Food Handler Cards", "status": "Faltante", "expiry": "N/A"}
                        ]
                    }
                    
                    # Append to our local data session
                    vendors.append(new_client)
                    st.toast(f"¡{new_name} registrado exitosamente!", icon="✅")
                    
                    # Force rerun so the sidebar radio selection updates immediately
                    st.rerun()
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
    
    # Translating column headers visually for Spanish clients
    df = pd.DataFrame(vendor['permits'])
    df_es = df.rename(columns={
        "document": "Documento",
        "status": "Estado",
        "expiry": "Fecha de Vencimiento"
    })
    
    # Styled table display (using the corrected .map() method)
    def style_status(val):
        color = '#d1fae5' if val == 'Aprobado' else '#fee2e2' if val in ['Vencido', 'Faltante'] else '#fef3c7'
        text_color = '#065f46' if val == 'Aprobado' else '#991b1b' if val in ['Vencido', 'Faltante'] else '#92400e'
        return f'background-color: {color}; color: {text_color}; font-weight: bold; border-radius: 5px'

    st.table(df_es.style.map(style_status, subset=['Estado']))

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

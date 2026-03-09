# main.py
import streamlit as st
from datetime import date, timedelta
import core
import os  # Fixed the missing import that caused your error

st.set_page_config(page_title="New Delhi Cause List Generator", layout="wide")
st.title("⚖️ New Delhi District Court PDF Cause List Generator")

# --- Initialize the driver at the start ---
if 'driver' not in st.session_state:
    with st.spinner("Initializing browser... Please wait."):
        st.session_state.driver = core.initialize_driver()
driver = st.session_state.driver

# --- Session State Caching ---
if 'complex_list' not in st.session_state:
    st.session_state.complex_list = {}
    st.session_state.establishment_list = {}
    st.session_state.last_primary_id = None
    st.session_state.court_list = {}
    # State for batch processing
    st.session_state.court_queue = []
    st.session_state.batch_results = []

# --- Fetch initial data using the API method ---
if not st.session_state.complex_list:
    with st.spinner("Fetching court complex and establishment lists..."):
        st.session_state.complex_list, st.session_state.establishment_list = core.get_complex_and_establishment_lists()

# --- UI Layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Court Selection")
    search_type_display = st.radio("Search By", ("Court Complex", "Court Establishment"), key="search_type_radio")
    search_type = "courtComplex" if search_type_display == "Court Complex" else "courtEstablishment"

    if search_type == "courtComplex":
        selected_primary_name = st.selectbox("Select Court Complex", list(st.session_state.complex_list.keys()), key="sb_complex")
        selected_primary_value = st.session_state.complex_list.get(selected_primary_name)
    else:
        selected_primary_name = st.selectbox("Select Court Establishment", list(st.session_state.establishment_list.keys()), key="sb_establishment")
        selected_primary_value = st.session_state.establishment_list.get(selected_primary_name)
    
    if selected_primary_value and selected_primary_value != st.session_state.last_primary_id:
        with st.spinner("Fetching court list from server..."):
            st.session_state.court_list = core.get_courts_via_api(selected_primary_value, search_type)
            st.session_state.last_primary_id = selected_primary_value
            st.session_state.court_queue = [] # Reset queue if complex changes
            st.session_state.batch_results = []

    if st.session_state.court_list:
        selected_court_name = st.selectbox("Select Specific Court (for single download)", list(st.session_state.court_list.keys()))
        selected_court_value = st.session_state.court_list.get(selected_court_name)
    else:
        st.warning("No courts loaded.")
        selected_court_value = None

with col2:
    st.subheader("2. Details & CAPTCHA")
    today = date.today()
    cause_list_date = st.date_input("Select Cause List Date", today, min_value=today - timedelta(days=30), max_value=today)
    case_type = st.radio("Case Type", ("Civil", "Criminal"), horizontal=True)
    
    st.write("**Enter the CAPTCHA code:**")
    
    if st.button("Refresh CAPTCHA"):
        st.rerun() 

    captcha_path = core.get_captcha_image(driver)
    if captcha_path:
        st.image(captcha_path)
    else:
        st.error("Could not load CAPTCHA image. Try refreshing.")
        
    captcha_text = st.text_input("Enter Captcha", label_visibility="collapsed")

# --- Single Download Button ---
st.markdown("---")
st.subheader("3. Single Court Download")

if st.button("Generate PDF for Selected Court", use_container_width=True, disabled=not selected_court_value):
    if captcha_text and selected_court_value and selected_primary_value:
        with st.spinner(f"Submitting form for {selected_court_name}..."):
            result = core.process_cause_list(driver, search_type, selected_primary_value, selected_court_value, cause_list_date, case_type, captcha_text)
        
        if result['status'] == 'success':
            st.success(f"Generated successfully!")
            file_path = os.path.join("output", result['file'])
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Cause List PDF",
                        data=f,
                        file_name=result['file'],
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.error(f"Failed: {result['data']}")
    else:
        st.warning("Please ensure a court is selected and CAPTCHA is entered.")

# --- START: REVISED BATCH PROCESSING SECTION ---
st.markdown("---")
st.subheader("4. Batch Download Helper")

if st.button("Start New Batch for All Courts in Complex", use_container_width=True):
    if st.session_state.court_list:
        st.session_state.court_queue = list(st.session_state.court_list.items())
        st.session_state.batch_results = []
        st.info(f"Batch initialized with {len(st.session_state.court_queue)} courts. The next court is ready below.")
        st.rerun()
    else:
        st.error("No court list is loaded. Please select a complex first.")

if st.session_state.court_queue:
    next_court_name, next_court_value = st.session_state.court_queue[0]
    
    st.warning(f"**Next in queue:** {next_court_name}")
    st.write(f"Remaining courts to process: {len(st.session_state.court_queue)}")

    if st.button("Process Next Court", use_container_width=True, type="primary"):
        if not captcha_text:
            st.error("Please enter the CAPTCHA to proceed!")
        else:
            with st.spinner(f"Processing {next_court_name}..."):
                result = core.process_cause_list(
                    driver,
                    search_type,
                    selected_primary_value,
                    next_court_value,
                    cause_list_date,
                    case_type,
                    captcha_text
                )
                
                if result['status'] == 'success':
                    st.session_state.batch_results.append({
                        "status": "success",
                        "court": next_court_name,
                        "file": result['file']
                    })
                    st.session_state.court_queue.pop(0) # Success! Remove from queue.
                else:
                    st.session_state.batch_results.append({
                        "status": "error",
                        "court": next_court_name,
                        "error": result['data']
                    })
            st.rerun()

# Display results from the batch process
if st.session_state.batch_results:
    st.markdown("---")
    st.subheader("Batch History")
    
    for res in reversed(st.session_state.batch_results):
        if res["status"] == "success":
            col_msg, col_btn = st.columns([3, 1])
            col_msg.success(f"✅ {res['court']}")
            file_path = os.path.join("output", res["file"])
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    col_btn.download_button("Download", f, file_name=res["file"], key=res["file"])
        else:
            st.error(f"❌ {res['court']}: {res['error']}")

if not st.session_state.court_queue and len(st.session_state.batch_results) > 0:
    st.success("🎉 Batch complete! All courts have been processed.")

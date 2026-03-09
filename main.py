# main.py
import os
import uuid
import base64
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import core

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory dictionary to keep browser instances alive with timestamps
active_sessions = {}

# --- ROUTE: Serve the Frontend UI ---
@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

# --- MEMORY MANAGEMENT: Background task to kill abandoned browsers ---
async def cleanup_sessions():
    while True:
        now = datetime.now()
        expired_keys = []
        for session_id, session_data in active_sessions.items():
            if now - session_data['timestamp'] > timedelta(minutes=5): # 5 min timeout
                try:
                    session_data['driver'].quit()
                except:
                    pass
                expired_keys.append(session_id)
        
        for k in expired_keys:
            del active_sessions[k]
            
        await asyncio.sleep(60) # Run check every minute

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_sessions())

# --- API ROUTES ---
@app.get("/api/init")
def get_initial_data():
    complex_list, est_list = core.get_complex_and_establishment_lists()
    return {"complex_list": complex_list, "establishment_list": est_list}

@app.get("/api/courts")
def get_courts(est_code: str, service_type: str):
    return core.get_courts_via_api(est_code, service_type)

@app.get("/api/captcha")
def get_captcha():
    session_id = str(uuid.uuid4())
    driver = core.initialize_driver()
    
    # Store the driver alongside a timestamp for our cleanup task
    active_sessions[session_id] = {
        'driver': driver,
        'timestamp': datetime.now()
    }
    
    captcha_path = core.get_captcha_image(driver)
    if not captcha_path or not os.path.exists(captcha_path):
        raise HTTPException(status_code=500, detail="Failed to load CAPTCHA")
        
    with open(captcha_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    return {"session_id": session_id, "captcha_base64": encoded_string}

class SubmitRequest(BaseModel):
    session_id: str
    search_by: str
    primary_val: str
    court_val: str
    date_str: str
    case_type: str
    captcha_text: str

@app.post("/api/submit")
def submit_form(req: SubmitRequest):
    session_data = active_sessions.get(req.session_id)
    if not session_data:
        raise HTTPException(status_code=400, detail="Session expired. Please refresh the CAPTCHA.")
        
    driver = session_data['driver']
    
    try:
        date_obj = datetime.strptime(req.date_str, "%Y-%m-%d").date()
        result = core.process_cause_list(
            driver, req.search_by, req.primary_val, req.court_val, 
            date_obj, req.case_type, req.captcha_text
        )
        
        if result['status'] == 'success':
            file_path = os.path.join("output", result['file'])
            with open(file_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode('utf-8')
            return {"status": "success", "file_name": result['file'], "pdf_base64": pdf_b64}
        else:
            return result
    finally:
        # Always kill the browser after scraping
        driver.quit()
        if req.session_id in active_sessions:
            del active_sessions[req.session_id]

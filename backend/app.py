import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np
import mediapipe as mp
import base64
import shutil
import threading
from datetime import datetime
from pymongo import MongoClient
import glob
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Mount public directory for uploads
app.mount("/uploads", StaticFiles(directory="public/uploads"), name="uploads")

from .database import students_collection, attendance_collection, admin_collection, MONGO_URI

# ==== CONFIG ====
STUDENT_IMAGES_DIR = "backend/Student_Images"
UPLOAD_DIR = "public/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
SIMILARITY_THRESHOLD = 0.65 

# ==== MEDIAPIPE LAZY SETUP ====
mp_face_detection = None
face_detection = None

def get_face_detector():
    global mp_face_detection, face_detection
    if face_detection is None:
        print("[INFO] Initializing MediaPipe Face Detection...")
        mp_face_detection = mp.solutions.face_detection
        face_detection = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
    return face_detection

# ==== GLOBAL STATE ====
known_faces = [] # List of {"name": name, "hist": histogram}

print(f"[INFO] Connected to MongoDB at {MONGO_URI}")

# ==== CORS ====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== HELPER FUNCTIONS ====

def get_face_embedding(image):
    """
    Detects face and returns a Histogram 'embedding' for comparison.
    """
    if image is None:
        print("[ERROR] No image provided to get_face_embedding")
        return None
        
    height, width, _ = image.shape
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    detector = get_face_detector()
    results = detector.process(rgb_image)

    if not results or not results.detections:
        print("[WARNING] No face detected by MediaPipe")
        return None

    print(f"[INFO] Detected {len(results.detections)} face(s)")

    detection = results.detections[0]
    bboxC = detection.location_data.relative_bounding_box
    x, y, w, h = int(bboxC.xmin * width), int(bboxC.ymin * height), int(bboxC.width * width), int(bboxC.height * height)
    
    x_start = max(0, x)
    y_start = max(0, y)
    x_end = min(width, x + w)
    y_end = min(height, y + h)

    face_crop = image[y_start:y_end, x_start:x_end]
    if face_crop.size == 0: return None

    face_crop = cv2.resize(face_crop, (128, 128))
    hsv_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv_crop], [0, 1], None, [180, 256], [0, 180, 0, 256])
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    
    return hist

def load_known_faces():
    global known_faces
    known_faces = []
    
    # 1. Load from Disk
    if os.path.exists(STUDENT_IMAGES_DIR):
        all_files = glob.glob(os.path.join(STUDENT_IMAGES_DIR, "**", "*.*"), recursive=True)
        valid_extensions = {".jpg", ".jpeg", ".png"}
        img_files = [f for f in all_files if os.path.splitext(f)[1].lower() in valid_extensions]
        
        for file_path in img_files:
            img = cv2.imread(file_path)
            if img is not None:
                hist = get_face_embedding(img)
                if hist is not None:
                    name = os.path.basename(os.path.dirname(file_path)) or os.path.splitext(os.path.basename(file_path))[0]
                    known_faces.append({"name": name, "hist": hist})

    # 2. Load from Database
    db_students = list(students_collection.find({"faceEmbedding": {"$exists": True}}))
    for s in db_students:
        try:
            hist = np.array(s["faceEmbedding"], dtype=np.float32).reshape(180, 256)
            known_faces.append({"name": s["name"], "hist": hist})
        except:
            continue
            
    print(f"[INFO] Total loaded reference faces: {len(known_faces)}")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    print("[INFO] Starting face cache loader in background...")
    threading.Thread(target=load_known_faces, daemon=True).start()

# ==== AUTH ROUTES ====

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/admin/login")
async def login(data: LoginRequest):
    # For demo, allow hardcoded or any existing db admin
    if (data.email == "admin@vidya.com" or data.email == "admin@sbpcoe.ac.in") and data.password == "admin123":
        return {"user": {"name": "Administrator", "email": data.email, "role": "admin"}}
    
    admin = admin_collection.find_one({"email": data.email, "password": data.password})
    if admin:
        return {"user": {"name": admin.get("name", "Admin"), "email": admin["email"], "role": "admin"}}
    
    raise HTTPException(status_code=401, detail="Invalid Credentials")

# ==== STUDENT ROUTES ====

@app.get("/students/")
async def get_students():
    students = list(students_collection.find())
    for s in students:
        s["_id"] = str(s["_id"])
        if "faceEmbedding" in s: del s["faceEmbedding"]
    return students

@app.post("/students/add")
async def add_student(
    name: str = Form(...),
    rollNo: str = Form(...),
    department: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    file: UploadFile = File(...)
):
    if students_collection.find_one({"rollNo": rollNo}):
        raise HTTPException(status_code=400, detail="Student already exists")

    # Save photo
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{rollNo}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process embedding
    img = cv2.imread(filepath)
    hist = get_face_embedding(img)
    if hist is None:
        if os.path.exists(filepath): os.remove(filepath)
        raise HTTPException(status_code=400, detail="No face detected in photo")

    print(f"[INFO] Adding student: {name}, {rollNo}")
    student_data = {
        "name": name,
        "rollNo": rollNo,
        "department": department,
        "email": email,
        "phone": phone,
        "profileImage": f"/uploads/{filename}",
        "faceEmbedding": hist.flatten().tolist(),
        "createdAt": datetime.now()
    }
    
    result = students_collection.insert_one(student_data)
    load_known_faces() # Reload cache
    return {"id": str(result.inserted_id), "message": "Student added"}

@app.delete("/students/{id}")
async def delete_student(id: str):
    students_collection.delete_one({"_id": ObjectId(id)})
    return {"message": "Deleted"}

# ==== ATTENDANCE ROUTES ====

class AttendanceRequest(BaseModel):
    image: str

@app.post("/attendance/mark")
async def mark_attendance(data: AttendanceRequest):
    if not data.image:
        raise HTTPException(status_code=400, detail="No image")

    try:
        encoded = data.image.split(",", 1)[1] if "," in data.image else data.image
        image_data = base64.b64decode(encoded)
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None: raise HTTPException(status_code=400, detail="Invalid Image")

        target_hist = get_face_embedding(img)
        if target_hist is None: return {"status": "failed", "message": "No face detected"}

        best_score = 0
        best_match = None
        
        for person in known_faces:
            score = cv2.compareHist(target_hist, person["hist"], cv2.HISTCMP_CORREL)
            if score > best_score:
                best_score = score
                best_match = person["name"]

        if best_match and best_score > SIMILARITY_THRESHOLD:
            # Match
            student_info = students_collection.find_one({
                "$or": [{"rollNo": best_match}, {"name": best_match}, {"email": best_match}]
            })
            
            display_name = student_info["name"] if student_info else best_match
            roll_no = student_info["rollNo"] if student_info else "N/A"
            dept = student_info.get("department", "")

            today = datetime.now().strftime("%Y-%m-%d")
            existing = attendance_collection.find_one({"studentName": display_name, "date": today})
            
            if not existing:
                attendance_collection.insert_one({
                    "studentName": display_name,
                    "rollNo": roll_no,
                    "date": today,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "status": "Present"
                })
            
            return {
                "status": "success", 
                "message": f"Verified: {display_name}", 
                "student": {"name": display_name, "rollNo": roll_no, "department": dept}
            }
        
        return {"status": "failed", "message": "ACCESS DENIED: Face Not Recognized"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/attendance/today")
async def get_today():
    today = datetime.now().strftime("%Y-%m-%d")
    records = list(attendance_collection.find({"date": today}))
    for r in records: r["_id"] = str(r["_id"])
    return records

@app.get("/attendance/stats")
async def get_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    total = students_collection.count_documents({})
    present = attendance_collection.count_documents({"date": today})
    return {
        "totalStudents": total,
        "presentToday": present,
        "absentToday": max(0, total - present),
        "attendancePercentage": round((present / total * 100), 1) if total > 0 else 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

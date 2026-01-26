# Vidya Rakshak - AI-Powered attendance System 🎓🛡️

Vidya Rakshak is a modern, AI-driven attendance management system designed for educational institutions. It uses face recognition technology to automate attendance tracking and provide real-time monitoring and analytics.

## 🚀 Features
- **Face Recognition Attendance**: Automated marking of attendance using MediaPipe.
- **Admin Dashboard**: Comprehensive dashboard for managing students, viewing statistics, and tracking daily attendance.
- **Smart Camera Module**: Standalone real-time face tracking and recognition window.
- **Robust Backend**: Fast API based server with MongoDB integration.
- **Modern UI**: Clean, responsive frontend built with Next.js 15 and Tailwind CSS.

## 📁 Project Structure
- `/src`: Frontend application (Next.js 15).
- `/backend`: Core logic, API routes, and AI models.
- `/public/uploads`: Storage for student profile photos.
- `start_backend.bat`: Start the FastAPI server.
- `start_smart_camera.bat`: Start the standalone AI camera interface.

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (Running on `localhost:27017`)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

### 2. Frontend Setup
```bash
npm install
```

### 3. Running the Project
- **Start Backend**: Run `start_backend.bat` (Starts on port 8001).
- **Start Frontend**: Run `npm run dev`.
- **Start AI Camera**: Run `start_smart_camera.bat`.

## ⚙️ Configuration
The system uses an `.env` file for configuration. Ensure the `MONGO_URI` is correctly set to your MongoDB instance.

## 🔒 Security
The project uses `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` to ensure compatibility across different Windows environments.

---
Built with ❤️ for SBPCOE.

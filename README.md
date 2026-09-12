# Futuristic Contact Manager

A full-stack contact management system with:
- React + Vite + Tailwind frontend
- Python FastAPI backend with JSON file storage
- Full CRUD contacts
- Soft delete / restore / purge
- Audit log
- Activities timeline
- Reminders
- Tags
- Custom fields JSON
- CSV import/export
- Search functionality

## Backend
cd backend
pip install -r ../requirements.txt
python3 api.py

Backend runs on http://localhost:8001

## Frontend
cd frontend
npm install
npm run dev

Frontend runs on http://localhost:5173

## Docker
docker-compose up -d --build

## Features
- Contact management with firstName/lastName fields
- Tag system for categorization
- Soft delete with restore capability
- Audit logging for all changes
- JSON file-based data persistence
- CSV import/export functionality
- Real-time search across contacts

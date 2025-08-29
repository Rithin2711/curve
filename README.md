# Gravity Curve - Project Repository

This repository contains the Gravity Curve project.

Containers:
- Backend (FastAPI): curve/Backend
- Frontend (React): To be added in a separate container (curvy/Frontend)

Start Backend:
- See curve/Backend/README.md for setup and running instructions.

Notes:
- The backend exposes REST APIs consumed by the React frontend.
- Configure CORS via CORS_ALLOW_ORIGINS in curve/Backend/.env to match your frontend origin (e.g., http://localhost:3000).
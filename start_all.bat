@echo off
title APEX LabelSure - Launcher
echo ===================================================
echo        Starting APEX LabelSure Services
echo ===================================================

echo [1/3] Launching FastAPI Backend (Port 8000)...
start "APEX LabelSure Backend" powershell -NoExit -Command "cd /d D:\Akhi\Projects\LabelSure; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Launching React Admin Web Dashboard (Port 5173)...
start "APEX LabelSure Web Admin" powershell -NoExit -Command "cd /d D:\Akhi\Projects\LabelSure\apps\admin-web; npm run dev"

echo [3/3] Launching Flutter Mobile App Server (Port 8080)...
start "APEX LabelSure Mobile App" powershell -NoExit -Command "$env:Path += ';C:\src\flutter\bin'; cd /d D:\Akhi\Projects\LabelSure\apps\mobile; flutter run -d web-server --web-port 8080 --web-hostname 127.0.0.1"

echo.
echo ===================================================
echo All 3 services are launching in separate windows!
echo - Admin Web Dashboard: http://localhost:5173
echo - Mobile Inspector App: http://localhost:8080
echo - FastAPI Backend & Docs: http://localhost:8000/docs
echo ===================================================
pause

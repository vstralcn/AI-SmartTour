@echo off
chcp 65001 >nul
cd /d "%~dp0"
uvicorn app.main:app --reload --port 8000
pause

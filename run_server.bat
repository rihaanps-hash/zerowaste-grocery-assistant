@echo off
set PYTHON="C:\Users\Rihaan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
cd /d "%~dp0"
echo ========================================================
echo  Starting ZeroWaste Grocery Assistant - FastAPI Server
echo  Web Dashboard: http://127.0.0.1:8050/dashboard
echo ========================================================
%PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8050
pause

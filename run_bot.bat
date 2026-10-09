@echo off
set PYTHON="C:\Users\Rihaan\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
cd /d "%~dp0"
echo ========================================================
echo  Starting ZeroWaste Grocery Assistant - Telegram Bot
echo ========================================================
%PYTHON% telegram_bot.py
pause

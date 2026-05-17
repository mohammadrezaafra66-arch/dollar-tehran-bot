@echo off
cd /d %~dp0
if not exist config.yaml copy config.example.yaml config.yaml
if not exist .env copy .env.example .env
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
python main.py run-loop
pause

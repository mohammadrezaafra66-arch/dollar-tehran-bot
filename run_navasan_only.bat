@echo off
cd /d %~dp0
if not exist .env copy .env.example .env
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
python main.py run-once --config configs\navasan_only.yaml
pause

@echo off
call venv/Scripts/activate
@pause
pip install -r requirements.txt
python main.py
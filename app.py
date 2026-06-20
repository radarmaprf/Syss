import os
import json
import re
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Set
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# ---------- ВАШ ВЕСЬ КОД ИЗ bot.py ----------
# (Все функции: load_previous_state, save_alerts, fetch_all_posts, classify_message, 
#  get_affected_regions, apply_timeout, send_status_updates, compute_status, etc.)

# НО МЫ ДОБАВИМ ОДНУ ВАЖНУЮ ПРАВКУ:
# В compute_status() нужно убрать вызов send_status_updates(previous_state, status),
# потому что мы будем вызывать его отдельно.

def compute_status() -> Dict[str, Dict]:
    # ... весь код как раньше, но без send_status_updates в конце
    # Вместо этого мы вернём статус для отправки
    return status

# ---------- СОЗДАЁМ ВЕБ-ПРИЛОЖЕНИЕ ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот-парсер работает! Используйте /run для запуска."

@app.route('/run')
def run_parser():
    """Эндпоинт для запуска парсинга"""
    try:
        print(f"Запуск парсера в {datetime.now().isoformat()}")
        
        # Загружаем предыдущее состояние
        previous_state = load_previous_state()
        
        # Вычисляем новый статус
        status = compute_status()
        
        # Сохраняем новый статус
        save_alerts(status)
        
        # Отправляем уведомления о изменениях
        send_status_updates(previous_state, status)
        
        return jsonify({
            "status": "success",
            "message": "Парсинг выполнен успешно",
            "regions": len(status),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Запускаем Flask-сервер
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import os
import json
import re
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Set
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

# ---------- НАСТРОЙКИ ----------
CHANNEL = "vrv_radar"
BASE_URL = f"https://t.me/s/{CHANNEL}"
POSTS_LIMIT = 200
IGNORED_REGIONS = ["Астраханская область", "Архангельская область", "Омская область", "Курганская область", "Москва"]

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
CHAT_ID = os.getenv("CHAT_ID")
if not CHAT_ID:
    raise ValueError("CHAT_ID не задан")

# Файлы для состояния
ALERTS_FILE = "alerts.json"
PROCESSED_POSTS_FILE = "processed_posts.json"

# ... (ваши функции: STOP_WORDS, REGION_ALIASES, load_previous_state, save_alerts, 
# load_processed_posts, save_processed_posts, send_telegram_message, fetch_page, 
# extract_posts, fetch_all_posts, is_advertisement, classify_message, 
# get_affected_regions, apply_timeout, send_status_updates, compute_status)

# Я не буду дублировать весь код, но вы должны скопировать все функции сюда.

# ---------- СОЗДАЁМ ВЕБ-ПРИЛОЖЕНИЕ ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот-парсер запущен! Используйте /run для запуска."

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
        
        # Отправляем уведомления
        send_status_updates(previous_state, status)
        
        return jsonify({
            "status": "success",
            "message": "Парсинг выполнен",
            "regions": len(status),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

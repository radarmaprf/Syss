import os
import json
import re
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Set, Optional

# ---------- НАСТРОЙКИ ----------
CHANNEL = "vrv_radar"
BASE_URL = f"https://t.me/s/{CHANNEL}"
POSTS_LIMIT = 200
IGNORED_REGIONS = ["Астраханская область", "Архангельская область", "Омская область", "Курганская область", "Москва"]

STOP_WORDS = [
    "реклама", "подпишись", "подписаться", "каналы", "телеграм", "telegram",
    "бот", "сводки", "новости", "срочно", "важно", "обзор", "дайджест",
    "канал", "чат", "группа", "вконтакте", "vk", "youtube", "инстаграм",
    "instagram", "facebook", "twitter", "ссылка", "поддержать", "донат",
    "промокод", "скидка", "акция", "партнёр", "репост", "лайк", "комментарий"
]

REGION_ALIASES = {
    "Москва": ["москва"],
    "Московская область": ["московская область", "подмосковье"],
    "Санкт-Петербург": ["санкт-петербург", "питер", "спб"],
    "Ленинградская область": ["ленинградская область", "ленобласть"],
    "Белгородская область": ["белгородская область", "белгород"],
    "Брянская область": ["брянская область", "брянск"],
    "Владимирская область": ["владимирская область", "владимир"],
    "Воронежская область": ["воронежская область", "воронеж"],
    "Ивановская область": ["ивановская область", "иваново"],
    "Калужская область": ["калужская область", "калуга"],
    "Костромская область": ["костромская область", "кострома"],
    "Курская область": ["курская область", "курск"],
    "Липецкая область": ["липецкая область", "липецк"],
    "Нижегородская область": ["нижегородская область", "нижний новгород"],
    "Новгородская область": ["новгородская область", "великий новгород", "новгород"],
    "Орловская область": ["орловская область", "орёл"],
    "Пензенская область": ["пензенская область", "пенза"],
    "Псковская область": ["псковская область", "псков"],
    "Рязанская область": ["рязанская область", "рязань"],
    "Смоленская область": ["смоленская область", "смоленск"],
    "Тамбовская область": ["тамбовская область", "тамбов"],
    "Тверская область": ["тверская область", "тверь"],
    "Тульская область": ["тульская область", "тула"],
    "Ярославская область": ["ярославская область", "ярославль"],
    "Краснодарский край": ["краснодарский край", "краснодар", "кубань"],
    "Ставропольский край": ["ставропольский край", "ставрополь"],
    "Ростовская область": ["ростовская область", "ростов-на-дону", "ростов"],
    "Волгоградская область": ["волгоградская область", "волгоград"],
    "Татарстан": ["татарстан", "республика татарстан", "казань"],
    "Башкортостан": ["башкортостан", "республика башкортостан", "уфа"],
    "Марий Эл": ["марий эл", "республика марий эл", "йошкар-ола"],
    "Чувашия": ["чувашия", "чувашская республика", "чебоксары"],
    "Республика Мордовия": ["мордовия", "республика мордовия", "саранск"],
    "Удмуртская Республика": ["республика удмуртия", "удмуртская республика", "ижевск"],
    "Самарская область": ["самарская область", "самара"],
    "Саратовская область": ["саратовская область", "саратов"],
    "Ульяновская область": ["ульяновская область"],
    "Свердловская область": ["свердловская область", "екатеринбург"],
    "Челябинская область": ["челябинская область", "челябинск"],
    "Оренбургская область": ["оренбургская область", "оренбург"],
    "Пермский край": ["пермский край", "пермь"],
    "Новосибирская область": ["новосибирская область", "новосибирск"],
    "Томская область": ["томская область", "томск"],
    "Кемеровская область": ["кемеровская область", "кемерово", "кузбасс"],
    "Иркутская область": ["иркутская область", "иркутск"],
    "Красноярский край": ["краснодарский край", "краснодар", "кубань"],
    "Алтайский край": ["алтайский край", "барнаул"],
    "Забайкальский край": ["забайкальский край", "чита"],
    "Приморский край": ["приморский край", "владивосток"],
    "Хабаровский край": ["хабаровский край", "хабаровск"],
    "Амурская область": ["амурская область", "благовещенск"],
    "Сахалинская область": ["сахалинская область", "сахалин", "южно-сахалинск"],
    "Магаданская область": ["магаданская область", "магадан"],
    "Камчатский край": ["камчатский край", "камчатка", "петропавловск-камчатский"],
    "Мурманская область": ["мурманская область", "мурманск"],
    "Крым": ["крым", "республика крым"],
    "Дагестан": ["дагестан", "республика дагестан", "махачкала"],
    "Республика Карелия": ["карелия", "республика карелия", "петрозаводск"],
    "Республика Коми": ["коми", "республика коми", "сыктывкар"],
    "Республика Саха (Якутия)": ["якутия", "саха", "якутск"],
    "ХМАО": ["хмао", "ханты-мансийский", "ханты-мансийск", "сургут"],
    "ЯНАО": ["янао", "ямало-ненецкий", "новый уренгой", "ноябрьск"],
    "Адыгея": ["адыгея", "республика адыгея", "майкоп"]
}
for ign in IGNORED_REGIONS:
    REGION_ALIASES.pop(ign, None)

ALERTS_FILE = "alerts.json"
PROCESSED_POSTS_FILE = "processed_posts.json"

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_moscow_time():
    """Возвращает текущее время в Москве (UTC+3) в формате ЧЧ:ММ (МСК)"""
    moscow_tz = timezone(timedelta(hours=3))
    now = datetime.now(moscow_tz)
    return now.strftime("%H:%M")

def ensure_files_exist():
    if not os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"regions": {}}, f, ensure_ascii=False, indent=2)
        print(f"[{datetime.now().isoformat()}] Создан {ALERTS_FILE}")
    if not os.path.exists(PROCESSED_POSTS_FILE):
        with open(PROCESSED_POSTS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        print(f"[{datetime.now().isoformat()}] Создан {PROCESSED_POSTS_FILE}")

def load_previous_state() -> Dict[str, Dict]:
    try:
        with open(ALERTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "regions" in data:
                return data["regions"]
    except Exception:
        pass
    return {}

def save_alerts(state: Dict[str, Dict]):
    data = {"last_updated": datetime.now(timezone.utc).isoformat(), "regions": {}}
    for region in REGION_ALIASES:
        st = state.get(region, {"rocket": False, "droneAlert": False, "droneDanger": False})
        out = {
            "rocket": st.get("rocket", False),
            "droneAlert": st.get("droneAlert", False),
            "droneDanger": st.get("droneDanger", False)
        }
        if st.get("droneAlert", False) and "droneAlert_time" in st:
            out["droneAlert_time"] = st["droneAlert_time"]
        data["regions"][region] = out
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now().isoformat()}] alerts.json обновлён, регионов: {len(data['regions'])}")

def load_processed_posts() -> Set[int]:
    try:
        with open(PROCESSED_POSTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            else:
                return set()
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_processed_posts(processed_set: Set[int], max_size=500):
    posts_list = list(processed_set)
    if len(posts_list) > max_size:
        posts_list = posts_list[-max_size:]
    with open(PROCESSED_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts_list, f, ensure_ascii=False, indent=2)

# ---------- ПАРСИНГ ----------
def fetch_page(url: str) -> str:
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"Ошибка загрузки страницы (попытка {attempt+1}): {e}")
            time.sleep(2)
    raise Exception(f"Не удалось загрузить {url} после 3 попыток")

def extract_posts(html: str) -> List[Tuple[int, str]]:
    pattern = r'data-post="[^/]+/(\d+)".*?(?:tgme_widget_message_text|tgme_widget_message_caption)[^>]*>(.*?)</div>'
    posts = []
    for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
        post_id = int(match.group(1))
        raw_text = re.sub(r'<[^>]+>', ' ', match.group(2))
        text = re.sub(r'\s+', ' ', raw_text).strip().lower()
        if text:
            posts.append((post_id, text))
    return posts

def fetch_all_posts() -> List[Tuple[int, str]]:
    all_posts = []
    next_url = BASE_URL
    oldest_id = None
    pages = 0
    while len(all_posts) < POSTS_LIMIT and pages < 25:
        pages += 1
        html = fetch_page(next_url)
        posts = extract_posts(html)
        if not posts:
            break
        existing_ids = {p[0] for p in all_posts}
        for pid, ptext in posts:
            if pid not in existing_ids:
                all_posts.append((pid, ptext))
        current_oldest = min(p[0] for p in posts)
        if current_oldest == oldest_id:
            break
        oldest_id = current_oldest
        next_url = f"{BASE_URL}?before={oldest_id}"
        time.sleep(0.8)
    all_posts.sort(key=lambda x: x[0])
    return all_posts[-POSTS_LIMIT:]

def is_advertisement(text: str) -> bool:
    text_lower = text.lower()
    for word in STOP_WORDS:
        if word in text_lower:
            return True
    return False

def classify_message(text: str):
    # Глобальный отбой БПЛА
    if re.search(r'отбой.*бпла.*всех.*регион|снята угроза бпла во всех регионах|отбой опасности по бпла во всех ранее объявленных регионах', text):
        return ('globalCancelDrone', None)

    # Отбой – расширенный набор паттернов
    cancel_pattern = r'(?<![а-я])отбой(?![а-я])|снят[ао]|завершен[ао]|отменен[ао]|нет\s*угрозы|угроза\s*снят[ао]|отбой\s*опасности'
    is_cancel = re.search(cancel_pattern, text)
    if is_cancel:
        cancel_rocket = re.search(r'ракетн(?:ая|ую|ой|ая)\s*опасность\s*отменен|отбой\s*ракетн', text)
        cancel_drone = re.search(r'отбой\s*бпла|снят[ао]\s*бпла|отбой\s*опасности\s*бпла|опасность\s*бпла\s*снят[ао]|отбой\s*угрозы\s*бпла', text)
        if cancel_rocket:
            return ('cancel', 'rocket')
        if cancel_drone:
            return ('cancel', 'drone')
        return ('cancel', 'all')

    # Тревоги
    is_rocket = re.search(r'ракетн(?:ая|ую|ой|ая)\s*(?:опасность|тревога)|баллистическ(?:ая|ую)|крылат(?:ая|ую)', text)
    is_drone_danger = re.search(r'бпла|беспилотн(?:ик|ый|ая)|опасность\s*бпла|угроза\s*бпла', text)
    is_fixation = re.search(r'фиксаци[яи]|работа\s*пво|пво\s*работает|заходит группа|сбитие|тревога\s*бпла', text)

    if is_rocket:
        return ('alert', 'rocket')
    if is_fixation:
        return ('alert', 'droneAlert')
    if is_drone_danger:
        return ('alert', 'droneDanger')
    return (None, None)

def get_affected_regions(text: str) -> List[str]:
    matched = []
    for official, keywords in REGION_ALIASES.items():
        if any(kw in text for kw in keywords):
            matched.append(official)
    return matched

def apply_timeout(state: Dict[str, Dict]):
    now = datetime.now(timezone.utc)
    timeout = timedelta(hours=1)
    for region, st in state.items():
        if st.get("droneAlert", False) and "droneAlert_time" in st:
            try:
                alert_time = datetime.fromisoformat(st["droneAlert_time"])
                if now - alert_time > timeout:
                    st["droneAlert"] = False
                    st["droneDanger"] = True
                    del st["droneAlert_time"]
                    print(f"[{region}] Автоматический переход из droneAlert в droneDanger (истек час)")
            except Exception as e:
                print(f"Ошибка разбора времени для {region}: {e}")

# ---------- ОТПРАВКА СООБЩЕНИЙ ----------
def send_telegram_message(text: str, chat_id=None):
    if chat_id is None:
        chat_id = os.getenv("CHAT_ID")
        if not chat_id:
            print("CHAT_ID не задан, сообщение не отправлено")
            return
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("BOT_TOKEN не задан")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    for attempt in range(3):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                return
            else:
                print(f"Ошибка отправки (попытка {attempt+1}): {resp.text}")
                time.sleep(2)
        except Exception as e:
            print(f"Исключение при отправке (попытка {attempt+1}): {e}")
            time.sleep(2)
    print("Не удалось отправить сообщение после 3 попыток")

# ---------- НОВЫЙ СТИЛЬ ОТПРАВКИ (без кнопки "Источник") ----------
def send_pending_changes(pending_changes: Dict[Tuple[str, str], Tuple[int, bool]], previous_state: Dict[str, Dict]):
    """
    Отправляет все изменения в красивом оформлении, с эмодзи и временем.
    """
    if not pending_changes:
        return

    # Сортируем по post_id
    sorted_changes = sorted(pending_changes.items(), key=lambda item: item[1][0])

    for (region, change_type), (post_id, new_value) in sorted_changes:
        time_str = get_moscow_time()

        if change_type == 'rocket':
            if new_value:
                msg = (
                    f"🚨🚨🚨 <b>РАКЕТНАЯ ОПАСНОСТЬ</b> 🚨🚨🚨\n"
                    f"📍 <b>Регион:</b> {region}\n"
                    f"🕒 <b>Время:</b> {time_str} (МСК)\n"
                    f"📢 Просьба не паниковать!\n"
                )
            else:
                msg = (
                    f"✅✅✅ <b>ОТБОЙ РАКЕТНОЙ ОПАСНОСТИ</b> ✅✅✅\n"
                    f"📍 <b>Регион:</b> {region}\n"
                    f"🕒 <b>Время:</b> {time_str} (МСК)\n"
                    f"Ситуация стабилизирована.\n"
                )
        elif change_type == 'droneAlert':
            if new_value:
                msg = (
                    f"🛸🛸🛸 <b>ФИКСАЦИЯ БПЛА / РАБОТА ПВО</b> 🛸🛸🛸\n"
                    f"📍 <b>Регион:</b> {region}\n"
                    f"🕒 <b>Время:</b> {time_str} (МСК)\n"
                    f"⚠️ Будьте внимательны!\n"
                )
            else:
                msg = (
                    f"✅✅✅ <b>СНЯТА ФИКСАЦИЯ БПЛА</b> ✅✅✅\n"
                    f"📍 <b>Регион:</b> {region}\n"
                    f"🕒 <b>Время:</b> {time_str} (МСК)\n"
                )
        elif change_type == 'droneDanger':
            if new_value:
                msg = (
                    f"⚠️⚠️⚠️ <b>УГРОЗА БПЛА</b> ⚠️⚠️⚠️\n"
                    f"📍 <b>Регион:</b> {region}\n"
                    f"🕒 <b>Время:</b> {time_str} (МСК)\n"
                    f"🔴 Примите меры предосторожности!\n"
                )
            else:
                msg = (
                    f"✅✅✅ <b>ОТБОЙ УГРОЗЫ БПЛА</b> ✅✅✅\n"
                    f"📍 <b>Регион:</b> {region}\n"
                    f"🕒 <b>Время:</b> {time_str} (МСК)\n"
                    f"Угроза миновала.\n"
                )
        else:
            continue

        # Добавляем разделитель (без ссылки)
        msg += "\n——————————————————"

        send_telegram_message(msg)
        print(f"Отправлено: {msg.replace(chr(10), ' ')} (post_id={post_id})")

# ---------- ГЛАВНАЯ ФУНКЦИЯ ----------
def compute_status() -> Dict[str, Dict]:
    ensure_files_exist()
    
    previous_state = load_previous_state()
    processed_posts = load_processed_posts()
    
    # Инициализируем новый статус на основе предыдущего
    status = {}
    for region in REGION_ALIASES:
        if region in previous_state:
            st = previous_state[region]
            status[region] = {
                "rocket": st.get("rocket", False),
                "droneAlert": st.get("droneAlert", False),
                "droneDanger": st.get("droneDanger", False)
            }
            if "droneAlert_time" in st:
                status[region]["droneAlert_time"] = st["droneAlert_time"]
        else:
            status[region] = {"rocket": False, "droneAlert": False, "droneDanger": False}
    
    # Словарь для отложенных изменений: (region, change_type) -> (post_id, new_value)
    pending_changes = {}
    
    posts = fetch_all_posts()
    print(f"Загружено постов: {len(posts)}")
    
    new_processed = set(processed_posts)
    
    for pid, text in posts:
        if pid in processed_posts:
            continue
        
        if is_advertisement(text):
            print(f"[{pid}] Пропущено (реклама/информация): {text[:50]}...")
            new_processed.add(pid)
            continue
        
        msg_type, subtype = classify_message(text)
        if msg_type == 'globalCancelDrone':
            # Сбрасываем все БПЛА статусы для всех регионов
            for region in REGION_ALIASES:
                status[region]["droneAlert"] = False
                status[region]["droneDanger"] = False
                if "droneAlert_time" in status[region]:
                    del status[region]["droneAlert_time"]
                # Запоминаем изменения
                if previous_state.get(region, {}).get("droneAlert", False) != False:
                    pending_changes[(region, 'droneAlert')] = (pid, False)
                if previous_state.get(region, {}).get("droneDanger", False) != False:
                    pending_changes[(region, 'droneDanger')] = (pid, False)
            # Отправляем общее сообщение о глобальном отбое
            send_telegram_message("🌐 <b>Глобальный отбой угрозы БПЛА во всех регионах!</b>")
            new_processed.add(pid)
            continue
        
        regions = get_affected_regions(text)
        if not regions:
            new_processed.add(pid)
            continue
        
        if msg_type == 'cancel':
            for reg in regions:
                if subtype == 'rocket':
                    old_val = status[reg].get("rocket", False)
                    if old_val != False:
                        status[reg]["rocket"] = False
                        pending_changes[(reg, 'rocket')] = (pid, False)
                elif subtype == 'drone':
                    old_alert = status[reg].get("droneAlert", False)
                    old_danger = status[reg].get("droneDanger", False)
                    if old_alert != False:
                        status[reg]["droneAlert"] = False
                        if "droneAlert_time" in status[reg]:
                            del status[reg]["droneAlert_time"]
                        pending_changes[(reg, 'droneAlert')] = (pid, False)
                    if old_danger != False:
                        status[reg]["droneDanger"] = False
                        pending_changes[(reg, 'droneDanger')] = (pid, False)
                elif subtype == 'all':
                    old_rocket = status[reg].get("rocket", False)
                    old_alert = status[reg].get("droneAlert", False)
                    old_danger = status[reg].get("droneDanger", False)
                    if old_rocket != False:
                        status[reg]["rocket"] = False
                        pending_changes[(reg, 'rocket')] = (pid, False)
                    if old_alert != False:
                        status[reg]["droneAlert"] = False
                        if "droneAlert_time" in status[reg]:
                            del status[reg]["droneAlert_time"]
                        pending_changes[(reg, 'droneAlert')] = (pid, False)
                    if old_danger != False:
                        status[reg]["droneDanger"] = False
                        pending_changes[(reg, 'droneDanger')] = (pid, False)
            new_processed.add(pid)
        
        elif msg_type == 'alert':
            for reg in regions:
                if subtype == 'rocket':
                    old_val = status[reg].get("rocket", False)
                    if old_val != True:
                        status[reg]["rocket"] = True
                        pending_changes[(reg, 'rocket')] = (pid, True)
                elif subtype == 'droneAlert':
                    old_val = status[reg].get("droneAlert", False)
                    if old_val != True:
                        status[reg]["droneAlert"] = True
                        status[reg]["droneDanger"] = False
                        status[reg]["droneAlert_time"] = datetime.now(timezone.utc).isoformat()
                        pending_changes[(reg, 'droneAlert')] = (pid, True)
                        # Если был droneDanger, снимаем его
                        if status[reg].get("droneDanger", False):
                            status[reg]["droneDanger"] = False
                            pending_changes[(reg, 'droneDanger')] = (pid, False)
                elif subtype == 'droneDanger':
                    old_val = status[reg].get("droneDanger", False)
                    if old_val != True:
                        status[reg]["droneDanger"] = True
                        pending_changes[(reg, 'droneDanger')] = (pid, True)
                        # Если был droneAlert, снимаем его
                        if status[reg].get("droneAlert", False):
                            status[reg]["droneAlert"] = False
                            if "droneAlert_time" in status[reg]:
                                del status[reg]["droneAlert_time"]
                            pending_changes[(reg, 'droneAlert')] = (pid, False)
            new_processed.add(pid)
        else:
            # Не распознано – помечаем как обработанное
            new_processed.add(pid)
    
    # Применяем тайм-аут (автоматически, без отправки уведомлений)
    apply_timeout(status)
    
    # Отправляем все накопленные изменения в хронологическом порядке
    send_pending_changes(pending_changes, previous_state)
    
    # Сохраняем состояние и обработанные посты
    save_alerts(status)
    save_processed_posts(new_processed)
    
    return status

if __name__ == "__main__":
    print("Запуск парсинга...")
    status = compute_status()
    print("Парсинг завершён.")

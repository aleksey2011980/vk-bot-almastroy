from flask import Flask, request, Response
import json
import os
import requests
import time
import re

app = Flask(__name__)

# Настройки
CONFIRMATION_TOKEN = '112293f8'
SECRET_KEY = 'alma123secret'
GROUP_ID = '70382509'

# Этапы анкеты
WELCOME_FORM = (
    "Здравствуйте!\n"
    "Мы занимаемся строительством и ремонтом в Анапе и Анапском районе.\n\n"
    "Пожалуйста, отправьте нам данные для связи (обязательно):\n"
    "— Ваше имя (обязательно)\n"
    "— Телефон (обязательно)\n"
    "— Район или адрес\n"
    "— Что нужно: ремонт, строительство, смета?\n\n"
    "Мы ответим вам в ближайшее время!"
)

MISSING_DATA_MESSAGE = (
    "Пожалуйста, укажите имя и номер телефона, чтобы мы могли с вами связаться.\n"
    "Это необходимо для обработки заявки."
)

FINAL_MESSAGE = "Спасибо! Мы вам ответим в ближайшее время."

user_last_time = {}
user_asked = {}
user_thanked = {}

@app.route('/', methods=['POST'])
def vk_callback():
    data = json.loads(request.data)
    print(f"Получен запрос: {data}")

    if 'secret' in data and data['secret'] != SECRET_KEY:
        return 'invalid secret'

    if data['type'] == 'confirmation':
        return Response(CONFIRMATION_TOKEN, content_type='text/plain')

    elif data['type'] == 'message_new':
        user_id = data['object']['message']['from_id']
        message_text = data['object']['message'].get('text', '').strip()
        now = time.time()

        # Если прошло больше 10 минут — сбрасываем статус анкеты
        if user_id in user_last_time and now - user_last_time[user_id] >= 600:
            user_asked.pop(user_id, None)
            user_thanked.pop(user_id, None)

        # Если пользователь ещё не получил форму
        if user_id not in user_asked:
            send_message(user_id, WELCOME_FORM)
            user_last_time[user_id] = now
            user_asked[user_id] = True
            user_thanked[user_id] = False
            return 'ok'

        # Проверка, указано ли имя и телефон
        has_phone = bool(re.search(r'\d{5,}', message_text))
        has_name = bool(re.search(r'[А-Яа-яA-Za-z]{2,}', message_text))

        if has_phone and has_name and not user_thanked.get(user_id, False):
            send_message(user_id, FINAL_MESSAGE)
            user_last_time[user_id] = now
            user_thanked[user_id] = True
            return 'ok'

        if (has_phone or has_name) and not (has_phone and has_name):
            send_message(user_id, MISSING_DATA_MESSAGE)
            return 'ok'

    return 'ok'

def send_message(user_id, message):
    access_token = os.environ.get('ACCESS_TOKEN')
    payload = {
        'user_id': user_id,
        'message': message,
        'random_id': 0,
        'access_token': access_token,
        'v': '5.131'
    }
    response = requests.post('https://api.vk.com/method/messages.send', params=payload)
    print(f"\U0001f4ec Ответ VK API: {response.status_code} — {response.text}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

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
steps = {
    1: (
        "Здравствуйте!
"
        "Мы занимаемся строительством и ремонтом в Анапе и Анапском районе.
"
        "Напишите, пожалуйста:
"
        "— Ваше имя
"
        "— Телефон
"
        "— Район или адрес
"
        "— Что нужно: ремонт, строительство, смета?
"
    )
}

FINAL_MESSAGE = "Спасибо! Мы вам ответим в ближайшее время."
user_steps = {}
user_data = {}
last_response_time = {}

@app.route('/', methods=['POST'])
def vk_callback():
    data = json.loads(request.data)
    print(f"Получен запрос: {data}")

    # Проверка секретного ключа
    if 'secret' in data and data['secret'] != SECRET_KEY:
        return 'invalid secret'

    # Подтверждение сервера
    if data['type'] == 'confirmation':
        return Response(CONFIRMATION_TOKEN, content_type='text/plain')

    # Обработка новых сообщений
    elif data['type'] == 'message_new':
        user_id = data['object']['message']['from_id']
        message_text = data['object']['message'].get('text', '').strip()
        now = time.time()

        # Проверка таймера 10 минут
        last_time = last_response_time.get(user_id, 0)
        if now - last_time < 600:
            print(f"⏳ Менее 10 минут с последнего ответа пользователю {user_id}, пропускаем")
            return 'ok'

        # Если в сообщении есть цифры (телефон), отправляем финальное сообщение
        if re.search(r'\d{5,}', message_text):
            send_message(user_id, FINAL_MESSAGE)
            last_response_time[user_id] = now
            return 'ok'

        # Сброс состояния анкеты и начало заново с вопроса "Как вас зовут?"
        user_steps[user_id] = 1
        user_data[user_id] = {}
        last_response_time[user_id] = now
        send_message(user_id, steps[1])

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
    print(f"📬 Ответ VK API: {response.status_code} — {response.text}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

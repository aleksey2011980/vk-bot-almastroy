from flask import Flask, request, Response
import json
import os
import requests

app = Flask(__name__)

# Настройки
CONFIRMATION_TOKEN = '112293f8'
SECRET_KEY = 'alma123secret'
GROUP_ID = '70382509'

# Приветственное сообщение
WELCOME_MESSAGE = (
    "Здравствуйте!\n"
    "Мы занимаемся строительством и ремонтом в Анапе и Анапском районе.\n"
    "Напишите, пожалуйста:\n"
    "— Ваше имя\n"
    "— Телефон\n"
    "— Район или адрес\n"
    "— Что нужно: ремонт, строительство, смета?\n\n"
    "Наши сайты: https://almastroi.ru | https://luxury-house.site"
)

@app.route('/', methods=['POST'])
def vk_callback():
    data = json.loads(request.data)
    print(f"Получен запрос: {data}")

    # Проверка секретного ключа
    if 'secret' in data and data['secret'] != SECRET_KEY:
        print("❌ Неверный секретный ключ")
        return 'invalid secret'

    # Подтверждение сервера
    if data['type'] == 'confirmation':
        print("✅ Подтверждение сервера")
        return Response(CONFIRMATION_TOKEN, content_type='text/plain')

    # Обработка новых сообщений
    elif data['type'] == 'message_new':
        user_id = data['object']['message']['from_id']
        print(f"📩 Новое сообщение от пользователя: {user_id}")
        send_message(user_id, WELCOME_MESSAGE)
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

    print(f"➡️ Отправка сообщения с параметрами: {payload}")
    response = requests.post('https://api.vk.com/method/messages.send', params=payload)
    print(f"📬 Ответ VK API: {response.status_code} — {response.text}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

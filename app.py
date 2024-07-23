from flask import Flask, request
import os
import time
from youbot import bot  # Make sure 'youbot.py' correctly initializes the 'bot' object from pyTelegramBotAPI
import telebot  # This is necessary to use telebot.types for deserializing JSON

WEBHOOK_URL = 'https://redmoonutubetranscriptor.onrender.com/bot'

app = Flask(__name__)

@app.route('/bot', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data(as_text=True)  # Using as_text=True to directly get string
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '!', 403

@app.route('/')
def index():
    return '<h1>The bot is running</h1>'

if __name__ == '__main__':
    bot.remove_webhook()  # Clear any previously set webhook
    time.sleep(1)  # Wait to ensure webhook is removed
    bot.set_webhook(url=WEBHOOK_URL)  # Set the new webhook for the bot
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))  # Ensure using PORT env var or default to 5000

# app.py
from flask import Flask, request
import os
from youbot import bot  # Import the bot instance

WEBHOOK_URL = 'https://redmoonutubetranscriptor.onrender.com/bot'  # Replace <your-domain> with your actual domain

app = Flask(__name__)

@app.route('/bot', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '!', 403

@app.route('/')
def index():
    return '<h1>The bot is running</h1>'

if __name__ == '__main__':
    bot.remove_webhook()
    time.sleep(1)  # Ensure the removal is processed
    response = bot.set_webhook(url=WEBHOOK_URL)
    if response:  # Log the response to see if the webhook is set successfully
        print("Webhook set successfully.")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


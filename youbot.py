import telebot
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
import logging
import csv
import os
from datetime import datetime

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_ID =os.getenv('ADMIN_ID')
LOG_CHANNEL_ID =os.getenv('LOG_CHANNEL_ID')

bot = telebot.TeleBot(API_TOKEN)

# Configure logging
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)  # Adjust to DEBUG for more info

def read_user_data():
    user_data = {}
    if os.path.exists('user_data.csv'):
        with open('user_data.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header
            for row in reader:
                user_id, premium, last_used, count = row
                user_data[int(user_id)] = {'premium': premium == 'True',
                                           'last_used': datetime.strptime(last_used, '%Y-%m-%d') if last_used else None,
                                           'count': int(count)}
    return user_data

def write_user_data(user_data):
    with open('user_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['user_id', 'premium', 'last_used', 'count'])
        for user_id, info in user_data.items():
            writer.writerow([user_id, info['premium'], info['last_used'].strftime('%Y-%m-%d') if info['last_used'] else '', info['count']])

def update_daily_usage(user_id):
    user_data = read_user_data()
    user_info = user_data.get(user_id, {'premium': False, 'last_used': None, 'count': 0})
    
    if not user_info['last_used'] or user_info['last_used'].date() < datetime.now().date():
        user_info['last_used'] = datetime.now()
        user_info['count'] = 1
    else:
        user_info['count'] += 1

    user_data[user_id] = user_info
    write_user_data(user_data)
    return user_info['count']

def extract_video_id(url):
    if 'youtube.com/watch?v=' in url:
        return url.split('v=')[-1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0]
    return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hi! I'm your YouTube Transcription Bot. 🤖\n"
                          "📌 Send me a YouTube video link to get started!\n"
                          "🆘 Use /help to see this message again.\n\n"
                          "Let's get started! 🚀\n"
                          "Developer @redmoon0x")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "📖 Help Menu:\n\n"
                          "🔗 Send me a YouTube video link, and I'll provide the transcript.\n"
                          "Commands:\n"
                          "/start - Welcome message 👋\n"
                          "/help - This help message 🆘")

@bot.message_handler(commands=['make_premium', 'revoke_premium'], func=lambda message: str(message.from_user.id) == ADMIN_ID)
def manage_premium(message):
    command, user_id = message.text.split()
    user_id = int(user_id)
    user_data = read_user_data()

    if command == '/make_premium':
        if user_id in user_data:
            user_data[user_id]['premium'] = True
            write_user_data(user_data)
            bot.reply_to(message, f"User {user_id} is now a premium member.")
        else:
            bot.reply_to(message, "User not found in records.")

    elif command == '/revoke_premium':
        if user_id in user_data and user_data[user_id]['premium']:
            user_data[user_id]['premium'] = False
            write_user_data(user_data)
            bot.reply_to(message, f"Premium status revoked for user {user_id}.")
        else:
            bot.reply_to(message, "User was not premium or not found.")

@bot.message_handler(func=lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
def fetch_transcript(message):
    chat_id = message.chat.id
    user_data = read_user_data()

    if chat_id in user_data and not user_data[chat_id]['premium'] and user_data[chat_id]['count'] >= 2 and user_data[chat_id]['last_used'].date() == datetime.now().date():
        bot.reply_to(message, "You have reached your limit for today. Please wait until tomorrow or contact @redmoon0x to become a premium member.")
        return

    update_daily_usage(chat_id)  # Update or reset count for the new day

    url = message.text
    video_id = extract_video_id(url)
    if not video_id:
        bot.reply_to(message, "Invalid YouTube link. Please send a valid YouTube video URL. ❌")
        return

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'],preserve_formatting=True)
        transcript_text = '\n'.join([item['text'] for item in transcript])
        for part in [transcript_text[i:i+4096] for i in range(0, len(transcript_text), 4096)]:
            bot.send_message(chat_id, part)
    except NoTranscriptFound:
        bot.reply_to(message, "Sorry, no transcript found for this video. 📄❌")
    except VideoUnavailable:
        bot.reply_to(message, "Sorry, this video is unavailable. 📹❌")
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        bot.reply_to(message, "Sorry, could not fetch the transcript. Please try again later. 🚫")
        bot.send_message(LOG_CHANNEL_ID, f"Error with user {chat_id}: {str(e)}")



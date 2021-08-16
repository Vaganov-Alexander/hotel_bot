import os
import telebot
import requests
from dotenv import load_dotenv, find_dotenv


def get_from_env(key):
    load_dotenv(find_dotenv())
    return os.environ.get(key)


bot = telebot.TeleBot(get_from_env('TOKEN_TELEGRAM'))


def get_location_search():
    rapid_key = get_from_env("RAPID_KEY")
    rapid_host = get_from_env("RAPID_HOST")
    url = "https://hotels4.p.rapidapi.com/locations/search"
    querystring = {"query": "Moscow", "locale": "ru_RU"}
    headers = {
        'x-rapidapi-key': rapid_key,
        'x-rapidapi-host': rapid_host,
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    print(response.text)
    return str(response.text)

def new_message(message):
    bot.send_message(message.chat.id)

@bot.message_handler(commands=['greet'])
def greet(message):
    new_message()
    bot.send_message(message.chat.id, 'greet')


@bot.message_handler(commands=['hello'])
def greet(message):
    bot.send_message(message.chat.id, 'hello')


bot.polling()

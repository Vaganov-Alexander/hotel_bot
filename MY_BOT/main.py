import os
import sys
import telebot
import logging
from find_city import find_cities, find_price_of_hotel
from dotenv import load_dotenv
from typing import Any, Optional, List
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# # # # # # # # # # # # # # # SETTINGS # # # # # # # # # # # # # # #
load_dotenv()
token = os.environ.get('TOKEN_TELEGRAM')
bot = telebot.TeleBot(token)

# # # # # # # # # # # # # # # LOGGING # # # # # # # # # # # # # # #
logger = telebot.logger
formatter = logging.Formatter('[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                              '%m-%d %H:%M:%S')
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)
logger.setLevel(logging.INFO)
ch.setFormatter(formatter)

# # # # # # # # # # # # # # # MAIN COMMANDS # # # # # # # # # # # # # # #
main_commands = {'/lowprice', '/highprice', '/bestdeal', }

# # # # # # # # # # # # # # # HELP COMMANDS # # # # # # # # # # # # # # #
help_commands = {'/start', '/help', }


# # # # # # # # # # # # # # # BOT LOGICS # # # # # # # # # # # # # # #
@bot.message_handler(content_types=['text'])
def command_handler(message: Message):
    """
    Handler for commands entered by the user
    :param message:
    :return:
    """
    if message.text in help_commands:
        if message.text == '/start':
            bot.send_message(message.from_user.id, f'Hello {message.chat.first_name}!\n'
                                                   f'I am a bot for finding hotels\n'
                                                   f'Send /help for help')
        elif message.text == '/help':
            bot.send_message(message.from_user.id,
                             f'Here are my commands:\n'
                             f'/lowprice - find hotel low price hotel\n'
                             f'/highprice - find hotel high price hotel\n'
                             f'/bestdeal - most suitable for the price and location from the center\n'
                             f'/start - launch bot\n'
                             f'/help - see bot commands\n')
    elif message.text in main_commands:
        if message.text == '/lowprice':
            bot.send_message(message.chat.id, f'Find low price hotel')
            command_handler.sorting_key = 'PRICE'
        elif message.text == '/highprice':
            bot.send_message(message.chat.id, f'Find high price hotel')
            command_handler.sorting_key = 'PRICE_HIGHEST_FIRST'
        else:
            bot.send_message(message.chat.id, f'Find most suitable for the price and location from the center')
            command_handler.sorting_key = 'DISTANCE_FROM_LANDMARK'
        bot.send_message(message.chat.id, f'Enter city to search')
        bot.register_next_step_handler(message, cities_found_list)
    else:
        bot.send_message(message.chat.id, f'Wrong command!')


def cities_found_list(message: Message):
    """
    Keyboard output with found cities
    :param message:
    :return:
    """
    cities = InlineKeyboardMarkup(row_width=1)
    cities_button = list()
    for city in find_cities(message.text):
        cities_button.append(
            InlineKeyboardButton(text=city.city_name, callback_data='='.join([city.city_name, city.city_id])))

    if cities_button:
        cities.add(*cities_button)
        bot.send_message(message.chat.id, f'Choose town in:', reply_markup=cities)
    else:
        bot.send_message(message.chat.id, 'No such city found. Re-enter')
        bot.register_next_step_handler(message, cities_found_list)


@bot.callback_query_handler(func=lambda call: True)
def amount_of_hotels(call: Any):
    """
    Hotel count handler
    :param call:
    :return:
    """
    city, amount_of_hotels.city_id = call.data.split('=')
    bot.send_message(call.message.chat.id, city)
    bot.send_message(call.message.chat.id, f'How many hotels to look for? (no more than 25)')
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    if command_handler.sorting_key == 'PRICE' or command_handler.sorting_key == 'PRICE_HIGHEST_FIRST':
        bot.register_next_step_handler(call.message, find_price)
    elif command_handler.sorting_key == 'DISTANCE_FROM_LANDMARK':
        bot.register_next_step_handler(call.message, bestdeal)


def bestdeal(message: Message, answer_hotel: Optional[List[str]] = None):
    """
    Find most suitable for the price and location from the center (/bestdeal command)
    :param message:
    :param answer_hotel:
    :return:
    """
    if answer_hotel is None:
        answer_hotel = list()
    while len(answer_hotel) < 4:
        if not message.text.isdigit():
            if len(answer_hotel) == 0:
                bot.send_message(message.chat.id, f'How many hotels to look for? (no more than 25)')
                bot.register_next_step_handler(message, bestdeal)
                return
            elif len(answer_hotel) == 1:
                bot.send_message(message.chat.id, f'Enter minimal price:')
                bot.register_next_step_handler(message, bestdeal, answer_hotel)
                return
            elif len(answer_hotel) == 3:
                bot.send_message(message.chat.id, f'Enter distance from center:')
                bot.register_next_step_handler(message, bestdeal, answer_hotel)
                return
        else:
            if len(answer_hotel) == 0 and int(message.text) > 25:
                bot.send_message(message.migrate_to_chat_id, f'How many hotels to look for? (no more than 25)')
                bot.register_next_step_handler(message, bestdeal)
                return
            answer_hotel.append(message.text)
            if len(answer_hotel) == 1:
                bot.send_message(message.chat.id, f'Enter minimal price:')
                bot.register_next_step_handler(message, bestdeal, answer_hotel)
                return
            elif len(answer_hotel) == 2:
                bot.send_message(message.chat.id, f'Enter maximal price:')
                bot.register_next_step_handler(message, bestdeal, answer_hotel)
                return
            elif len(answer_hotel) == 3:
                bot.send_message(message.chat.id, f'Enter distance from center:')
                bot.register_next_step_handler(message, bestdeal, answer_hotel)
                return
            elif len(answer_hotel) == 4:
                if int(answer_hotel[1]) > int(answer_hotel[2]):
                    answer_hotel[1], answer_hotel[2] = answer_hotel[2], answer_hotel[1]
                elif int(answer_hotel[3]) > 999:
                    answer_hotel[3] = '999'
                bestdeal.hotels_amount = answer_hotel[0]
                bestdeal.minimal_price = answer_hotel[1]
                bestdeal.maximum_price = answer_hotel[2]
                bestdeal.distance = answer_hotel[3]
                bot.send_message(message.chat.id, f'Working. looking for hotels.\nWait please!')
                hotels_array = find_price_of_hotel(amount_of_hotels.city_id,
                                                   bestdeal.hotels_amount,
                                                   command_handler.sorting_key,
                                                   bestdeal.minimal_price,
                                                   bestdeal.maximum_price,
                                                   bestdeal.distance)
                if hotels_array:
                    bot.send_message(message.chat.id, 'Well, what i found:')
                    for hotel in hotels_array:
                        bot.send_message(message.chat.id, f'{hotel.hotel_name}\n'
                                                          f'address: {hotel.hotel_address}\n'
                                                          f'distance: {hotel.distance_from_center} miles from center\n'
                                                          f'price is {hotel.hotel_price} USD')
                    break
                else:
                    bot.send_message(message.chat.id, f'Nothing found')
                    break


def find_price(message: Message):
    """
    Find low price and high price hotel (/lowprice and /highprice command)
    :param message:
    :return:
    """
    find_price.hotels_amount = message.text
    if not find_price.hotels_amount.isdigit():
        bot.send_message(message.chat.id, f'How many hotels to look for? (no more than 25)')
        bot.register_next_step_handler(message, find_price)
        return
    elif int(find_price.hotels_amount) > 25:
        bot.send_message(message.chat.id, f'How many hotels to look for? (no more than 25)')
        bot.register_next_step_handler(message, find_price)
        return
    bot.send_message(message.chat.id, f'Working. looking for hotels.\nWait please!')
    hotels_array = find_price_of_hotel(amount_of_hotels.city_id, find_price.hotels_amount,
                                       command_handler.sorting_key)
    if hotels_array:
        for hotel in hotels_array:
            bot.send_message(message.chat.id, f'{hotel.hotel_name}\n'
                                              f'address: {hotel.hotel_address}\n'
                                              f'distance: {hotel.distance_from_center} mile from center\n'
                                              f'price: {hotel.hotel_price} USD')
    else:
        bot.send_message(message.chat.id, f'Nothing found')


# # # # # # # # # # # # # # # BOT POLLING # # # # # # # # # # # # # # #
if __name__ == '__main__':
    bot.polling()

import logging
import os
from datetime import datetime
from typing import Any, Optional, List
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup as BotMarkup
from telebot.types import InlineKeyboardButton as BotButtons
from telebot.types import Message
from find_city import finding_cities, finding_hotel_price

load_dotenv()
token = os.environ.get('TOKEN_TELEGRAM')
bot = TeleBot(token)
logging.basicConfig(filename='bot_logging.log', level=logging.INFO)
log = logging.getLogger('hotels_bot')
primary_commands = {'/lowprice', '/highprice', '/bestdeal'}
simple_commands = {
    '/start': lambda message:
    bot.send_message(message.from_user.id, f'Hello {message.chat.first_name}!\n bot for search hotel'),
    '/help': lambda message:
    bot.send_message(message.from_user.id, f'/lowprice - low price hotels\n'
                                           f'/highprice - high price hotel\n'
                                           f'/bestdeal - best deal hotel\n'
                                           f'/start - start bot\n'
                                           f'/help - list of command bot\n'
                                           f'/test - test message'),
    '/test': lambda message:
    bot.send_message(message.from_user.id, f'test message {message.chat.first_name}!'),
    'hello'.lower(): lambda message:
    bot.send_message(message.from_user.id, message.text)
}


@bot.message_handler(content_types=['text'])
def execute_command(message: Message) -> None:
    """
    Обработчик команд, вводимых пользователем
    :param message:
    :return:
    """
    if message.text in simple_commands:
        simple_commands[message.text](message)
    elif message.text in primary_commands:
        if message.text == '/lowprice':
            bot.send_message(message.chat.id, f'find low price hotel')
            execute_command.sorting_key = 'PRICE'
        elif message.text == '/highprice':
            bot.send_message(message.chat.id, f'find high price hotel')
            execute_command.sorting_key = 'PRICE_HIGH_FIRST'
        else:
            bot.send_message(message.chat.id, f'find best deal hotel')
            execute_command.sorting_key = 'DISTANCE_FROM_LANDMARK'
        bot.send_message(message.chat.id, f'enter city: ')
        bot.register_next_step_handler(message, show_the_cities_list)
    else:
        bot.send_message(message.from_user.id, f'wrong command')


def show_the_cities_list(message: Message) -> None:
    """
    вывод inline клавиатуры для выбора города
    :param message:
    :return:
    """
    markup = BotMarkup(row_width=1)
    markup_buttons = list()
    for current_city in finding_cities(message.text):
        markup_buttons.append(
            BotButtons(text=current_city.city_name,
                       callback_data='='.join([current_city.city_name, current_city.city_id]))
        )

    if not markup_buttons:
        bot.send_message(message.chat.id, f'not find this city, re-enter')
        bot.register_next_step_handler(message, show_the_cities_list)
    else:
        markup.add(*markup_buttons)
        bot.send_message(message.chat.id, f'choose town in:', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def choose_hotels_amount(call: Any) -> None:
    """
    обработчик запроса с Inline клавиатуры
    :param call:
    :return:
    """
    city_name, choose_hotels_amount.city_id = call.data.split('=')
    bot.send_message(call.message.chat.id, city_name)
    bot.send_message(call.message.chat.id, f'choose of 10 hotel')
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, reply_markup=None)
    if (execute_command.sorting_key == 'PRICE'
            or execute_command.sorting_key == 'PRICE_HIGH_FIRST'):
        bot.register_next_step_handler(call.message, find_price)
    elif execute_command.sorting_key == 'DISTANCE_FROM_LANDMARK':
        bot.register_next_step_handler(call.message, best_deal)


def best_deal(message: Message, query_array: Optional[List[str]] = None) -> None:
    """
    функция для обработки команды /bestdeal
    :param message:
    :param query_array:
    :return:
    """
    if query_array is None:
        query_array = list()
    while len(query_array) < 4:
        if not message.text.isdigit():
            if len(query_array) == 0:
                bot.send_message(message.chat.id, f'pls enter digit lower than 10')
                bot.register_next_step_handler(message, best_deal)
                return
            elif len(query_array) == 1:
                bot.send_message(message.chat.id, f'enter low price digit')
                bot.register_next_step_handler(message, best_deal, query_array)
                return
            elif len(query_array) == 3:
                bot.send_message(message.chat.id, f'enter digit distance of center')
                bot.register_next_step_handler(message, best_deal, query_array)
                return
            else:
                if len(query_array) == 0 and int(message.text) > 10:
                    bot.send_message(message.migrate_to_chat_id, f'enter amount hotel, lower than 10')
                    bot.register_next_step_handler(message, best_deal)
                    return
                query_array.append(message.text)
                if len(query_array) == 1:
                    bot.send_message(message.chat.id, f'enter minimal price')
                    bot.register_next_step_handler(message, best_deal, query_array)
                    return
                elif len(query_array) == 2:
                    bot.send_message(message.chat.id, f'enter maximal price')
                    bot.register_next_step_handler(message, best_deal, query_array)
                    return
                elif len(query_array) == 3:
                    bot.send_message(message.chat.id, f'enter distance of center')
                    bot.register_next_step_handler(message, best_deal, query_array)
                    return
                elif len(query_array) == 4:
                    if int(query_array[1]) > int(query_array[2]):
                        query_array[1], query_array[2] = query_array[2], query_array[1]
                    elif int(query_array[3]) > 999:
                        best_deal.hotels_amount = query_array[0]
                        best_deal.minimal_price = query_array[1]
                        best_deal.maximum_price = query_array[2]
                        best_deal.distance = query_array[3]
                        bot.send_message(message.chat.id, f'search hotels, wait')
                        hotels_array = finding_hotel_price(choose_hotels_amount.city_id,
                                                           best_deal.hotels_amount,
                                                           execute_command.sorting_key,
                                                           best_deal.minimal_price,
                                                           best_deal.maximum_price,
                                                           best_deal.distance)
                        if hotels_array:
                            for hotel in hotels_array:
                                bot.send_message(message.chat.id, f'{hotel.hotel_name} adres: {hotel.hotel_address}'
                                                                  f'distance {hotel.distance_from_center}'
                                                                  f'km from center price is {hotel.hotel_price} RUB')
                                break
                            else:
                                bot.send_message(message.chat.id, f'not fond')
                                break


def find_price(message: Message) -> None:
    """
    функция обрабботки команд highprice lowprice
    :param message:
    :return:
    """
    find_price.hotels_amount = message.text
    if not find_price.hotels_amount.isdigit():
        bot.send_message(message.chat.id, f'pls enter digit hotel (lower than 10')
        bot.register_next_step_handler(message, find_price)
        return
    elif int(find_price.hotels_amount) > 10:
        bot.send_message(message.chat.id, f'pls enter digit hotel (lower than 10')
        bot.register_next_step_handler(message, find_price)
        return
    bot.send_message(message.chat.id, f'search hotels, wait')
    hotels_array = finding_hotel_price(choose_hotels_amount.city_id, find_price.hotels_amount,
                                       execute_command.sorting_key)
    if hotels_array:
        for hotel in hotels_array:
            bot.send_message(message.chat.id, f'{hotel.hotel_name} '
                                              f'address: {hotel.hotel_address} '
                                              f'distance: {hotel.distance_from_center} km from center '
                                              f'price: {hotel.hotel_price} RUB')
    else:
        bot.send_message(message.chat.id, f'not found')


bot.polling()

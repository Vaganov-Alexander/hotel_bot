import os
import telebot
import logging
from telebot import types
from find_city import finding_cities, finding_hotel_price
from dotenv import load_dotenv
from typing import Any, Optional, List
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
token = os.environ.get('TOKEN_TELEGRAM')
bot = telebot.TeleBot(token)
keyboard = telebot.types.ReplyKeyboardMarkup()
button1 = types.KeyboardButton("Tоп самых дешёвых отелей в городе")
button2 = types.KeyboardButton("Tоп самых дорогих отелей в городе")
button3 = types.KeyboardButton("Tоп отелей, наиболее подходящих\n по цене и расположению от центра")
keyboard.row(button1)
keyboard.row(button2)
keyboard.row(button3)

primary_commands = {'/lowprice', '/highprice', '/bestdeal'}
simple_commands = {
    '/start': lambda message:
    bot.send_message(message.from_user.id, f'Привет {message.chat.first_name}!\n Я бот для поиска отелей'),
    '/help': lambda message:
    bot.send_message(message.from_user.id, f'/lowprice - низкая цена отеля\n'
                                           f'/highprice - высокая цена отеля\n'
                                           f'/bestdeal - ближние по расположению от центра\n'
                                           f'/start - запустить бота\n'
                                           f'/help - посмотреть команды бота\n'
                                           f'/test - для тестирования бота'),
    '/test': lambda message:
    bot.send_message(message.from_user.id, f'test message {message.chat.first_name}!'),
    'hello'.lower(): lambda message:
    bot.send_message(message.from_user.id, message.text)
}


@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.send_message(message.chat.id, "Привет, я бот по путешествию)\nДля просмотра меню напиши /menu\nДля помощи напиши /help")


@bot.message_handler(commands=['help'])
def help_bots(message):
	bot.send_message(message.chat.id, 'Бот предназначен для поиска отеля в нужном для тебя городе\nДля просмотра возможностей бота напиши /menu')


@bot.message_handler(commands=['menu'])
def low_state(message):
	bot.send_message(message.chat.id, 'Вот мои возможности',reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def execute_command(message):
	if message.text == 'Tоп самых дешёвых отелей в городе' or message.text == '/lowprice':
		bot.send_message(message.chat.id, f'Поиск самых дешёвых отелей в городе')
		execute_command.sorting_key = 'PRICE'
		bot.send_message(message.chat.id, f'Введите город: ')
		bot.register_next_step_handler(message, show_the_cities_list)
	elif message.text == 'Tоп самых дорогих отелей в городе' or message.text == '/highprice':
		bot.send_message(message.chat.id, f'Поиск самых дорогих отелей в городе')
		execute_command.sorting_key = 'PRICE_HIGH_FIRST'
		bot.send_message(message.chat.id, f'Введите город: ')
		bot.register_next_step_handler(message, show_the_cities_list)
	elif message.text == 'Tоп отелей, наиболее подходящих\n по цене и расположению от центра' or message.text =='/bestdeal':
		bot.send_message(message.chat.id, f'Поиск самых дорогих отелей в городе')
		execute_command.sorting_key = 'DISTANCE_FROM_LANDMARK'
		bot.send_message(message.chat.id, f'Введите город: ')
		bot.register_next_step_handler(message, show_the_cities_list)
	else:
		bot.send_message(message.from_user.id, f'Не понимаю введите /help')


def show_the_cities_list(message: telebot.types.Message) -> None:
	markup = InlineKeyboardMarkup(row_width=1)
	markup_buttons = list()
	for current_city in finding_cities(message.text):
		markup_buttons.append(
			InlineKeyboardButton(text=current_city.city_name, callback_data='='.join([current_city.city_name, current_city.city_id])))

	if not markup_buttons:
		bot.send_message(message.chat.id, f'не нашел такого города, повторите еще раз:)')
		bot.register_next_step_handler(message, show_the_cities_list)
	else:
		markup.add(*markup_buttons)
		bot.send_message(message.chat.id, f'Выберите нужный город', reply_markup=markup)
@bot.callback_query_handler(func=lambda call: True)
def choose_hotels_amount(call) -> None:
	"""
    обработчик запроса с Inline клавиатуры
    """
	city_name, choose_hotels_amount.city_id = call.data.split('=')
	bot.send_message(call.message.chat.id, city_name)
	bot.send_message(call.message.chat.id, f'Выберите до 10 отелей')
	bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
	if (execute_command.sorting_key == 'PRICE' or execute_command.sorting_key == 'PRICE_HIGH_FIRST'):
		bot.register_next_step_handler(call.message, find_price)
	elif execute_command.sorting_key == 'DISTANCE_FROM_LANDMARK':
		bot.register_next_step_handler(call.message, best_deal)


def best_deal(message: telebot.types.Message, query_array: Optional[List[str]] = None) -> None:
	"""
Функция для обработки команды /bestdeal
    """
	if query_array is None:
		query_array = list()
	while len(query_array) < 4:
		if not message.text.isdigit():
			if len(query_array) == 0:
				bot.send_message(message.chat.id, f'Пожалуйста введите число меньше 10')
				bot.register_next_step_handler(message, best_deal)
				return
			elif len(query_array) == 1:
				bot.send_message(message.chat.id, f'Введите минимальную цену')
				bot.register_next_step_handler(message, best_deal, query_array)
				return
			elif len(query_array) == 2:
				bot.send_message(message.chat.id,f'Введите максимальную цену')
				bot.register_next_step_handler(message,best_deal,query_array)
				return
			elif len(query_array) == 3:
				bot.send_message(message.chat.id, f'Введите расстояние от центра')
				bot.register_next_step_handler(message, best_deal, query_array)
				return
		else:
			if len(query_array) == 0 and int(message.text) > 10:
				bot.send_message(message.chat.id, f'Введите кол-во отелей меньше 10')
				bot.register_next_step_handler(message, best_deal)
				return
			query_array.append(message.text)
			if len(query_array) == 1:
				bot.send_message(message.chat.id, f'Введите минимальную цену')
				bot.register_next_step_handler(message, best_deal, query_array)
				return
			elif len(query_array) == 2:
				bot.send_message(message.chat.id, f'Введите максимальную цену')
				bot.register_next_step_handler(message, best_deal, query_array)
				return
			elif len(query_array) == 3:
				bot.send_message(message.chat.id, f'Введите расстояние от центра')
				bot.register_next_step_handler(message, best_deal, query_array)
				return
			elif len(query_array) == 4:
				if int(query_array[1]) > int(query_array[2]):
					query_array[1], query_array[2] = query_array[2], query_array[1]
				elif int(query_array[3]) > 999:
					query_array[3] = '999'
				best_deal.hotels_amount = query_array[0]
				best_deal.minimal_price = query_array[1]
				best_deal.maximum_price = query_array[2]
				best_deal.distance = query_array[3]
				bot.send_message(message.chat.id, f'Идёт поиск отеля подождите:)')
				hotels_array = finding_hotel_price(choose_hotels_amount.city_id,
                                                   best_deal.hotels_amount,
                                                   execute_command.sorting_key,
                                                   best_deal.minimal_price,
                                                   best_deal.maximum_price,
                                                   best_deal.distance)
				if hotels_array:
					for hotel in hotels_array:
						bot.send_message(message.chat.id, f'{hotel.hotel_name} адрес: {hotel.hotel_address}'
                                                          f'расстояние {hotel.distance_from_center}'
                                                          f'км от центра города цена {hotel.hotel_price} RUB')
					break
				else:
					bot.send_message(message.chat.id, f'Не нашел(')
					break


def find_price(message: telebot.types.Message) -> None:
	"""
    функция обрабботки команд highprice lowprice
    """
	find_price.hotels_amount = message.text
	if not find_price.hotels_amount.isdigit():
		bot.send_message(message.chat.id, f'Пожалуйста введите кол-во отелей(меньше 10)')
		bot.register_next_step_handler(message, find_price)
		return
	elif int(find_price.hotels_amount) > 10:
		bot.send_message(message.chat.id, f'Пожалуйста введите кол-во отелей(меньше 10)')
		bot.register_next_step_handler(message, find_price)
		return
	bot.send_message(message.chat.id, f'Идёт поиск')
	hotels_array = finding_hotel_price(choose_hotels_amount.city_id, find_price.hotels_amount, execute_command.sorting_key)
	if hotels_array:
		for hotel in hotels_array:
			bot.send_message(message.chat.id, f'{hotel.hotel_name} '
                                              f'адрес: {hotel.hotel_address} '
                                              f'расстояние: {hotel.distance_from_center} км от центра'
                                              f'цена: {hotel.hotel_price} RUB')
	else:
		bot.send_message(message.chat.id, f'Не найдено')


if __name__ == '__main__':
	bot.polling()
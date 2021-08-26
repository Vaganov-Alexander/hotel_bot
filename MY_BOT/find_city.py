import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
from re import match, findall
from typing import Optional, Dict

# # # # # # # # # # # # # # # SETTINGS # # # # # # # # # # # # # # #
load_dotenv()
hotel_token = os.environ.get('RAPID_KEY')
CITY_URL = 'https://hotals4.p.rapidapi.com/locations/search'
HOTEL_URL = 'https://hotels4.p.rapidapi.com/properties/list'
headers = {
    'x-rapidapi-key': hotel_token,
    'x-rapidapi-host': 'hotels4.p.rapidapi.com',
}

check_in_day = datetime.today().date()
check_out_day = check_in_day + timedelta(days=1)


# # # # # # # # # # # # # # # CLASS CITY and HOTEL # # # # # # # # # # # # # # #
class City:
    def __init__(self, city_name: str, city_id: str) -> None:
        self.city_name = city_name
        self.city_id = city_id


class Hotel:
    def __init__(self, hotel_name: str, hotel_address: str, hotel_price: str, distance_from_center: str) -> None:
        self.hotel_name = hotel_name
        self.hotel_address = hotel_address
        self.hotel_price = hotel_price
        self.distance_from_center = distance_from_center


# # # # # # # # # # # # # # # SEARCH CITY # # # # # # # # # # # # # # #
def find_cities(city: str):
    """
    получает на вход название города делает запрос к апи и
    возвращает список из обектов класса сити куда сохраняется
    называние города ИД полученные из джосон сервера
    """
    cities_array = list()
    if len(findall(r"[а-яА-ЯЁё]", city)) > 0:
        locale = 'ru_RU'
    else:
        locale = 'en_US'

    if '-' in city:
        city = '-'.join([letter.capitalize() for letter in city.split('-')])
    else:
        city = ' '.join([letter.capitalize() for letter in city.split()])
    querystring = {'query': city, 'locale': locale}
    find_city_request = requests.get(CITY_URL, headers=headers, params=querystring)
    suggestion_array = json.loads(find_city_request.text)['suggestions']
    for current_suggestion in suggestion_array:
        if current_suggestion.get('group') == 'CITY_GROUP':
            suggestion_array = current_suggestion['entities']
            break
    for current_city in suggestion_array:
        city_name = current_city.get('caption').replace("<span "
                                                        "class='highlighted'>",
                                                        '').replace("</span>",
                                                                    '')

        if current_city.get('type') == 'CITY' and city_name.startswith(city):
            if locale == 'ru_RU':
                cities_array.append(City(city_name.split(', ')[0] + ', ' + city_name.split(', ')[-1],
                                         current_city.get('destinationId')))
            else:
                cities_array.append(City(city_name, current_city.get('destinationId')))
    return cities_array


# # # # # # # # # # # # # # # SEARCH PRICE # # # # # # # # # # # # # # #
def find_price_of_hotel(destination_id: str,
                        page_size: str, sorting_key: str,
                        minimal_price: Optional[str] = None,
                        maximum_price: Optional[str] = None,
                        distance: str = '999'):
    """
    получает на вход ряд аргументов из которых формирует параметры для запроса к апи отелей
    и выдачи списка из объектов Hotel в которых сохранены данные о названии отел, адресе,
    цене за номер и расстояние до центра
    """
    request_parameters: Dict = {
        'adults1': '1',
        'pageNumber': '1',
        'destinationId': destination_id,
        'pageSize': page_size,
        'checkOut': str(check_out_day),
        'checkIn': str(check_in_day),
        'sortOrder': sorting_key,
        'locale': 'ru_RU',
        'currency': 'USD',
        'priceMax': maximum_price,
        'priceMin': minimal_price,
        'landmarkIds': 'City center',
    }

    find_hotel_request = requests.get(HOTEL_URL, headers=headers, params=request_parameters)
    results_array = \
        json.loads(find_hotel_request.text)['data']['body']['searchResults']['results']
    hotels_array = list()
    for current_hotel in results_array:
        hotel_name = current_hotel.get('name')
        hotel_address = current_hotel.get('address').get('streetAddress')
        hotel_price = current_hotel.get('ratePlan').get('price').get('exactCurrent')
        hotel_distance = "".join(symbol for symbol in
                                 current_hotel.get('landmarks')[0].get(
                                     'distance')
                                 if match(r"[0-9,.]", symbol)).replace(',', '.')
        hotel_distance = str(round(float(hotel_distance) * 1.6, 2))
        if float(distance) >= float(hotel_distance):
            hotels_array.append(
                Hotel(hotel_name, hotel_address, hotel_price, hotel_distance))
    if sorting_key == 'DISTANCE_FROM_LANDMARK':
        hotels_array = sorted(hotels_array, key=lambda hotel: hotel.hotel_price)

    return hotels_array

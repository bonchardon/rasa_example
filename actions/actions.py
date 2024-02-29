from typing import Any, Text, Dict, List
from rasa_sdk.events import SlotSet, Form
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from num2words import num2words
import json
import ssl
import graypy
from urllib.request import urlopen
ssl._create_default_https_context = ssl._create_unverified_context
# from actions.names import *
import requests

import pymorphy2
from transliterate import translit
from num2words import num2words
import spacy
import re
import json
import psycopg2


def names_changed(name):
    morph = pymorphy2.MorphAnalyzer(lang='uk')
    forms = morph.parse(name)

    try:
        if name == 'Ксюша':
            return 'Ксеніє'
        elif name == 'Енн':
            return 'Анно'
        elif name == 'Юлія':
            return 'Юліє'
        elif name == 'Юлій':
            return 'Юлію'
        elif name == 'Анастасія':
            return 'Анастасіє'
        elif name == 'Леся' or name == 'Лесь':
            return 'Лесю'
        elif name == 'Костя':
            return 'Костю'
        elif name == 'Федя':
            return 'Федю'
        elif name == 'Август':
            return 'Августе'
        elif name == 'Ярослава':
            return 'Ярославо'
        elif name == 'Адам':
            return 'Адаме'
        elif name == 'Аристарх':
            return 'Аристарху'
        elif name == 'Ая':
            return 'Ає'
        elif name == 'Тиміш':
            return 'Тимоше'
        elif name == 'Дорош':
            return 'Дороше'
        elif name == 'Лукаш':
            return 'Лукаше'
        else:
            voc_case = forms[0].inflect({'voct'}).word
            return voc_case.capitalize()
    except AttributeError:
        return ''


def balance_words(nums):
    one_uah = ' одна гривня '
    one_kop = 'одна копійка'

    two_uah = ' дві гривні '
    two_kop = 'дві копійки'

    three_uah = ' три гривні '
    three_kop = 'три копійки'

    four_uah = ' чотири гривні '
    four_kop = 'чотири копійки'
    a, b = map(int, nums.split(".", 1))

    # hrvns and kopiikas
    HRVNIA = num2words(str(a), lang='uk')
    KOPIIKA = num2words(str(b), lang='uk')

    rate = ''

    # Гривня
    if str(a)[-1] == '11' or str(a)[1] == '12' \
                    or str(a)[1] == '13' or str(a)[1] == '14':
                rate += HRVNIA + ' гривень '
    elif str(a)[-1] == '1':
                rate += HRVNIA[:len(HRVNIA) - 5] + one_uah
    elif str(a)[-1] == '2':
                rate += HRVNIA[:len(HRVNIA) - 3] + two_uah
    elif str(a)[-1] == '3':
                rate += HRVNIA[:len(HRVNIA) - 3] + three_uah
    elif str(a)[-1] == '4':
                rate += HRVNIA[:len(HRVNIA) - 6] + four_uah
    else:
                rate += HRVNIA + ' гривень '

    # Копійка
    if str(b)[-1] == '11' or str(b)[-1] == '12' \
                    or str(b)[-1] == '13' or str(b)[-1] == '14':
                rate += KOPIIKA + 'копійок'
    elif str(b)[-1] == '1':
                rate += KOPIIKA[:len(KOPIIKA) - 4] + one_kop
    elif str(b)[-1] == '2':
                rate += KOPIIKA[:len(KOPIIKA) - 3] + two_kop
    elif str(b)[-1] == '3':
                rate += KOPIIKA[:len(KOPIIKA) - 3] + three_kop
    elif str(b)[-1] == '4':
                rate += KOPIIKA[:len(KOPIIKA) - 6] + four_kop
    else:
                rate += KOPIIKA + ' копійок'

    return rate


def balance_words_gold(nums):
    a, b = map(int, nums.split(".", 1))

    # hrvns and kopiikas
    DOLLAR = num2words(str(a), lang='uk')
    CENTS = num2words(str(b), lang='uk')

    rate = ''

    # dollars
    if str(a)[-2:] == '11' or str(a)[-2:] == '12' \
                    or str(a)[-2:] == '13' or str(a)[-2:] == '14':
                rate += DOLLAR + ' доларів '
    elif str(a)[-1] == '1' or str(a) == '1':
                rate += DOLLAR + ' долар '
    elif str(a)[-1] == '2' or str(a)[-1] == '3' or str(a)[-1] == '4':
                rate += DOLLAR + ' долари '
    elif str(a) == '2' or str(a) == '3' or str(a) == '4':
                rate += DOLLAR + ' долари '
    else:
                rate += DOLLAR + ' доларів '

    # cents
    if str(b)[-2:] == '11' or str(b)[-2:] == '12' \
            or str(b)[-2:] == '13' or str(b)[-2:] == '14':
        rate += CENTS + ' центів '
    elif str(b)[-1] == '1' or str(b) == '1':
        rate += CENTS + ' цент '
    elif str(b)[-1] == '2' or str(b)[-1] == '3' or str(b)[-1] == '4':
        rate += CENTS + ' центи '
    elif str(b) == '2' or str(b) == '3' or str(b) == '4':
        rate += CENTS + ' центи '
    else:
        rate += CENTS + ' центів '

    return rate


def convert_written_numbers(text):
    written_to_numeric = {
        'адин': "1",
        'четире': '4',
        'пять': '5',
        "п'ять": '5',
        'шесть': '6',
        'семь': '7',
        'восемь': '8',
        'девять': '9',
        "дев'ять": '9',
        'ноль': '0',
    }

    # Convert written number words to numeric values
    for word, num in written_to_numeric.items():
        text = re.sub(rf"\b{word}\b", num, text)

    return text


def get_token(link) -> str:
    post_url = link
    post_data = {
        "credential": "cred1",
        "principal": "cred2"
    }
    post_headers = {
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    response = requests.post(post_url, data=json.dumps(post_data), headers=post_headers, verify=False)

    if response.status_code == 200:
        return response.json().get('token')
    else:
        return None


def get_data_with_token(link, token: str, user_phone: int) -> List[Dict[Text, Any]]:
    get_url = f"{link}{user_phone}"
    get_headers = {
        "Authorization": f"Bearer {token}"
    }
    post_data = {
        "credential": "cred1",
        "principal": "cred2"
    }

    response = requests.get(get_url, data=json.dumps(post_data), headers=get_headers, verify=False)

    if response.status_code == 200:
        return response.json()
    else:
        return []


class ActionCurrencyRate(Action):

    def name(self) -> Text:
        return "action_currency_rate"

    def format_currency(self, amount: int, currency_name: str) -> str:
        hrn = num2words(amount, lang='uk')
        kop = num2words(amount % 100, lang='uk')
        if amount == 1:
            hrn_word = "гривня"
            kop_word = "копійка"
        elif 2 <= amount <= 4:
            hrn_word = "гривні"
            kop_word = "копійки"
        else:
            hrn_word = "гривень"
            kop_word = "копійок"
        return f"Курс {currency_name} — {hrn} {hrn_word} {kop} {kop_word}."

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        path = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json'
        page = urlopen(path)
        html_bytes = page.read()
        html = html_bytes.decode("utf-8")
        currency_data = json.loads(html)

        currency_messages = []

        for i in currency_data:
            if i['cc'] == 'USD':
                currency_messages.append(self.format_currency(int(i['rate']), 'долара'))
            elif i['cc'] == 'EUR':
                currency_messages.append(self.format_currency(int(i['rate']), 'євро'))
            elif i['cc'] == 'GBP':
                currency_messages.append(self.format_currency(int(i['rate']), 'фунта стерлінгів'))

        for message in currency_messages:
            dispatcher.utter_message(text=message)

        return []


class ActionHello(Action):

    def name(self) -> Text:
        return "action_convert_name_hello"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:
        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)
        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(text=f'Вітаю Вас, {converted_name}! Буду рада вам допомогти!')
            else:
                 dispatcher.utter_message(text=f'Вітаю Вас! Буду рада вам допомогти!')
        except:
            dispatcher.utter_message(text="На жаль, не зрозуміла ваше привітання. Повторіть будь ласка.")
        
        return []


class UtterStartAction(Action):

    def name(self) -> Text:
        return "action_convert_name_utter_start"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        # бот повинен вітатися, прощатися і просто звертатися до користувача по імені в кличному відмінку.
        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7708

        
        token = get_token()
        data = get_data_with_token(token, user_phone)

        if data:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(text=f'{converted_name}, вас вітає демонстраційний бот компанії Смідл, сформулюйте будь ласка ваш запит, наприклад: передати показники лічильників, перевірити баланс, закрити картку або турбують проблеми з карткою.')
            else: 
                 dispatcher.utter_message(text=f'Вас вітає демонстраційний бот компанії Смідл, сформулюйте будь ласка ваш запит, наприклад: передати показники лічильників, перевірити баланс, закрити картку або турбують проблеми з карткою.')
        else:
            dispatcher.utter_message(text="Вас вітає демонстраційний бот компанії Смідл, сформулюйте будь ласка ваш запит, наприклад: передати показники лічильників, перевірити баланс, закрити картку або турбують проблеми з карткою.")

        return []


class ActionPrintLastTurnInfo(Action):
    def name(self) -> Text:
            return "action_print_last_turn_info"

    def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # WRITING THE WHOLE THINK TO THE .TXT FILE
        import os
        if not os.path.isfile('chats.txt'):
            with open('chats.txt', 'w') as file:
                # file.write("intent,user_input,entity_name,entity_value,action,bot_reply\n")
                file.write('Our dialogue:\n')

        # LOG PART
        my_logger = logging.getLogger('smd-nlu-logger')
        my_logger.setLevel(logging.DEBUG)

        handler = graypy.GELFUDPHandler('10.100.70.245', 12201)
        my_logger.addHandler(handler)

        # Retrieve the last user turn
        last_user_turn = tracker.get_last_event_for('user')

        # Retrieve the intent and user message text of the last user turn
        last_intent = last_user_turn.get('parse_data').get('intent').get('name')
        last_message_text = last_user_turn.get('text')

        # Retrieve the recognized entities of the last user turn
        entities = last_user_turn.get('parse_data').get('entities')
        recognized_entities = [(entity.get('entity'), entity.get('value')) for entity in entities]

        # Retrieve the bot's utterances for the last turn
        bot_utterances = tracker.get_last_event_for('bot')

        utterance_names = []
        utterance_texts = []

        if bot_utterances:
            if isinstance(bot_utterances, list):
                for utterance in bot_utterances:
                    utterance_names.append(utterance.get('name'))
                    utterance_texts.append(utterance.get('text'))
            else:
                utterance_names.append(bot_utterances.get('name'))
                utterance_texts.append(bot_utterances.get('text'))

        # Retrieve the name of the last custom action triggered
        last_custom_action = tracker.get_last_event_for('action')
        utter_name = last_custom_action.get('name') if last_custom_action else "None"

        chat_data = ''

        # print("Intent: ", last_intent)
        last_intent = "Intent: " + last_intent
        my_logger.debug(last_intent)
        chat_data += last_intent + '\n'

        # print("User Message Text: ", last_message_text)
        last_message_text = "User Message Text: " + last_message_text
        my_logger.debug(last_message_text)
        chat_data += last_message_text + '\n'

        # print("Recognized Entities:")
        my_logger.debug("Recognized Entities:")
        chat_data += "Recognized Entities:" + '\n'

        for entity_name, entity_value in recognized_entities:
            # print(" - Name: ", entity_name, "Value: ", entity_value)
            ents = [" - Name: ", entity_name, '\n', " - Value: ", entity_value, '\n']
            my_logger.debug(str(ents))

            chat_data += "".join(ents)

        # print("Bot Utterances:")
        my_logger.debug("Bot Utterances:")
        chat_data += "Bot Utterances:" + '\n'

        for i in range(len(utterance_names)):
            # print(" - Name: ", utter_name, '\n', " - Text: ", utterance_texts[i])
            utters = [" - Name: ", utter_name, '\n', " - Text: ", utterance_texts[i], '\n']
            my_logger.debug(utters)
            chat_data += ''.join(utters)

            # need to be sure so that every custom actions STARTS WITH 'action'; if not this code will not apply
            if utter_name.split('_')[0] == 'action':
                # print('Custom action: ', utter_name)
                custom_utters = ['Custom action: ', utter_name, '\n']
                my_logger.debug(custom_utters)

                chat_data += ''.join(custom_utters)

        my_logger.debug('\n')
        chat_data += '\n'
        # print(chat_data)

        with open('chats.txt', 'a') as file:
            file.write(chat_data)

        return []

    # def write_to_database(self, intent, user_text, recognized_entities, utterance_names, utterance_texts, utter_name):
    #     # psql -h localhost -U your_username -d rasa_db -W 
    #     db_params = {
    #         'host': 'localhost',
    #         'database': 'rasa_db',  # Update with your actual database name
    #         'user': 'your_username',  # Update with your actual database username
    #         'password': 'your_password'
    #     }

    #     # Connect to the database
    #     connection = psycopg2.connect(**db_params)
    #     cursor = connection.cursor()

    #     # Insert data into the database
    #     cursor.execute(
    #         "INSERT INTO conversation_data (intent, user_text, recognized_entities, bot_name, bot_text) "
    #         "VALUES (%s, %s, %s, %s, %s)",
    #         (intent, user_text, str(recognized_entities), utter_name, str(utterance_texts)))

    #     # Commit the changes and close the connection
    #     connection.commit()
    #     cursor.close()
    #     connection.close()


class UtterCardNotWorkingAction(Action):

    def name(self) -> Text:
        return "action_convert_name_utter_card_not_working"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)

        # user_phone = 7722

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        if data:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(
                    text=f'{converted_name}, вашу карту для виплат було заблоковано, оскільки ми зафіксували підозрілу активність по ній. Зачекайте будь ласка на з\'єднання з оператором.')
            else:
                 dispatcher.utter_message(
                    text=f'Вашу карту для виплат було заблоковано, оскільки ми зафіксували підозрілу активність по ній. Зачекайте будь ласка на з\'єднання з оператором.')
        else:
            dispatcher.utter_message(text="Трапилась проблема із картою. Повторіть будь ласка для уточнення пробелми.")

        return []


class UtterByeAction(Action):

    def name(self) -> Text:
        return "action_convert_name_utter_bye"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)

        # user_phone = 7722

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(
                    text=f'До зв\'язку, {converted_name}!')
            else:
                 dispatcher.utter_message(
                    text=f'До побачення! Було приємно із вами поспілкуватися')

        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Не зрозуміла вас! Повторіть ваш запит будь ласка!")

        return []


# баланс по картці голд
class BalanceGoldAction(Action):
    def name(self) -> Text:
        return "action_balance_gold"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)

        # user_phone = 7722

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)
        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                data_balance = data[0].get('c_gold_balance')
                print('DATA BALANCE: ', data_balance)
                data_balance = balance_words_gold(str(data_balance))
            
                dispatcher.utter_message(text=f'{converted_name}, баланс по вашій картці Голд складає {data_balance}. '
                                          f'Чим ще ми можемо вам допомогти?')
            else:
                dispatcher.utter_message(text=f'Трапилась помилка! Ми вже працюємо над її усуненням.')
        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Не зрозуміла вас! Повторіть ваш запит будь ласка!")

        return []


# баланс по картці стандарт
class BalanceStandardAction(Action):
    def name(self) -> Text:
        return "action_balance_standard"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)

        # user_phone = 7722

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)
        if data:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                data_balance = data[0].get('c_standard_balance')
                data_balance = balance_words(str(data_balance))
            
                dispatcher.utter_message(text=f'{converted_name}, баланс по вашій картці Стандарт складає {data_balance}. '
                                          f'Чим ще ми можемо вам допомогти?')
            else:
                dispatcher.utter_message(text=f'Трапилась помилка! Ми вже працюємо над її усуненням.')
        else:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Не зрозуміла вас! Повторіть ваш запит будь ласка!")
            
        return []


class ActionWeather(Action):
    def name(self) -> Text:
        return "action_weather"

    def get_weather_data(self, city_name: str) -> List[Any]:

        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city_name,
            "appid": '094e29c639d77a117075ef7e6c489c7f',
            "lang": "uk",
            "units": "metric"
        }

        response = requests.get(base_url, params)
        print(response.status_code)

        weather_data = response.json()

        weather_data_real = num2words(int(weather_data['main']['temp']), lang='uk')
        weather_data_feels = num2words(int(weather_data['main']['feels_like']), lang='uk')
        # description of the weather
        description = weather_data['weather'][0]['description']

        # HERE we get all the needed data for further implementation wicj is
        # 1) result[0] ==> just basic weather data
        # 2) result[1] ==> weather the way it feels like (we use it ONLY if result[0] and result[1] are different)
        # 3) result[2] ==> description of the weather (in uk), such as 'рвані хмари', 'сонячно', 'хмарно'
        # 4) result[3] ==> OUR RESPONSE FROM THE SERVER (200 -- OK, 404 -- nothing works, so we seek another solution)

        results = [weather_data_real, weather_data_feels, description, response]
        return results

    def cases_for_weather_data(self, weather: str):

        weather_words = weather.split()

        # (2)5 - градуси, (2)5 - градусів, (2)6 - градусів, (2)7 - градусів, (2)8 - градусів, (2)9 - градусів

        if len(weather_words) == 2 and weather_words[1] == 'один' \
                or len(weather_words) == 1 and weather_words[0] == 'один':
            return ' '.join(weather_words) + ' градус'
        elif len(weather_words) == 2 and weather_words[1] == 'два' or len(weather_words) == 1 and weather_words[0] == 'два'\
                or len(weather_words) == 2 and weather_words[1] == 'три' or len(weather_words) == 1 and weather_words[0] == 'три'\
                or len(weather_words) == 2 and weather_words[1] == 'чотири' or len(weather_words) == 1 and weather_words[0] == 'чотири':
            return ' '.join(weather_words) + ' градуси'

        else:
            return ' '.join(weather_words) + ' градусів'

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        morph = pymorphy2.MorphAnalyzer(lang="uk")

        # all exceptions
        exceptions_kyiv = ['Києва', 'Київ', 'Києві', 'Київська', 'Кийов']
        exceptions_ryga = ['Рига', 'Ризі' 'Ригі']
        exceptions_lviv = ['Львові', 'Льові', 'місті Лева', 'Леві', '']
        exceptions_franyk = ['франику', 'івано франківськ', 'івано франківську', 'іване франківськ', 'іван франківську']

        try:
            # var1
            last_user_turn = tracker.get_last_event_for('user')
            entities = last_user_turn.get('parse_data').get('entities')
            if entities[0]['value'] in exceptions_kyiv:
                entities = 'Київ'
            elif entities[0]['value'] in exceptions_ryga:
                entities = 'Рига'
            elif entities[0]['value'] in exceptions_lviv:
                entities = 'Львів'
            elif entities[0]['value'] in exceptions_franyk:
                entities = 'Івано-Франківськ'
            else:
                entities = entities[0]['value']
            print(entities)
        except IndexError:
            print('IndexError, try more.')

        # here we catch our error (need answer 200; however, if we get 404, the code will go on)
        try:
            resp = self.get_weather_data(entities)
            resp = resp[3].status_code
        except KeyError:
            resp = 404

        try:
            if resp == 200:

                city_name = entities
                print(city_name)

                base = self.get_weather_data(city_name)
                simple_weather = base[0]
                more_info_weather = base[1]
                type_weather = base[2]

                if simple_weather != more_info_weather:
                    dispatcher.utter_message(
                        text=f'Дякую за точний запит! Погода у місті {city_name} сьгодні {type_weather}. Температура у місті {city_name} {self.cases_for_weather_data(simple_weather)} за Цельсієм, але відчувається як {self.cases_for_weather_data(more_info_weather)}.')
                else:
                    dispatcher.utter_message(
                        text=f'Дякую за точний запит! Погода у місті {city_name} сьгодні {type_weather}. Температура у місті {city_name} {self.cases_for_weather_data(simple_weather)} за цельсієм.')

            else:
                # load the custom SpaCy NER model
                nlp = spacy.load("uk_core_news_lg")

                # THIS IS OUR CITY NAME
                doc = str(nlp(entities))
                nom_case = morph.parse(doc)[0].inflect({"nomn"}).word.capitalize()
                print(nom_case)

                # our weather and it's types
                base = self.get_weather_data(nom_case)
                simple_weather = base[0]
                more_info_weather = base[1]
                type_weather = base[2]

                if simple_weather != more_info_weather:
                    dispatcher.utter_message(
                        text=f'Дякую за точний запит! Погода у місті {nom_case} сьгодні {type_weather}. Температура у місті {nom_case} {self.cases_for_weather_data(simple_weather)} за Цельсієм, але відчувається як {self.cases_for_weather_data(more_info_weather)}.')
                else:
                    dispatcher.utter_message(
                        text=f'Дякую за точний запит! Погода у місті {nom_case} сьгодні {type_weather}. Температура у місті {nom_case} {self.cases_for_weather_data(simple_weather)} за цельсієм.')

        # to catch our final exception
        except (IndexError, KeyError, ValueError, AttributeError, UnboundLocalError) as e:
            error_messages = {
                IndexError: f'It is not about you! It is about {e}.',
                KeyError: 'KeyError: main',
                ValueError: 'Value error',
                AttributeError: 'AttributeError',
                UnboundLocalError: 'UnboundLocalError'
            }
            error_message = error_messages.get(type(e), 'Unknown Error')
            print(error_message)
            dispatcher.utter_message(text='На жаль, не зрозуміла ваш запит. Повторіть будь ласка.')

        return []


# NEW DATA STARTS FROM HERE


class ActionHappyToTalk(Action):
    def name(self) -> Text:
        return "action_glad_to_help"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(
                    text=f'Ми завжди раді допомогти, {converted_name}. Сформулюйте, будь ласка, ваш запит.')
            else:
                 dispatcher.utter_message(
                    text=f'Трапилася помилка. Ми працюємо над її виправленням.')

        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        return []


# getting first account number --> successful one
class ActionQuestionFirst(Action):

    def name(self) -> Text:
        return "action_address"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        # file that we will use as a counter
        with open('counter1.txt', 'a') as file:
            file.write('used ')

        user_message = tracker.latest_message.get("text", "")
        preprocessed_message = re.sub(r"[.'’]", "", user_message.lower())
        print('PREPROCESSED MESSAGE', str(preprocessed_message))

        result = convert_written_numbers(str(preprocessed_message)).replace(' ', '')
        result = result.replace('.', '')
        result_numbers_only = re.sub(r'\D', '', result)
        print('SHORTEN ANSWER', result_numbers_only)

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722
        # один один два два три три чотири чотири пять пять шість

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            translated = translit(data_name, 'uk')
            converted_name = names_changed(translated)

            data_address = data[0].get('c_address')
            data_contact = data[0].get('c_contract')
            data_name = data[0].get('c_clientname')
            print('DATA CONTACT ==> ', data_contact)
            print('DATA ADDRESS ==> ', data_address)

            with open('counter1.txt', 'r') as file:
                text = file.read()
                words = text.split()
                count = len(words)

                if int(data_contact) == int(result_numbers_only):
                        dispatcher.utter_message(
                            text=f'Ваша адреса {data_address}, будь ласка підтвердіть, якщо все вірно.')
                elif count > 3:
                        dispatcher.utter_message(text=f'Ми завжди раді допомогти, {converted_name}. Сформулюйте, будь ласка, ваш запит.')
                else:
                        dispatcher.utter_message(
                        text=f'На жаль, номер договору {preprocessed_message} відсутній в нашій базі даних. '
                             f'Спробуємо ще раз. Будь ласка, назвіть номер вашого особового договору по одній цифрі, наприклад: один два чотири шість нуль один.')
                        dispatcher.utter_message(template='utter_beep')
        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')

        with open('counter1.txt', 'r') as file:
            text = file.read()
            words = text.split()
            count = len(words)

        if count > 3:
            with open('counter1.txt', 'w') as file:
                file.truncate()

        return []


# getting electricity meter --> successful one
class ActionQuestionSecond(Action):

    def name(self) -> Text:
        return "action_electricity_meter"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722


        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                data_address = data[0].get('c_address')
                data_contact = data[0].get('c_contract')
                data_name = data[0].get('c_clientname')
                print('DATA CONTACT ==> ', data_contact)
                print('DATA ADDRESS ==> ', data_address)

                dispatcher.utter_message(text=f'{converted_name}, тепер будь ласка після звукового сигналу назвіть показники лічильника по одній цифрі. '
                                            f'Нагадую, це до шести цифр до коми.')
            else:
                 dispatcher.utter_message(
                    text=f'Трапилася помилка. Ми працюємо над її виправленням.')

        except:
            print('Something went wrong. Check here ==> action_electricity_meter!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        return []


# getting electricity meter --> failed one (not six numbers)
class ActionQuestionThird(Action):
    def name(self) -> Text:
        return "action_pre_check"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        # cleaning previous file
        with open('counter1.txt', 'w') as file:
            file.truncate()

        # making a new file to check whether the amount of numbers in the electricity meter is sufficient
        with open('counter2.txt', 'a') as file:
            file.write('used ')

        user_message = tracker.latest_message.get("text", "")
        preprocessed_message = re.sub(r"['’]", "", user_message.lower())
        result = convert_written_numbers(str(preprocessed_message)).replace(' ', '')
        result = result.replace('.', '')
        result = re.sub(r'\D', '', result)
        print('SHORTEN ANSWER', result)
        # separate words
        global_words = [int(digit) for digit in result]

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                data_address = data[0].get('c_address')
                data_contact = data[0].get('c_contract')
                print('DATA CONTACT ==> ', data_contact)
                print('DATA ADDRESS ==> ', data_address)

                with (open('counter2.txt', 'r') as file):
                    text = file.read()
                    words = text.split()
                    count = len(words)
                    print('COUNTING ATTEPTS: ', count)

                    if len(global_words) <= 6:
                        dispatcher.utter_message(
                        text=f'{converted_name} давайте перевіримо. Ваші показники {global_words}, будь ласка підтвердіть, якщо все вірно?')
                    elif count > 3:
                        dispatcher.utter_message(
                        text='На жаль, я не почула показники лічильників. Будь ласка скажіть, якщо ми ще чимось можемо допомогти.')
                    elif len(global_words) > 6:
                        dispatcher.utter_message(text=f'На жаль, я почула більше шести цифр {converted_name}, а саме {global_words}. '
                                              f'Спробуємо ще раз.  '
                                              f'{converted_name}, назвіть будь ласка ще раз показники лічильника по одній цифрі. '
                                              f'Нагадую, це до шести цифр до коми.')
                        dispatcher.utter_message(template='utter_beep')

            else:
                dispatcher.utter_message(text="Схоже, що щось пішло не так. Повторіть ваш запит будь ласка.")
        except:
            print('Something went wrong. Check here ==> action_electricity_meter!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        with open('counter2.txt', 'r') as file:
            text = file.read()
            words = text.split()
            count = len(words)

        if count > 3:
            with open('counter2.txt', 'w') as file:
                file.truncate()
        

        return []


# FINISH success
class ActionFinal(Action):
    def name(self) -> Text:
        return "action_final"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict, link
    ) -> List[Dict[Text, Any]]:
        # cleaning counter2
        with open('counter2.txt', 'w') as file:
            file.truncate()

        bot_event = next(e for e in reversed(tracker.events) if e["event"] == "bot")
        string = bot_event['text']
        print('STRING ==> ', string)
        data_num = re.findall(r'\d+', string)
        data_num = ''.join(data_num)
        print('OUR ENTERED NUMBER', data_num)

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722
        
        
        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                c_id = data[0].get('c_id')
                print('C_clientid', c_id)
                post_url = f"{link}{c_id}"
                post_data = {
                    "c_meter": str(data_num)
                }

                get_headers = {
                    "Authorization": f"Bearer {token}"
                }

                response2 = requests.put(post_url, json=post_data, headers=get_headers)
                print('RESPONSE ==> ', response2)

                # response3 = requests.put(post_url, data=post_data, headers=get_headers)
                # print(response3)

                dispatcher.utter_message(
                text=f'Чудово, {converted_name}! Ваші показники успішно внесено в базу даних. Якщо вам ще щось потрібно, то ми завжди до ваших послуг.')
            else:
                dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        return []


# account number incorrect, ask one more time
class ActionLetsTryMore(Action):

    def name(self) -> Text:
        return "action_ask_one_more_time"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722

        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(
                    text=f'{converted_name}, давайте спробуємо ще раз')
            else:
                 dispatcher.utter_message(
                    text=f'Трапилася помилка. Ми працюємо над її виправленням.')

        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        return []


# account number is wrong, let's try one more time
class ActionQuestionFirstClarify(Action):

    def name(self) -> Text:
        return "action_address_wrong"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")
        preprocessed_message = re.sub(r"['’]", "", user_message.lower())
        result = convert_written_numbers(str(preprocessed_message)).replace(' ', '')
        result = result.replace('.', '')
        print('SHORTEN ANSWER', result)

        # new data here

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722
        # один один два два три три чотири чотири пять пять шість


        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                data_address = [data_dict.get('c_address') for data_dict in data][0]
                data_contact = [data_dict.get('c_contract') for data_dict in data][0]
                print('DATA CONTACT ==> ', data_contact)
                print('DATA ADDRESS ==> ', data_address)

                if int(data_contact) != int(result):
                    dispatcher.utter_message(
                        text=f'На жаль, номер договору {user_message} відсутній в нашій базі даних. Спробуємо ще раз.')

            else:
                 dispatcher.utter_message(
                    text=f'Трапилася помилка. Ми працюємо над її виправленням.')

        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        return []


class ActionQuestionFirstIncorrect(Action):

    def name(self) -> Text:
        return "action_account_wrong_finish"

    def run(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get("text", "")
        preprocessed_message = re.sub(r"['’]", "", user_message.lower())
        result = convert_written_numbers(str(preprocessed_message)).replace(' ', '')
        result = result.replace('.', '')
        print('SHORTEN ANSWER', result)
        # new data here

        user_phone = tracker.current_state()['sender_id']
        user_phone = int(user_phone)
        # user_phone = 7722
        # один один два два три три чотири чотири пять пять шість


        token = get_token()
        print('TOKEN ==> ', token)

        data = get_data_with_token(token, user_phone)

        try:
            data_name = data[0].get('c_clientname')
            if data_name is not None or data_name != None:
                translated = translit(data_name, 'uk')
                converted_name = names_changed(translated)

                dispatcher.utter_message(text=f'На жаль, номер договору {user_message} відсутній в нашій базі даних. {converted_name} чим іще ми можемо вам допомогти?')
            else:
                 dispatcher.utter_message(
                    text=f'Трапилася помилка. Ми працюємо над її виправленням.')

        except:
            print('Something went wrong. Check here ==> action_convert_name_utter_bye!')
            dispatcher.utter_message(text="Трапилася помилка. Ми працюємо над її виправленням.")

        return []

        
# writing down everything we talsk about into a txt file
class ActionWriteToFile(Action):

    def name(self) -> Text:
        return "action_write_to_file"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the user's message
        user_message = tracker.latest_message.get('text', '')

        # Get the assistant's response
        assistant_response = dispatcher.messages[-1].get('text', '')

        # Create a string containing both the user's message and the assistant's response
        interaction_data = f"User: {user_message}\nAssistant: {assistant_response}\n\n"

        # Specify the file path where you want to store the interaction data
        file_path = "interaction_data.txt"

        # Write the interaction data to the file
        with open(file_path, 'a') as file:
            file.write(interaction_data)

        return []
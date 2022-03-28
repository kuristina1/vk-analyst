import telebot
from telebot import types
import requests
from pymorphy2 import MorphAnalyzer
import re
import pandas as pd
import matplotlib.pyplot as plt
import collections
from pymystem3 import Mystem
from wordcloud import WordCloud


TOKEN = "88f389cb88f389cb88f389cbcd88885196888f388f389cbeacc810cb5f620fe9c9f3080"
TOKEN2 = "5193551492:AAHBFv_3bDxAnUH_b8daZTjlLPip4PiB4es"
VERSION = "5.130"

bot = telebot.TeleBot(TOKEN2)

morph = MorphAnalyzer()
stem_lemm = Mystem()


# Кнопки помощи
@bot.message_handler(commands=["help"])
def repeat_all_messages(message):

    keyboard = types.InlineKeyboardMarkup()

    button1 = types.InlineKeyboardButton(text="Что делает этот бот?", callback_data="button1")
    button2 = types.InlineKeyboardButton(text="Список доступных команд", callback_data="button2")
    button3 = types.InlineKeyboardButton(text="Каким должен быть формат вводных данных?", callback_data="button3")
    button6 = types.InlineKeyboardButton(text="Контакты", callback_data="button6")
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button6)

    bot.send_message(message.chat.id, "FAQ", reply_markup=keyboard)


# Основная команда
@bot.message_handler(commands=['start'])
def get_id_message(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Введите ссылку на интересующее Вас сообщество в VK, пожалуйста")


# Обработчик ссылки - регуляркой выстаскиваем айди, чтобы послать запрос вк апи,
# также добавляем кнопку для получения данных
@bot.message_handler(regexp=r"https:..vk.com.(.+)")
def save_input_id(message):

    with open("id.txt", "w", encoding="utf-8") as f:
        f.write("".join(message.text).replace("https://vk.com/", ""))

    keyboard = types.InlineKeyboardMarkup()
    button4 = types.InlineKeyboardButton(text="Получить данные", callback_data="button4")
    keyboard.add(button4)

    bot.send_message(message.chat.id, "Ссылка успешно получена! Нажмите на кнопку, чтобы увидеть полученные данные! "
                                      "Если Вам требуется информация о другом сообществе,"
                                      " повторно наберите команду /start!", reply_markup=keyboard)


# Главный обработчик кнопок - настраиваем функционал
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    if call.message:
        if call.data == "button1":
            bot.send_message(call.message.chat.id, "Бот анализирует статистику по подписчикам интересного вам "
                                                   "сообщества в социальной сети Вконтакте и выдает демографические "
                                                   "данные по полу, возрасту, стране проживания и именам, также бот "
                                                   "умеет строить облако слов (визуальное представление текста) по "
                                                   "статусам подписчиков. Еще одна функция - "
                                                   "портрет среднестатистического подписчика")

        if call.data == "button2":
            bot.send_message(call.message.chat.id, "/start, /help")

        if call.data == "button3":
            bot.send_message(call.message.chat.id, "Необходимо ввести ссылку на интересующее сообщество "
                                                   "вида: https://vk.com/example")

        if call.data == "button4":
            keyboard = types.InlineKeyboardMarkup()
            button9 = types.InlineKeyboardButton(text="Демографическая статистика", callback_data="button9")
            button10 = types.InlineKeyboardButton(text="Облако слов", callback_data="button10")
            button11 = types.InlineKeyboardButton(text="Портрет", callback_data="button11")
            keyboard.add(button9, button10, button11)
            bot.send_message(call.message.chat.id, "Какой тип данных вас интересует?",
                             reply_markup=keyboard)

        # Здесь я собираю данные с помощью запроса, строю датафрейм для построения всех нужных графиков
        if call.data == "button9":

            GROUP_MEMBERS = "https://api.vk.com/method/groups.getMembers"

            with open("id.txt", "r", encoding="utf-8") as f:
                r = f.read()
                group = str(r)

            def get_members(group_name, page, count=1000):
                data = requests.get(
                    GROUP_MEMBERS,
                    params={
                        'group_id': group_name,
                        'access_token': TOKEN,
                        "count": count,
                        "sort": "id_asc",
                        "fields": "sex,bdate,country,first_name",
                        'v': VERSION,
                        'offset': count * page

                    }
                ).json()
                return data

            def get_age(string):
                return "".join(re.findall(r"[0-9]{4}", string)).lower()

            response = get_members(group, page=0, count=1000)
            listio = []
            low_age = []
            mid_age = []
            high_age = []
            very_high_age = []
            for person in response["response"]["items"]:
                dictio = dict()
                dictio["id"] = person["id"]
                if "country" in list(person.keys()):
                    if person["country"]["title"] is not None:
                        if person["country"]["title"] != "":
                            dictio["country"] = person["country"]["title"]
                if person["sex"] == 1:
                    dictio["sex"] = "female"
                if person["sex"] == 2:
                    dictio["sex"] = "male"
                if "status" in list(person.keys()):
                    if person["status"] is not None:
                        if person["status"] != "":
                            dictio["status"] = person["status"]
                if "bdate" in list(person.keys()):
                    if person["bdate"] is not None:
                        if get_age(person["bdate"]) != "":
                            age = str(2022 - int(get_age(person["bdate"])))
                            if int(age) < 20:
                                low_age.append(age)
                            if 20 < int(age) < 40:
                                mid_age.append(age)
                            if 40 < int(age) < 60:
                                high_age.append(age)
                            if int(age) > 60:
                                very_high_age.append(age)
                if "first_name" in list(person.keys()):
                    if person["first_name"] is not None:
                        if person["first_name"] != "":
                            dictio["first_name"] = person["first_name"]
                listio.append(dictio)

            big_data = pd.DataFrame(listio).dropna()
            name = str(group) + ".png"

            plt.figure(figsize=(18, 15))
            plt.subplot(2, 2, 1)
            big_data['sex'].value_counts().plot.pie(autopct='%1.1f%%', shadow=True, startangle=90)
            plt.title("Распределение по полу")

            plt.subplot(2, 2, 2)
            plt.bar(x=["Младше 20", "От 20 до 40", "От 40 до 60", "Старше 60"],
                    height=[len(low_age), len(mid_age), len(high_age), len(very_high_age)])
            plt.title("Распределение по возрастным группам")
            plt.ylabel("Кол-во человек")
            plt.xlabel("Возрастная группа")

            plt.subplot(2, 2, 3)
            countries = [row["country"] for i, row in big_data.iterrows()]
            dic_country = dict(collections.Counter(countries).most_common(5))
            plt.bar(x=list(dic_country.keys()), height=list(dic_country.values()))
            plt.title("Распределение по странам (топ-5)")
            plt.ylabel("Кол-во человек")
            plt.xlabel("Страна проживания")

            plt.subplot(2, 2, 4)
            names = [row["first_name"] for i, row in big_data.iterrows()]
            dic_names = dict(collections.Counter(names).most_common(10))
            sizes = list(dic_names.values())
            plt.pie(sizes, labels=list(dic_names.keys()), autopct='%1.1f%%',
                    shadow=True, startangle=90)
            plt.title("Топ-10 самых частых имен")

            plt.savefig(name)

            img = open(name, "rb")
            bot.send_photo(call.message.chat.id, img)

        # Далее для постройки вордклауда алгоритм примерно тот же самый + добавляется немного морф. парсинга и
        # приведения текстов в нужный вид
        if call.data == "button10":

            GROUP_MEMBERS = "https://api.vk.com/method/groups.getMembers"
            with open("id.txt", "r") as f:
                r = f.read()
                group = str(r)

            def get_statuses(group_name, page, count=1000):
                data = requests.get(
                    GROUP_MEMBERS,
                    params={
                        'group_id': group_name,
                        'access_token': TOKEN,
                        "count": count,
                        "sort": "id_asc",
                        "fields": "status",
                        'v': VERSION,
                        'offset': count * page

                    }
                ).json()
                return data

            response2 = get_statuses(group, page=0, count=1000)
            listio2 = []

            for person in response2["response"]["items"]:
                dictio = dict()
                dictio["id"] = person["id"]
                if "status" in list(person.keys()):
                    if person["status"] != "":
                        dictio["status"] = person["status"]
                listio2.append(dictio)

            big_data2 = pd.DataFrame(listio2).dropna()
            statuses = [str(row["status"]) for i, row in big_data2.iterrows()]
            name = str(group) + "_wordcloud.png"

            # Делаем строку
            text = "".join(statuses)

            # Чистим все ненужные знаки и лемматизируем
            text_no_punct = " ".join(re.findall(r"[а-яА-Я]+", text))
            lemmatized_text = "".join(stem_lemm.lemmatize(text_no_punct))

            # Убираем стопслова
            with open("stopwords.txt", encoding="utf-8") as f:
                r = f.readlines()
            stops = [i.replace("\n", "") for i in r] + ['это', 'весь', 'который', 'мочь', 'свой']
            text_no_stopwords = []
            for word in lemmatized_text.split():
                if word not in stops:
                    text_no_stopwords.append(word)
            lemmatized_text2 = " ".join(text_no_stopwords)

            # Делаем wordcloud
            wc = WordCloud(
                background_color='white',
                width=800,
                height=800,
            ).generate(lemmatized_text2)

            plt.figure(figsize=(8, 8), facecolor=None)
            plt.imshow(wc)
            plt.axis("off")
            plt.title('Облако слов по статусам подписчиков')
            plt.savefig(name)

            img = open(name, "rb")
            bot.send_photo(call.message.chat.id, img)

        # Здесь почти все те же самые алгоритмы, просто выделяем самые частотные пункты
        if call.data == "button11":

            GROUP_MEMBERS = "https://api.vk.com/method/groups.getMembers"
            with open("id.txt", "r") as f:
                r = f.read()
                group = str(r)

            def get_members2(group_name, page, count=1000):
                data = requests.get(
                    GROUP_MEMBERS,
                    params={
                        'group_id': group_name,
                        'access_token': TOKEN,
                        "count": count,
                        "sort": "id_asc",
                        "fields": "sex,bdate,country,first_name, status",
                        'v': VERSION,
                        'offset': count * page

                    }
                ).json()
                return data

            def get_age(string):
                return "".join(re.findall(r"[0-9]{4}", string)).lower()

            response3 = get_members2(group, page=0, count=1000)

            listio3 = []

            for person in response3["response"]["items"]:
                dictio = dict()
                dictio["id"] = person["id"]
                if person["sex"] == 1:
                    dictio["sex"] = "female"
                if person["sex"] == 2:
                    dictio["sex"] = "male"
                if "country" in list(person.keys()):
                    if person["country"]["title"] is not None:
                        if person["country"]["title"] != "":
                            dictio["country"] = person["country"]["title"]
                if "bdate" in list(person.keys()):
                    if person["bdate"] is not None:
                        if get_age(person["bdate"]) != "":
                            dictio["age"] = str(2022 - int(get_age(person["bdate"])))
                if "first_name" in list(person.keys()):
                    if person["first_name"] is not None:
                        if person["first_name"] != "":
                            dictio["first_name"] = person["first_name"]
                if "status" in list(person.keys()):
                    if person["status"] != "":
                        dictio["status"] = person["status"]
                listio3.append(dictio)

            big_data3 = pd.DataFrame(listio3).dropna()

            sexs = [row["sex"] for i, row in big_data3.iterrows()]
            sexport = "".join(dict(collections.Counter(sexs).most_common(1)).keys())
            ages = [row["age"] for i, row in big_data3.iterrows()]
            ageport = "".join(dict(collections.Counter(ages).most_common(1)).keys())
            names = [row["first_name"] for i, row in big_data3.iterrows()]
            nameport = "".join(dict(collections.Counter(names).most_common(1)).keys())
            countries = [row["country"] for i, row in big_data3.iterrows()]
            countryport = "".join(dict(collections.Counter(countries).most_common(1)).keys())

            statuses = [str(row["status"]) for i, row in big_data3.iterrows()]
            # Делаем строку
            text = "".join(statuses)

            # Чистим все ненужные знаки и лемматизируем
            text_no_punct = " ".join(re.findall(r"[а-яА-Я]+", text))
            lemmatized_text = "".join(stem_lemm.lemmatize(text_no_punct))

            # Убираем стопслова
            with open("stopwords.txt", encoding="utf-8") as f:
                r = f.readlines()
            stops = [i.replace("\n", "") for i in r] + ['это', 'весь', 'который', 'мочь', 'свой']
            text_no_stopwords = []
            for word in lemmatized_text.split():
                if word not in stops:
                    text_no_stopwords.append(word)
            wordport = "".join(dict(collections.Counter(text_no_stopwords).most_common(1)).keys())

            bot.send_message(call.message.chat.id, "Портрет среднестатистического подписчика на основе полученных "
                                                   "данных: \n- Пол: "
                                                   "" + sexport + "\n" + "- Возраст: " + ageport + "\n" + "- Имя: "
                             + nameport + "\n" + "- Страна проживания: " + countryport + "\n" + "- Самое вероятное "
                                                                                                "слово в статусе: "
                             + wordport)

        if call.data == "button6":
            bot.send_message(call.message.chat.id, "Электронная почта: sf86workshop@gmail.com, tg: @kuristina2")


if __name__ == '__main__':
    bot.polling(none_stop=True)

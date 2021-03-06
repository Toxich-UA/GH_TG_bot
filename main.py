import os
import telebot
import requests
import json
from os import path
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

key = "API_KEY"
file_name = "ips.json"
spaces_amount = 25
API_KEY = os.environ.get(key)
bot = telebot.TeleBot(API_KEY)


@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    get_btn = KeyboardButton('Get')
    markup.row(get_btn)
    bot.send_message(message.chat.id, "Press Get button to get temperature:", reply_markup=markup)


def check_add_message(message):
    if message.text.startswith("/add") and len(message.text.split()) == 3:
        return True
    else:
        return False


@bot.message_handler(func=check_add_message)
def add(message):
    args = message.text.split()
    data = {}
    if path.exists(file_name):
        if os.stat(file_name).st_size != 0:
            with open(file_name, "r") as file:
                data = json.load(file)
                data[args[1]] = {
                    "name": args[2],
                    "temp_names": [
                        "\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430 \u0432\u043e\u0437\u0434\u0443\u0445\u0430",
                        "\u0422\u0435\u043c\u043f\u0440\u0435\u0442\u0443\u0440\u0430 \u043a\u043e\u0442\u043b\u0430",
                        "\u0422\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430 \u0432\u043d\u0443\u0442\u0440\u0438",
                        "OneWire_c",
                        "OneWire_d",
                        "OneWire_e"
                    ],
                    "hum_names": [
                        "\u0412\u043b\u0430\u0436\u043d\u043e\u0441\u0442\u044c \u0432\u043e\u0437\u0434\u0443\u0445\u0430",
                        "\u0412\u043b\u0430\u0436\u043d\u043e\u0441\u0442\u044c \u043f\u043e\u0447\u0432\u044b",
                        "b",
                        "c",
                        "d"
                    ]
                }
        else:
            data[args[1]] = args[2]
        with open(file_name, "w") as file:
            file.write(json.dumps(data))
        bot.send_message(message.chat.id, f"Greenhouse with ip {args[1]} was added to bot with name {args[2]}")


@bot.message_handler(commands=["remove"])
def remove(message):
    gh_to_remove_menu = InlineKeyboardMarkup(row_width=2)
    if path.exists(file_name):
        if os.stat(file_name).st_size != 0:
            with open(file_name, "r") as file:
                data = json.load(file)
                if len(data) != 0:
                    for item in data.items():
                        ip = item[0]
                        name = item[1]["name"]
                        gh_to_remove_menu.add(InlineKeyboardButton(name, callback_data="remove_" + ip))
                    bot.send_message(message.chat.id, "Chose GH to remove", reply_markup=gh_to_remove_menu)
                else:
                    bot.send_message(message.chat.id, f"There is nothing to remove!")


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith('remove_'))
def remove_callback(callback_query):
    ip = callback_query.data.replace('remove_', "")
    if path.exists(file_name):
        if os.stat(file_name).st_size != 0:
            with open(file_name, "r") as file:
                data = json.load(file)
                if ip in data:
                    del data[ip]
            with open(file_name, "w") as file:
                file.write(json.dumps(data))
            bot.answer_callback_query(callback_query.id, text=f'Ip {ip} was removed from bot')
        else:
            bot.answer_callback_query(callback_query.id, f"There is no any GH added!")


@bot.message_handler(func=lambda message: message.text == "Get")
def get(message):
    res = ""

    if path.exists(file_name):
        with open(file_name, "r") as file:
            ips = json.load(file)
            current_time = datetime.now().strftime('%H:%M:%S')
            for item in ips.items():
                ip = item[0]
                temp_names = item[1]["temp_names"]
                hum_names = item[1]["hum_names"]
                name = item[1]["name"]
                try:
                    response = requests.post(f"http://{ip}/sensors", data={'key': '8Synbt9N7p5yttx8'},
                                             timeout=1).json()
                    msg = "<pre>"
                    msg += f" Values for {name} on {current_time} ".center(spaces_amount, '+')
                    msg += "\n"
                    msg += f" Ip {ip} ".center(spaces_amount, '+')
                    msg += "\n"
                    msg += f" Temperature ".center(spaces_amount, '=')
                    msg += "\n"
                    msg += get_name_and_values(temp_names, response["sensors"]["temperature"])
                    msg += f" Humidity ".center(spaces_amount, '=')
                    msg += "\n"
                    msg += get_name_and_values(hum_names, response["sensors"]["humidity"])
                    msg += "+".center(spaces_amount, '+')
                    msg += "</pre>"
                except requests.exceptions.RequestException as e:
                    msg = "<pre>"
                    msg += f" Values for {name} on {current_time} ".center(spaces_amount, '+')
                    msg += "\n"
                    msg += f" Ip {ip} ".center(spaces_amount, '+')
                    msg += "\n"
                    msg += "Cannot get data".center(spaces_amount, " ")
                    msg += "\n"
                    msg += "+".center(spaces_amount, '+')
                    msg += "</pre>"
                res += msg + "\n\n"
        bot.send_message(message.chat.id, res, parse_mode="HTML")


def get_name_and_values(names, response):
    msg = ""
    values = []
    for t in response:
        values.append(response[t]["val"])
    for i, val in enumerate(values):
        msg += f"{names[i] :<25}{val : >10}\n"
    return msg


if __name__ == '__main__':
    bot.infinity_polling()

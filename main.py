import os
import telebot
import requests
import json
from os import path
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

key = "API_KEY"
file_name = "ips.json"
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
                data[args[1]] = args[2]
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
                    for ip, name in data.items():
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
    temp_names = ["Температура воздуха", "OneWire_a", "OneWire_b", "OneWire_c", "OneWire_d", "OneWire_e"]
    hum_names = ["Влажность воздуха", "a", "b", "c", "d"]
    if path.exists(file_name):
        with open(file_name, "r") as file:
            ips = json.load(file)
            current_time = datetime.now().strftime('%H:%M:%S')
            for ip, name in ips.items():
                try:
                    response = requests.get(f"http://{ip}/", timeout=5).json()
                    msg = f"+++ Values for {name} on {current_time} +++"
                    msg += "\n"
                    msg += f"+++ Ip {ip} +++"
                    msg += "\n"
                    msg += f"Temperature".center(35, '=')
                    msg += "\n"
                    msg += get_name_and_values(temp_names, response["sensors"]["temperature"])
                    msg += f"Humidity".center(35, '=')
                    msg += "\n"
                    msg += get_name_and_values(hum_names, response["sensors"]["humidity"])
                    msg += "\n"
                    msg += "++++++++++++++++++++++++++++++++++"
                except:
                    msg = f"+++ Values for {name} on {current_time} +++"
                    msg += "\n"
                    msg += f"+++ Ip {ip} +++"
                    msg += "\n"
                    msg += "Cannot get data".center(40, " ")
                    msg += "\n"
                    msg += "+++++++++++++++++++++++++++++++++++"
                res += msg + "\n\n"
        bot.send_message(message.chat.id, res)


def get_name_and_values(names, response):
    msg = ""
    values = []
    for t in response:
        values.append(response[t]["val"])
    for i, val in enumerate(values):
        msg += f"{names[i] :<25}{val : >25}\n"
    return msg


if __name__ == '__main__':
    bot.infinity_polling()

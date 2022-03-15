import os
from datetime import datetime
from os import path
import telebot
import requests

key = "API_KEY"
file_name = "ips.txt"
API_KEY = os.environ.get(key)
bot = telebot.TeleBot(API_KEY)


@bot.message_handler(commands=['get'])
def get(message):
    res = ""
    temp_names = ["Температура воздуха", "OneWire_a", "OneWire_b", "OneWire_c", "OneWire_d", "OneWire_e"]
    hum_names = ["Влажность воздуха", "a", "b", "c", "d"]
    if path.exists(file_name):
        with open(file_name, "r") as file:
            ips = file.read().splitlines()
            current_time = datetime.now().strftime('%H:%M:%S')
            for ip in ips:
                try:
                    response = requests.get(f"http://{ip}/", timeout=5).json()
                    msg = f"++++++++++ Values for {ip} on {current_time} ++++++++++"
                    msg += "\n"
                    msg += f"Temperature".center(40, '=')
                    msg += "\n"
                    msg += get_name_and_values(temp_names, response["sensors"]["temperature"])
                    msg += f"Humidity".center(40, '=')
                    msg += "\n"
                    msg += get_name_and_values(hum_names, response["sensors"]["humidity"])
                    msg += "\n"
                    msg += "+++++++++++++++++++++++++++++++++++++++++++++++++"
                except:
                    msg = f"++++++++++ Values for {ip} on {current_time} ++++++++++"
                    msg += "\n"
                    msg += "Cannot get data".center(40, " ")
                    msg += "\n"
                    msg += "+++++++++++++++++++++++++++++++++++++++++++++++++"
                res += msg + "\n"
        bot.send_message(message.chat.id, res)


def get_name_and_values(names, response):
    msg = ""
    values = []
    for t in response:
        values.append(response[t]["val"])
    for i, val in enumerate(values):
        msg += f"{names[i] :<30}{val : >30}\n"
    return msg


if __name__ == '__main__':
    bot.polling()

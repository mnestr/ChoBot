import telebot
import db
import config
from main import base_buttons

bot = telebot.TeleBot(config.token, parse_mode=None)

if __name__ == "__main__":
    notify_list = db.get_notify_list()
    for item in notify_list:
        if not item[5] or item[3] > item[5]:
            db.count_notification(item[0])
            markup = base_buttons()
            bot.send_message(item[1], "Hey, you have {0} words to repeat! Wanna start?".format(item[2]),
                             disable_notification=False, reply_markup=markup)

import telebot
import db
import config
from telebot import types
import datetime
from pytz import timezone

bot = telebot.TeleBot(config.token, parse_mode=None)

if __name__ == "__main__":
    notify_list = db.get_notify_list()
    for item in notify_list:
        # delta = timezone('UTC').localize(datetime.datetime.now()) - item[5]
        if not item[5] or item[3] > item[5]:
            db.count_notification(item[0], "+1")
            markup = types.ReplyKeyboardMarkup(row_width=2)
            answer_1 = types.KeyboardButton('Anything to repeat?')
            answer_2 = types.KeyboardButton('Learn new words')
            answer_3 = types.KeyboardButton('Add word')
            markup.add(answer_1, answer_2, answer_3)
            bot.send_message(item[1], "Hey, you have {0} words to repeat! Wanna start?".format(item[2]), reply_markup=markup)

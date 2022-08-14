import telebot
import db
import config
import datetime
from pytz import timezone

bot = telebot.TeleBot(config.token, parse_mode=None)

if __name__ == "__main__":
    notify_list = db.get_notify_list()
    for item in notify_list:
        # delta = timezone('UTC').localize(datetime.datetime.now()) - item[5]
        # if item[3] < timezone('UTC').localize(datetime.datetime.now()) and delta.days > 1:
        #     db.count_notification(item[0], "+1")
        bot.send_message(item[1], "Hey, you have {0} words to repeat! Wanna start?".format(item[2]))

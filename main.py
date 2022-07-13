import telebot
import random
from telebot import types
from telebot import custom_filters
import db

bot = telebot.TeleBot('5532590680:AAH7jrLQjuDy87cFcin3UDM7uaD8DubYtEE', parse_mode=None)

# repetitions = {1: 15 минут, 2: 6 часов, 3: 1 день, 4: 2 дня, 4: 3 суток, 5: 5 дней, 6: 7 дней, 7: 14 дней, 8: 1 месяц}


class Repetition:
    def __init__(self):
        self.user_id = None
        self.new_words = None
        self.sorted_words_count = 0
        self.level_down_once = 0
        self.word_lrn = None
        self.word_tr = None
        self.word_id = None


user_repetition = Repetition()


def create_user(message):
    tg_id = int(message.from_user.id)
    first_name = str(message.from_user.first_name)
    last_name = str(message.from_user.last_name)
    user_name = str(message.from_user.username)
    language_code = str(message.from_user.language_code)
    db.db_insert_user(tg_id, first_name, last_name, language_code, user_name)


def pickup_answers_on_buttons():
    words = []
    answer = user_repetition.word_lrn
    words_from_dictionary = db.get_words_from_dictionary()
    for x in words_from_dictionary:
        if x[0] == user_repetition.word_id:
            continue
        else:
         words.append(x[1])
    answers = random.sample(list(words), 3)
    answers.append(answer)
    random.shuffle(answers)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    answer_1 = types.KeyboardButton(answers[0])
    answer_2 = types.KeyboardButton(answers[1])
    answer_3 = types.KeyboardButton(answers[2])
    answer_4 = types.KeyboardButton(answers[3])
    markup.add(answer_1, answer_2, answer_3, answer_4)
    return markup

    # for name in available_food_names: пример как можно попробовать сделать
    #     keyboard.add(name)


def save_word(user_id, word_id, status):
    db.insert_word(user_id, word_id, status)


def pickup_word(repetition):
    word_ids = []
    for x in repetition:
        word_ids.append(x[2])
    word_id = random.choice(word_ids)
    user_repetition.word_id = word_id
    for x in repetition:
        if x[2] == word_id:
            user_repetition.word_lrn = x[0]
            user_repetition.word_tr = x[1]
            break
    return user_repetition.word_tr


@bot.message_handler(commands=['start'])
def start(message):
    tg_id = int(message.from_user.id)
    user_id = db.get_user_id(tg_id)
    if user_id is None:
        create_user(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        answer_1 = types.KeyboardButton('учить новые слова')
        markup.add(answer_1)
        bot.send_message(message.from_user.id, 'У тебя нет слов для повторения. Посмотрим новые слова?', reply_markup=markup)
    else:
        repetition = db.get_repetition(user_id)
        if repetition is None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            answer_1 = types.KeyboardButton('учить новые слова')
            markup.add(answer_1)
            bot.send_message(message.from_user.id, 'У тебя нет слов для повторения. Посмотрим новые слова?', reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            answer_1 = types.KeyboardButton('Повторить')
            markup.add(answer_1)
            bot.send_message(message.from_user.id, 'Повторим слова?', reply_markup=markup)


@bot.message_handler(text=['учить новые слова', 'Повторить'])
def show_word(message):
    tg_id = int(message.from_user.id)
    user_id = db.get_user_id(tg_id)
    user_repetition.user_id = user_id
    repetition = db.get_repetition(user_id)
    if len(repetition) > 0:
        word_tr = pickup_word(repetition)
        markup = pickup_answers_on_buttons()
        bot.send_message(message.chat.id, word_tr, reply_markup=markup)
        bot.register_next_step_handler(message, check_answer)
    else:
        new_words = db.get_new_words_from_dictionary(user_id)
        word = random.choice(new_words)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Уже знаю')
        answer_2 = types.KeyboardButton('Учить')
        markup.add(answer_1, answer_2)
        bot.send_message(message.chat.id, word, reply_markup=markup)
        bot.register_next_step_handler(message, sort_word)


def sort_word(message):
    answer = message.text
    if answer == 'Учить' and user_repetition.sorted_words_count > 2:
        save_word(user_repetition.user_id, user_repetition.word_id, 'repetition')
        user_repetition.sorted_words_count = 0
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Да')
        answer_2 = types.KeyboardButton('Потом')
        markup.add(answer_1, answer_2)
        bot.send_message(message.from_user.id, 'Будем учить! Слова кончились. Начнем учить?', reply_markup=markup)
        bot.register_next_step_handler(message, want_to_learn)
    elif answer == 'Уже знаю':
        save_word(user_repetition.user_id, user_repetition.word_id, 'already_know')
        bot.send_message(message.from_user.id, 'Красава! Вот еще слово:')
        show_word(message)
    elif answer == 'Учить':
        save_word(user_repetition.user_id, user_repetition.word_id, 'repetition')
        user_repetition.sorted_words_count += 1
        bot.send_message(message.from_user.id, 'Будем учить! Вот еще слово:')
        show_word(message)


def check_answer(message):
    user_answer = message.text
    if user_answer == user_repetition.word_lrn:
        if user_repetition.level_down_once == 1:
            user_repetition.level_down_once = 0
            bot.send_message(message.from_user.id, 'Правильно!')
            show_word(message)
        else:
            db.count_repetition(user_repetition.word_id, user_repetition.user_id, "+1")
            user_repetition.level_down_once = 0
            bot.send_message(message.from_user.id, 'Правильно!')
            show_word(message)
    else:
        if user_repetition.level_down_once == 0:
            db.count_repetition(user_repetition.word_id, user_repetition.user_id, "-1")
            user_repetition.level_down_once = 1
        bot.send_message(message.from_user.id, 'Попробуй еще')
        bot.register_next_step_handler(message, check_answer)


def want_to_learn(message):
    answer = message.text
    if answer == 'Да':
        show_word(message)
    elif answer == 'Потом':
        bot.send_message(message.from_user.id, 'Ну как хочешь=/')


bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.polling(none_stop=True)

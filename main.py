import telebot
import random
from telebot import types
from telebot import custom_filters
import db
import config

bot = telebot.TeleBot(config.token, parse_mode=None)

# repetitions = {1: 15 минут, 2: 6 часов, 3: 1 день, 4: 2 дня, 4: 3 суток, 5: 5 дней, 6: 7 дней, 7: 14 дней, 8: 1 месяц}


def create_user(message):
    tg_id = int(message.from_user.id)
    first_name = str(message.from_user.first_name)
    last_name = str(message.from_user.last_name)
    user_name = str(message.from_user.username)
    language_code = str(message.from_user.language_code)
    db.db_insert_user(tg_id, first_name, last_name, language_code, user_name)


def pickup_answers_on_buttons(id_lrn_tr):
    words = []
    words_from_dictionary = db.get_words_from_dictionary()
    for x in words_from_dictionary:
        if x[0] == id_lrn_tr[0]:
            continue
        else:
         words.append(x[1])
    answers = random.sample(list(words), 3)
    answers.append(id_lrn_tr[1])
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
    #
    # #This will generate buttons for us in more elegant way
    # def generate_buttons(bts_names, markup):
    #     for button in bts_names:
    #         markup.add(types.KeyboardButton(button))
    #     return markup


def save_word(user_id, word_id, status):
    db.insert_word(user_id, word_id, status)


def pickup_word(repetition):
    word_ids = []
    for x in repetition:
        word_ids.append(x[0])
    word_id = random.choice(word_ids)
    for x in repetition:
        if x[0] == word_id:
            word_lrn = x[1]
            word_tr = x[2]
            break
    return word_id, word_lrn, word_tr


def format_string(full_translation):
    examp_list = full_translation[0][4].split("\n")
    examp_list2 = []
    for i in examp_list:
        examp_list2.append("  \* " + i)
    examp = "\n".join(examp_list2)
    return examp


@bot.message_handler(commands=['start'])
@bot.message_handler(text=['Hey!'])
def start(message):
    tg_id = message.from_user.id
    user_id = db.get_user_id(tg_id)
    if not user_id:
        create_user(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        answer_1 = types.KeyboardButton('Sure!')
        markup.add(answer_1)
        bot.send_message(message.from_user.id, "Hi! I'm Steve!")
        photo = open('Pictures/1.jpg', 'rb')
        bot.send_photo(message.from_user.id, photo)
        bot.send_message(message.from_user.id, "Wanna learn some words?", reply_markup=markup)
        bot.register_next_step_handler(message, want_to_start, tg_id)
    else:
        repetition = db.get_repetition(user_id)
        if not repetition:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            answer_1 = types.KeyboardButton('Learn new words')
            markup.add(answer_1)
            bot.send_message(message.from_user.id, "You have nothing to repeat. Let's see some new words?", reply_markup=markup)
            bot.register_next_step_handler(message, want_to_start, tg_id)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            answer_1 = types.KeyboardButton('Repeat')
            markup.add(answer_1)
            bot.send_message(message.from_user.id, "You have {0} words to repeat. Let's repeat?".format(len(repetition)), reply_markup=markup)


@bot.message_handler(text=['Learn new words', 'Anything to repeat?'])
def before_want_to_start(message):
    tg_id = message.from_user.id
    bot.register_next_step_handler(message, want_to_start, tg_id)


def want_to_start(message, tg_id):
    answer = message.text
    if answer in ['Sure!', 'Learn new words'] and tg_id == message.from_user.id:
        bot.send_message(message.chat.id, "Ok. Do you know this one?")
        show_word(message)
    elif answer == 'Anything to repeat?' and tg_id == message.from_user.id:
        before_repeat_word(message)


def show_word(message, sorted_words_count=0):
    tg_id = message.from_user.id
    user_id = db.get_user_id(tg_id)
    new_words = db.get_new_words_from_dictionary(user_id)
    id_lrn_tr = pickup_word(new_words)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    answer_1 = types.KeyboardButton('Already know')
    answer_2 = types.KeyboardButton('Learn')
    answer_3 = types.KeyboardButton('Show translation')
    markup.add(answer_1, answer_2, answer_3)
    bot.send_message(message.chat.id, id_lrn_tr[1], disable_notification=True, reply_markup=markup)
    bot.register_next_step_handler(message, sort_word, tg_id,  sorted_words_count, id_lrn_tr)


def sort_word(message, tg_id, sorted_words_count, id_lrn_tr=None):
    answer = message.text
    user_id = db.get_user_id(tg_id)
    if answer == 'Learn' and tg_id == message.from_user.id and sorted_words_count > 1:
        save_word(user_id, id_lrn_tr[0], 'repetition')
        sorted_words_count = 0
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Sure!')
        answer_2 = types.KeyboardButton('Later')
        markup.add(answer_1, answer_2)
        bot.send_message(message.from_user.id, 'You have 3 new words to learn. Wanna start?', reply_markup=markup)
        bot.register_next_step_handler(message, want_to_learn, tg_id)
    elif answer == 'Already know' and tg_id == message.from_user.id:
        save_word(user_id, id_lrn_tr[0], 'already_know')
        bot.send_message(message.from_user.id, 'Lucky you! Here is another word:')
        show_word(message, sorted_words_count)
    elif answer == 'Learn' and tg_id == message.from_user.id:
        save_word(user_id, id_lrn_tr[0], 'repetition')
        sorted_words_count += 1
        bot.send_message(message.from_user.id, "Ok, let's learn then! Here is another word:")
        show_word(message, sorted_words_count)
    elif answer == 'Show translation' and tg_id == message.from_user.id:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Already know')
        answer_2 = types.KeyboardButton('Learn')
        markup.add(answer_1, answer_2)
        full_translation = db.get_tr_by_id(id_lrn_tr[0])
        examp = format_string(full_translation)
        bot.send_message(message.chat.id, "  *{0}* (_{1}_) - {2} *//* {3}\n\n_Example:_\n{4}".format(full_translation[0][0], full_translation[0][2], full_translation[0][1], full_translation[0][3], examp), reply_markup=markup,  parse_mode='markdown')
        bot.register_next_step_handler(message, sort_word, tg_id, sorted_words_count, id_lrn_tr)


def want_to_learn(message, tg_id):
    answer = message.text
    if answer == 'Sure!' and tg_id == message.from_user.id:
        before_repeat_word(message)
    elif answer == 'Later' and tg_id == message.from_user.id:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        answer_1 = types.KeyboardButton('Hey!')
        markup.add(answer_1)
        bot.send_message(message.from_user.id, 'As you wish=/', reply_markup=markup)


@bot.message_handler(text=['Repeat'])
def before_repeat_word(message):
    tg_id = message.from_user.id
    user_id = db.get_user_id(tg_id)
    repetition = db.get_repetition(user_id)
    repeat_word(message, repetition)


def repeat_word(message, repetition):
    if len(repetition) > 0:
        tg_id = message.from_user.id
        id_lrn_tr = pickup_word(repetition)
        markup = pickup_answers_on_buttons(id_lrn_tr)
        bot.send_message(message.chat.id, id_lrn_tr[2], reply_markup=markup)
        bot.register_next_step_handler(message, check_answer, tg_id, id_lrn_tr)
    elif len(repetition) == 0:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Anything to repeat?')
        answer_2 = types.KeyboardButton('Learn new words')
        markup.add(answer_1, answer_2)
        bot.send_message(message.from_user.id, "You've repeated all words. Try to memorize them and Come back later to repeat", disable_notification=True, reply_markup=markup)
        tg_id = message.from_user.id
        bot.register_next_step_handler(message, want_to_start, tg_id)


def check_answer(message, tg_id, id_lrn_tr=None, level_down_once=0):
    user_answer = message.text
    user_id = db.get_user_id(tg_id)
    if user_answer == id_lrn_tr[1] and tg_id == message.from_user.id:
        if level_down_once == 1:
            bot.send_message(message.from_user.id, 'Correct!', disable_notification=True)
            before_repeat_word(message)
        else:
            db.count_repetition(id_lrn_tr[0], user_id, "+1")
            bot.send_message(message.from_user.id, 'Correct!', disable_notification=True)
            before_repeat_word(message)
    elif tg_id == message.from_user.id:
        if level_down_once == 0:
            db.count_repetition(id_lrn_tr[0], user_id, "-1")
            level_down_once = 1
        bot.send_message(message.from_user.id, 'Try again')
        bot.register_next_step_handler(message, check_answer, tg_id, id_lrn_tr,  level_down_once=level_down_once)


# @bot.message_handler(commands=['add_word'])
# @bot.message_handler(text=['добавить слово', 'Добавить слово', 'добавить слово',])
# def dialog_add_word(message):
#     tg_id = message.from_user.id
#     bot.send_message(message.from_user.id, 'Write your word')
#     bot.register_next_step_handler(message, check_answer, tg_id)
#
# def check_word(message):
#     check_word()
#     If check_word() True:


bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.polling(none_stop=True)

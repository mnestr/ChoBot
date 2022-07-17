import telebot
import random
from telebot import types
from telebot import custom_filters
import db
import config

bot = telebot.TeleBot(config.token, parse_mode=None)

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
        self.repetition = None


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
    user_repetition.word_id = word_id
    for x in repetition:
        index = repetition.index(x)
        if x[0] == word_id:
            user_repetition.word_lrn = x[1]
            user_repetition.word_tr = x[2]
            user_repetition.repetition.pop(index)
            break
    return user_repetition.word_tr


@bot.message_handler(commands=['start'])
@bot.message_handler(text=['Hey!'])
def start(message):
    tg_id = message.from_user.id
    user_id = db.get_user_id(tg_id)
    if not user_id:
        create_user(message)
        user_id = db.get_user_id(tg_id)
        user_repetition.user_id = user_id
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
            bot.send_message(message.from_user.id, "You have 3 words to repeat. Let's repeat?", reply_markup=markup)


def want_to_start(message, tg_id):
    answer = message.text
    if answer in ['Sure!', 'Learn new words'] and tg_id == message.from_user.id:
        bot.send_message(message.chat.id, "Ok. Do you know this one?")
        show_word(message)
    elif answer == 'Anything to repeat?' and tg_id == message.from_user.id:
        before_repeat_word(message)


def show_word(message):
    tg_id = message.from_user.id
    new_words = db.get_new_words_from_dictionary(user_repetition.user_id)
    user_repetition.repetition = new_words
    pickup_word(new_words)
    word = user_repetition.word_lrn
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    answer_1 = types.KeyboardButton('Already know')
    answer_2 = types.KeyboardButton('Learn')
    answer_3 = types.KeyboardButton('Show a hint')
    markup.add(answer_1, answer_2, answer_3)
    bot.send_message(message.chat.id, word, reply_markup=markup)
    bot.register_next_step_handler(message, sort_word, tg_id)


def sort_word(message, tg_id):
    answer = message.text
    if answer == 'Learn' and tg_id == message.from_user.id and user_repetition.sorted_words_count > 1:
        save_word(user_repetition.user_id, user_repetition.word_id, 'repetition')
        user_repetition.sorted_words_count = 0
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Sure!')
        answer_2 = types.KeyboardButton('Later')
        markup.add(answer_1, answer_2)
        bot.send_message(message.from_user.id, 'You have 3 new words to learn. Wanna start?', reply_markup=markup)
        bot.register_next_step_handler(message, want_to_learn, tg_id)
    elif answer == 'Already know' and tg_id == message.from_user.id:
        save_word(user_repetition.user_id, user_repetition.word_id, 'already_know')
        bot.send_message(message.from_user.id, 'Lucky you! Here is another word:')
        show_word(message)
    elif answer == 'Learn' and tg_id == message.from_user.id:
        save_word(user_repetition.user_id, user_repetition.word_id, 'repetition')
        user_repetition.sorted_words_count += 1
        bot.send_message(message.from_user.id, "Ok, let's learn then! Here is another word:")
        show_word(message)
    elif answer == 'Show a hint' and tg_id == message.from_user.id:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Already know')
        answer_2 = types.KeyboardButton('Learn')
        markup.add(answer_1, answer_2)
        bot.send_message(message.chat.id, user_repetition.word_tr, reply_markup=markup)
        bot.register_next_step_handler(message, sort_word, tg_id)


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
    user_repetition.user_id = user_id
    repetition = db.get_repetition(user_id)
    user_repetition.repetition = repetition
    repeat_word(message)


def repeat_word(message):
    if len(user_repetition.repetition) > 0 and user_repetition.sorted_words_count == 0:
        tg_id = message.from_user.id
        word_tr = pickup_word(user_repetition.repetition)
        markup = pickup_answers_on_buttons()
        bot.send_message(message.chat.id, word_tr, reply_markup=markup)
        bot.register_next_step_handler(message, check_answer, tg_id)
    elif len(user_repetition.repetition) == 0:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        answer_1 = types.KeyboardButton('Anything to repeat?')
        answer_2 = types.KeyboardButton('Learn new words')
        markup.add(answer_1, answer_2)
        bot.send_message(message.from_user.id, "You've repeated all words. Try to memorize them and Come back later to repeat", reply_markup=markup)
        tg_id = message.from_user.id
        bot.register_next_step_handler(message, want_to_start, tg_id)


def check_answer(message, tg_id):
    user_answer = message.text
    if user_answer == user_repetition.word_lrn and tg_id == message.from_user.id:
        if user_repetition.level_down_once == 1:
            user_repetition.level_down_once = 0
            bot.send_message(message.from_user.id, 'Correct!')
            repeat_word(message)
        else:
            db.count_repetition(user_repetition.word_id, user_repetition.user_id, "+1")
            user_repetition.level_down_once = 0
            bot.send_message(message.from_user.id, 'Correct!')
            repeat_word(message)
    elif tg_id == message.from_user.id:
        if user_repetition.level_down_once == 0:
            db.count_repetition(user_repetition.word_id, user_repetition.user_id, "-1")
            user_repetition.level_down_once = 1
        bot.send_message(message.from_user.id, 'Try again')
        bot.register_next_step_handler(message, check_answer, tg_id)


bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.polling(none_stop=True)

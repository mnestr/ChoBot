import telebot
import random
from telebot import types
from telebot import custom_filters
import db
import config
from bs4 import BeautifulSoup
import requests
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage


state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.token, state_storage=state_storage, parse_mode=None)


class MyStates(StatesGroup):
    name = State()
    surname = State()
    age = State()

# repetitions = {1: 15 минут, 2: 6 часов, 3: 1 день, 4: 2 дня, 4: 3 суток, 5: 5 дней, 6: 7 дней, 7: 14 дней, 8: 1 месяц}


def scrap_word(word):
    url = "https://dictionary.cambridge.org/us/dictionary/english-russian/{0}".format(word)
    url = url.rstrip()
    headers = requests.utils.default_headers()

    headers.update({'User-Agent': 'My User Agent 1.0', })

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    block = soup.find("div", class_="def-block ddef_block")

    try:
        ps_tgs = soup.find("span", class_="pos dpos")
        prt_of_speach = ps_tgs.get_text(strip=True)

        tr_tgs = block.find("span", class_="trans dtrans dtrans-se")
        translation = tr_tgs.text.strip()

        mn_tgs = block.find_all("div", class_="def ddef_d db")
        meaning_lst = []
        for each in mn_tgs:
            meaning_lst.append(each.text.strip())
        meaning = " ".join(meaning_lst)

        examp_tgs = block.find_all("div", class_="examp dexamp")
        examp_lst = []
        for each in examp_tgs:
            examp_lst.append(each.text.strip())
        examp = "\n".join(examp_lst)
    except:
        return None
    return word, translation, prt_of_speach, meaning, examp


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
    markup = types.ReplyKeyboardMarkup(row_width=2)
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


def save_word(user_id, word_id, status, user_word_description=None):
    db.insert_word_user_dict(user_id, word_id, status, user_word_description)


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
    print(full_translation)
    examp_list = full_translation[4].split("\n")
    examp_list2 = []
    for i in examp_list:
        if not i: continue
        examp_list2.append("  \* " + i)
    examp = "\n".join(examp_list2)
    return examp


def show_word_description(message, word_id=None, scraped_desc=None):
    if word_id:
        full_description = db.get_descr_from_dict(word_id)
    elif scraped_desc:
        full_description = scraped_desc
    user_word_description = db.get_user_descr(word_id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("More",
                                           url='https://dictionary.cambridge.org/dictionary/english-russian/{0}'.format(
                                               full_description[0]))) #надо проверять доступно ли слово по этому адресу и скрывать кнопку если нет
    examp = format_string(full_description)
    if user_word_description:
        bot.send_message(message.chat.id,
                         "  *{0}* (_{1}_) - {2} *//* {3}\n\n_Additional meaning:_{5}\n\n_Example:_\n{4}".format(
                                                                                    full_description[0],
                                                                                    full_description[2],
                                                                                    full_description[1],
                                                                                    full_description[3],
                                                                                    examp,
                                                                                    user_word_description),
                         disable_notification=True, reply_markup=markup, parse_mode='markdown')
    else:
        bot.send_message(message.chat.id,
                         "  *{0}* (_{1}_) - {2} *//* {3}\n\n_Example:_\n{4}".format(full_description[0],
                                                                                    full_description[2],
                                                                                    full_description[1],
                                                                                    full_description[3],
                                                                                    examp),
                         disable_notification=True, reply_markup=markup, parse_mode='markdown')


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
        bot.send_message(message.from_user.id, "Hi! I'm Steve!", disable_notification=True,)
        photo = open('Pictures/1.jpg', 'rb')
        bot.send_photo(message.from_user.id, photo, disable_notification=True,)
        bot.send_message(message.from_user.id, "Wanna learn some words?", disable_notification=True, reply_markup=markup)
        bot.register_next_step_handler(message, want_to_start)
    else:
        repetition = db.get_repetition(user_id)
        if not repetition:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            answer_1 = types.KeyboardButton('Learn new words')
            answer_2 = types.KeyboardButton('Add word')
            markup.add(answer_1, answer_2)
            bot.send_message(message.from_user.id, "You have nothing to repeat. Let's see some new words?", disable_notification=True, reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            answer_1 = types.KeyboardButton('Repeat')
            markup.add(answer_1)
            bot.send_message(message.from_user.id, "You have {0} words to repeat. Let's repeat?".format(len(repetition)), disable_notification=True, reply_markup=markup)


@bot.message_handler(text=['Sure!', 'Learn new words', 'Anything to repeat?'])
def want_to_start(message):
    answer = message.text
    if answer in ['Sure!', 'Learn new words']:
        bot.send_message(message.chat.id, "Ok. Do you know this one?", disable_notification=True,)
        show_word(message)
    elif answer == 'Anything to repeat?':
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
        bot.send_message(message.from_user.id, 'You have 3 new words to learn. Wanna start?', disable_notification=True, reply_markup=markup)
        bot.register_next_step_handler(message, want_to_learn, tg_id)
    elif answer == 'Already know' and tg_id == message.from_user.id:
        save_word(user_id, id_lrn_tr[0], 'already_know')
        bot.send_message(message.from_user.id, 'Lucky you! Here is another word:', disable_notification=True,)
        show_word(message, sorted_words_count)
    elif answer == 'Learn' and tg_id == message.from_user.id:
        save_word(user_id, id_lrn_tr[0], 'repetition')
        sorted_words_count += 1
        bot.send_message(message.from_user.id, "Ok, let's learn then! Here is another word:", disable_notification=True,)
        show_word(message, sorted_words_count)
    elif answer == 'Show translation' and tg_id == message.from_user.id:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        answer_1 = types.KeyboardButton('Already know')
        answer_2 = types.KeyboardButton('Learn')
        markup.add(answer_1, answer_2)
        show_word_description(message, word_id=id_lrn_tr[0])
        bot.send_message(message.chat.id, "So, do you know it?", disable_notification=True, reply_markup=markup)
        bot.register_next_step_handler(message, sort_word, tg_id, sorted_words_count, id_lrn_tr)


def want_to_learn(message, tg_id):
    answer = message.text
    if answer == 'Sure!' and tg_id == message.from_user.id:
        before_repeat_word(message)
    elif answer == 'Later' and tg_id == message.from_user.id:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        answer_1 = types.KeyboardButton('Anything to repeat?')
        answer_2 = types.KeyboardButton('Learn new words')
        answer_3 = types.KeyboardButton('Add word')
        markup.add(answer_1, answer_2, answer_3)
        bot.send_message(message.from_user.id, 'As you wish=/', disable_notification=True, reply_markup=markup)


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
        bot.send_message(message.chat.id, id_lrn_tr[2], disable_notification=True, reply_markup=markup)
        bot.register_next_step_handler(message, check_answer, tg_id, id_lrn_tr)
    elif len(repetition) == 0:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        answer_1 = types.KeyboardButton('Anything to repeat?')
        answer_2 = types.KeyboardButton('Learn new words')
        answer_3 = types.KeyboardButton('Add word')
        markup.add(answer_1, answer_2, answer_3)
        bot.send_message(message.from_user.id, "You've repeated all words. Try to memorize them and Come back later to repeat", disable_notification=True, reply_markup=markup)


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
        bot.send_message(message.from_user.id, 'Try again', disable_notification=True,)
        bot.register_next_step_handler(message, check_answer, tg_id, id_lrn_tr,  level_down_once=level_down_once)


@bot.message_handler(commands=['add_word'])
@bot.message_handler(text=['добавить слово', 'add word', 'Add word'])
def start_dialog_add_word(message):
    tg_id = message.from_user.id
    bot.send_message(message.from_user.id, 'Write english word that you want to learn:', disable_notification=True,)
    bot.register_next_step_handler(message, recieve_word, tg_id)


def recieve_word(message, tg_id):
    if tg_id == message.from_user.id:
        user_word = message.text
        scraped_desc = None
        # check_spelling()
        # check_english_word()
        word_id = db.find_word_in_db(user_word)
        user_id = db.get_user_id(tg_id)
        if not word_id:
            scraped_desc = scrap_word(user_word)
            if not scraped_desc:
                word_id = db.insert_word(user_word, None, None, None, None, user_id)
                bot.send_message(message.from_user.id, "Can't find any description. Please add your own:", disable_notification=True,)
                bot.register_next_step_handler(message, add_user_word_desc, tg_id, word_id)
            elif scraped_desc:
                db.insert_word(scraped_desc[0], scraped_desc[1], scraped_desc[2], scraped_desc[3], scraped_desc[4], user_id)
                show_word_description(message, word_id=word_id, scraped_desc=scraped_desc)
                markup = types.ReplyKeyboardMarkup(row_width=2)
                answer_1 = types.KeyboardButton('Yes, please')
                answer_2 = types.KeyboardButton('Nope')
                answer_3 = types.KeyboardButton('Add another description')
                markup.add(answer_1, answer_2, answer_3)
                bot.send_message(message.from_user.id, "I've found it! Do you want to add it to your learning list?",
                                 disable_notification=True, reply_markup=markup)
                bot.register_next_step_handler(message, user_answer_dialog_add_word, tg_id, word_id)
        elif word_id:
            show_word_description(message, word_id=word_id, scraped_desc=scraped_desc)
            markup = types.ReplyKeyboardMarkup(row_width=2)
            answer_1 = types.KeyboardButton('Yes, please')
            answer_2 = types.KeyboardButton('Nope')
            answer_3 = types.KeyboardButton('Add another description')
            markup.add(answer_1, answer_2, answer_3)
            bot.send_message(message.from_user.id, "I've found it! Do you want to add it to your learning list?",
                             disable_notification=True, reply_markup=markup)
            bot.register_next_step_handler(message, user_answer_dialog_add_word, tg_id, word_id)


def user_answer_dialog_add_word(message, tg_id, word_id):
    if tg_id == message.from_user.id:
        answer = message.text
        if answer == 'Yep':
            user_id = db.get_user_id(tg_id)
            save_word(user_id, word_id, 'repetition')
            bot.send_message(message.from_user.id, "Saved it! What's next?", disable_notification=True,)
        elif answer == 'Add another description':
            bot.send_message(message.from_user.id, 'Write word description:', disable_notification=True,)
            bot.register_next_step_handler(message, add_user_word_desc, tg_id, word_id)
        elif answer == 'Nope':
            markup = types.ReplyKeyboardMarkup(row_width=2)
            answer_1 = types.KeyboardButton('Anything to repeat?')
            answer_2 = types.KeyboardButton('Learn new words')
            answer_3 = types.KeyboardButton('Add word')
            markup.add(answer_1, answer_2, answer_3)
            bot.send_message(message.from_user.id, "Ok, what's next?", disable_notification=True, reply_markup=markup)


def add_user_word_desc(message, tg_id, word_id):
    if tg_id == message.from_user.id:
        user_id = db.get_user_id(tg_id)
        save_word(user_id, word_id, 'repetition', user_word_description=message.text)
        markup = types.ReplyKeyboardMarkup(row_width=2)
        answer_1 = types.KeyboardButton('Anything to repeat?')
        answer_2 = types.KeyboardButton('Learn new words')
        answer_3 = types.KeyboardButton('Add word')
        markup.add(answer_1, answer_2, answer_3)
        bot.send_message(message.from_user.id, "Saved it! Saved it! What's next?", disable_notification=True, reply_markup=markup)


@bot.message_handler(commands=['test'])
def start_dialog_add_word(message):
    """
    Start command. Here we are starting state
    """
    bot.set_state(message.from_user.id, MyStates.name, message.chat.id)
    bot.send_message(message.chat.id, 'Hi, write me a name')


@bot.message_handler(state=MyStates.name)
def name_get(message):
    """
    State 1. Will process when user's state is MyStates.name.
    """
    bot.send_message(message.chat.id, 'Now write me a surname')
    bot.set_state(message.from_user.id, MyStates.surname, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['name'] = message.text
    print(data)
    bot.delete_state(message.from_user.id, message.chat.id)
    print(data)


@bot.message_handler(commands=['name'])
def show_name(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        print(data)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.polling(none_stop=True)

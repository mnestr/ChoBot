import telebot
from telebot import types
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
import random
import os
import subtitles_extractor as se
import db
import config
from bs4 import BeautifulSoup
import requests


state_storage = StateMemoryStorage()
bot = telebot.TeleBot(config.token, state_storage=state_storage, parse_mode=None, num_threads=3)


class MyStates(StatesGroup):
    sort_words = State()
    before_repeat_word = State()
    repetition = State()
    waiting_for_word = State()
    adding_user_word_desc = State()
    user_answer_dialog_add_word = State()
    id_lrn_tr = State()
    sorted_words_count = State()
    level_down_once = State()
    word_id = State()
    waiting_for_subtitles = State()
    subtitles_id = State()

# repetitions = {1: 15 минут, 2: 6 часов, 3: 1 день, 4: 2 дня, 4: 3 суток, 5: 5 дней, 6: 7 дней, 7: 14 дней, 8: 1 месяц}


def download_file(message):
    file_info = bot.get_file(message.document.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.token, file_info.file_path))
    open(message.document.file_unique_id, "wb").write(file.content)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as rt_data:
        rt_data['subtitles_id'] = message.document.file_unique_id


def delete_file(message):
    if os.path.exists(message.document.file_unique_id):
        os.remove(message.document.file_unique_id)


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
    chat_id = int(message.chat.id)
    first_name = str(message.from_user.first_name)
    last_name = str(message.from_user.last_name)
    user_name = str(message.from_user.username)
    language_code = str(message.from_user.language_code)
    db.db_insert_user(tg_id, chat_id, first_name, last_name, language_code, user_name)


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
    db.upsert_word_user_dict(user_id, word_id, status, user_word_description)


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
    markup.add(types.InlineKeyboardButton("Check Cambridge definition",
                                           url='https://dictionary.cambridge.org/dictionary/english-russian/{0}'.format(
                                               full_description[0])))
    # надо проверять доступно ли слово по этому адресу и скрывать кнопку если нет
    examp = format_string(full_description)
    if user_word_description[0]:
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


def base_buttons():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    answer_1 = types.KeyboardButton('Anything to repeat?')
    answer_2 = types.KeyboardButton('Learn new words')
    answer_3 = types.KeyboardButton('Add word')
    answer_4 = types.KeyboardButton('Add words from subtitles')
    markup.add(answer_1, answer_2, answer_3, answer_4)
    return markup


@bot.message_handler(commands=['start'])
@bot.message_handler(text=['Hey!'])
def start(message):
    tg_id = message.from_user.id
    user_id = db.get_user_id(tg_id)
    if not user_id:
        create_user(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        answer_1 = types.KeyboardButton('Learn new words')
        markup.add(answer_1)
        bot.send_message(message.chat.id, "Hi! I'm Steve!", disable_notification=True,)
        photo = open('Pictures/1.jpg', 'rb')
        bot.send_photo(message.from_user.id, photo, disable_notification=True,)
        bot.send_message(message.chat.id, "Wanna learn some words?", disable_notification=True, reply_markup=markup)
    else:
        repetition = db.get_repetition(user_id)
        if not repetition:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            answer_1 = types.KeyboardButton('Learn new words')
            answer_2 = types.KeyboardButton('Add word')
            markup.add(answer_1, answer_2)
            bot.send_message(message.chat.id, "You have nothing to repeat. Let's see some new words?",
                             disable_notification=True, reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(row_width=2)
            answer_1 = types.KeyboardButton('Repeat')
            answer_2 = types.KeyboardButton('Later')
            markup.add(answer_1, answer_2)
            bot.set_state(message.from_user.id, MyStates.before_repeat_word, message.chat.id)
            bot.send_message(message.chat.id, "You have {0} words to repeat. Let's repeat?".format(len(repetition)),
                             disable_notification=True, reply_markup=markup)


@bot.message_handler(commands=['home'])
@bot.message_handler(text=['Sure!', 'Learn new words', 'Anything to repeat?', 'Later'])
def main_dialog(message):
    if message.text == 'Learn new words':
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, "Ok. Do you know this one?", disable_notification=True,)
        bot.set_state(message.from_user.id, MyStates.sort_words, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['sorted_words_count'] = 0
        show_word(message)
    elif message.text in ('Anything to repeat?', 'Sure!'):
        repeat_word(message)
    elif message.text == 'Later':
        markup = base_buttons()
        bot.send_message(message.chat.id, 'As you wish=/', disable_notification=True, reply_markup=markup)
    elif message.text == '/home':
        markup = base_buttons()
        bot.send_message(message.chat.id, 'Hey, whats up?', disable_notification=True, reply_markup=markup)


def show_word(message):
    bot.send_chat_action(message.chat.id, 'typing')  # show the bot "typing" (max. 5 secs)
    user_id = db.get_user_id(message.from_user.id)
    new_words = db.get_new_words_from_dictionary(user_id)
    id_lrn_tr = pickup_word(new_words)
    markup = types.ReplyKeyboardMarkup(row_width=2)
    answer_1 = types.KeyboardButton('Already know')
    answer_2 = types.KeyboardButton('Learn')
    answer_3 = types.KeyboardButton('Show translation')
    markup.add(answer_1, answer_2, answer_3)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['id_lrn_tr'] = id_lrn_tr
    bot.send_message(message.chat.id, id_lrn_tr[1], disable_notification=True, reply_markup=markup)


@bot.message_handler(state=MyStates.sort_words)
def sort_word(message):
    answer = message.text
    user_id = db.get_user_id(message.from_user.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as rt_data:
        data = rt_data
    if answer == 'Learn' and data['sorted_words_count'] > 1:
        save_word(user_id, data['id_lrn_tr'][0], 'repetition')
        markup = types.ReplyKeyboardMarkup(row_width=2)
        answer_1 = types.KeyboardButton('Sure!')
        answer_2 = types.KeyboardButton('Later')
        markup.add(answer_1, answer_2)
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, 'You have 3 new words to learn. Wanna start?', disable_notification=True, reply_markup=markup)
    elif answer == 'Already know':
        save_word(user_id, data['id_lrn_tr'][0], 'already_know')
        bot.send_message(message.chat.id, 'Lucky you! Here is another word:', disable_notification=True,)
        show_word(message)
    elif answer == 'Learn':
        save_word(user_id, data['id_lrn_tr'][0], 'repetition')
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['sorted_words_count'] += 1
        bot.send_message(message.chat.id, "Ok, let's learn then! Here is another word:", disable_notification=True,)
        show_word(message)
    elif answer == 'Show translation':
        bot.send_chat_action(message.chat.id, 'typing')  # show the bot "typing" (max. 5 secs)
        markup = types.ReplyKeyboardMarkup(row_width=2)
        answer_1 = types.KeyboardButton('Already know')
        answer_2 = types.KeyboardButton('Learn')
        markup.add(answer_1, answer_2)
        show_word_description(message, word_id=data['id_lrn_tr'][0])
        bot.send_message(message.chat.id, "So, do you know it?", disable_notification=True, reply_markup=markup)


def repeat_word(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_id = db.get_user_id(message.from_user.id)
    repetition = db.get_repetition(user_id)
    if len(repetition) > 0:
        bot.send_message(message.chat.id, "You have {0} words to repeat. Do you remember:".format(len(repetition)))
        id_lrn_tr = pickup_word(repetition)
        markup = pickup_answers_on_buttons(id_lrn_tr)
        bot.set_state(message.from_user.id, MyStates.repetition, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['level_down_once'] = 0
            data['id_lrn_tr'] = id_lrn_tr
        bot.send_message(message.chat.id, id_lrn_tr[2], disable_notification=True, reply_markup=markup)
    elif len(repetition) == 0:
        markup = base_buttons()
        bot.delete_state(message.from_user.id, message.chat.id)
        statistics = db.get_statistics(message.from_user.id)
        bot.send_message(message.chat.id, "You've repeated all words. Try to memorize them and Come back later to "
                                          "repeat.\n\nHere is your short statistics:\n"
                                          "Already known *{0}* words. In progress *{2}* words. "
                                          "In a queue to learn *{3}*. Mastered *{1}* words.".format(
            statistics['already_know'], statistics['mastered'], statistics['repetition'], statistics['to_learn']),
                         disable_notification=True, reply_markup=markup, parse_mode='markdown')


@bot.message_handler(state=MyStates.repetition)
def check_answer(message):
    answer = message.text
    user_id = db.get_user_id(message.from_user.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as rt_data:
        data = rt_data
    if answer == data['id_lrn_tr'][1]:
        if data['level_down_once'] == 1:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as rt_data:
                rt_data['level_down_once'] = 0
            bot.send_message(message.chat.id, 'Correct!', disable_notification=True)
            bot.send_chat_action(message.chat.id, 'typing')
            show_word_description(message, word_id=data['id_lrn_tr'][0])
            repeat_word(message)
        else:
            db.count_repetition(data['id_lrn_tr'][0], user_id, "+1")
            with bot.retrieve_data(message.from_user.id, message.chat.id) as rt_data:
                rt_data['level_down_once'] = 0
            bot.send_message(message.chat.id, 'Correct!', disable_notification=True)
            bot.send_chat_action(message.chat.id, 'typing')
            show_word_description(message, word_id=data['id_lrn_tr'][0])
            repeat_word(message)
    else:
        if data['level_down_once'] == 0:
            db.count_repetition(data['id_lrn_tr'][0], user_id, "-1")
            with bot.retrieve_data(message.from_user.id, message.chat.id) as rt_data:
                rt_data['level_down_once'] = 1
        bot.send_message(message.chat.id, 'Try again', disable_notification=True,)


@bot.message_handler(text=['добавить слово', 'add word', 'Add word'])
def start_dialog_add_word(message):
    bot.set_state(message.from_user.id, MyStates.waiting_for_word, message.chat.id)
    bot.send_message(message.chat.id, 'Write english word that you want to learn:', disable_notification=True,
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=MyStates.waiting_for_word)
def recieve_word(message):
    user_word = message.text.lower()
    scraped_desc = None
    # check_spelling()
    # check_english_word()
    word_id = db.find_word_in_dict(user_word)
    user_id = db.get_user_id(message.from_user.id)
    if not word_id:
        scraped_desc = scrap_word(user_word)
        if not scraped_desc:
            db.insert_word(user_word, None, None, None, None, user_id)
            bot.send_message(message.chat.id, "Can't find any description. Please add your own:",
                             disable_notification=True,)
            bot.set_state(message.from_user.id, MyStates.adding_user_word_desc, message.chat.id)
        elif scraped_desc:
            word_id = db.insert_word(scraped_desc[0], scraped_desc[1], scraped_desc[2], scraped_desc[3],
                                     scraped_desc[4], user_id)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['word_id'] = word_id
            show_word_description(message, word_id=word_id, scraped_desc=scraped_desc)
            markup = types.ReplyKeyboardMarkup(row_width=2)
            answer_1 = types.KeyboardButton('Yes, please')
            answer_2 = types.KeyboardButton('Nope')
            answer_3 = types.KeyboardButton('Add another description')
            markup.add(answer_1, answer_2, answer_3)
            bot.set_state(message.from_user.id, MyStates.user_answer_dialog_add_word, message.chat.id)
            bot.send_message(message.chat.id, "I have such description of the word. "
                                              "Do you want to add it to your learning list?",
                             disable_notification=True, reply_markup=markup)
    elif word_id:
        show_word_description(message, word_id=word_id, scraped_desc=scraped_desc)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['word_id'] = word_id
        markup = base_buttons()
        bot.set_state(message.from_user.id, MyStates.user_answer_dialog_add_word, message.chat.id)
        bot.send_message(message.chat.id, "I've found it! Do you want to add it to your learning list?",
                         disable_notification=True, reply_markup=markup)


@bot.message_handler(state=MyStates.user_answer_dialog_add_word)
def user_answer_dialog_add_word(message):
    answer = message.text
    if answer == 'Yes, please':
        user_id = db.get_user_id(message.from_user.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            word_id = data['word_id']
        save_word(user_id, word_id, 'repetition')
        markup = base_buttons()
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "Saved it! What's next?", disable_notification=True, reply_markup=markup)
    elif answer == 'Add another description':
        bot.send_message(message.chat.id, 'Write word description:', disable_notification=True)
        bot.set_state(message.from_user.id, MyStates.adding_user_word_desc, message.chat.id)
    elif answer in ('Nope', 'no'):
        markup = base_buttons()
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id, "Ok, what's next?", disable_notification=True, reply_markup=markup)


@bot.message_handler(state=MyStates.adding_user_word_desc)
def add_user_word_desc(message):
    user_id = db.get_user_id(message.from_user.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word_id = data['word_id']
    save_word(user_id, word_id, 'repetition', user_word_description=message.text)
    markup = base_buttons()
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "Saved it! What's next?", disable_notification=True, reply_markup=markup)


@bot.message_handler(text=['add subtitles', 'Add words from subtitles'])
def start_dialog_add_subtitles(message):
    bot.set_state(message.from_user.id, MyStates.waiting_for_subtitles, message.chat.id)
    bot.send_message(message.chat.id, 'Hey, drop me your subtitles. It should be .srt or .txt file', disable_notification=True)


@bot.message_handler(state=MyStates.waiting_for_subtitles, content_types=['document'])
def handle_subtitles(message):
    if message.document.file_name[-4:] in ['.srt', '.txt']:
        bot.send_message(message.chat.id, "I've received your file. I need some time to process it. I'll message you when I'm done.",
                         disable_notification=True)
        download_file(message)
        raw_text = se.read_file(message.document.file_unique_id)
        delete_file(message)
        bot.delete_state(message.from_user.id, message.chat.id)
        text = se.clean_text(raw_text)
        lem_words = se.lemmatize_words(text)
        cleaned_words = se.clean(lem_words)
        count_cleaned_words = len(cleaned_words)
        bot.send_chat_action(message.chat.id, 'typing')  # show the bot "typing" (max. 5 secs)
        count_words_without_desc, count_words_added, count_words_already_known = se.add_to_user(message, cleaned_words)
        markup = base_buttons()
        bot.send_message(message.chat.id, "Ready! I've found {0} words in the text. You already know {1} words from this "
                                          "text. But {2} are new for you or at least they are not in your learning "
                                          "list, so i've added them.".format(count_cleaned_words, count_words_already_known, count_words_added),
                         disable_notification=False, reply_markup=markup)
    else:
        markup = base_buttons()
        bot.send_message(message.chat.id, "Sorry but I can't work with such file.(( I can only.srt or .txt file",
                         disable_notification=True, reply_markup=markup)


# default handler for every other text
@bot.message_handler(func=lambda message: True, content_types=['text'])
def command_default(message):
    # this is the standard reply to a normal message
    markup = base_buttons()
    bot.send_message(message.chat.id, "I don't understand. Maybe try one of the options on buttons",
                     disable_notification=True, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.polling(none_stop=True)

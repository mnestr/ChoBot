import string
import db
from bs4 import BeautifulSoup
import requests
import spacy
import re


def read_file(file_name):
    raw_text = ""
    file = open(file_name, "r")
    for line in file:
        raw_text += line
    raw_text = raw_text.lower()
    return raw_text


def clean_text(raw_text):
    CLEANR = re.compile('<.*?>')
    text = re.sub(CLEANR, '', raw_text)
    text = text.replace("\n", " ")
    text = text.lower()
    return text


def lemmatize_words(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    lem_words = [token.lemma_ for token in doc]
    return lem_words


def clean(words):
    cleaned_words = []
    stop_words = {'yes', 'Ahhh!', 'Hyah', 'huh', 'Hmm', 'yah', 'i', 'doesn', "needn't", 'against', 'just', 'at', "wouldn't", 'me', "weren't", 'out', 'an', 'themselves', "she's", 'hadn', 'between', 'you', 'himself', 'ours', 't', 'does', 'most', "you're", 'him', 'mightn', "mustn't", 'your', 'was', 'o', "doesn't", 'haven', 'through', "isn't", 'what', "didn't", "shouldn't", 'weren', 'did', 'below', 'then', 'after', 'other', 'aren', 'once', 'of', 'in', 'to', 'is', 'before', 're', "you'd", 'a', 'during', 'he', 'hasn', 'wasn', 'here', 's', "couldn't", 'didn', 'ma', 'some', 'the', 'but', 'mustn', 'whom', 'yourselves', 'and', 'than', 'for', 'from', 'under', "you'll", 'about', 'will', 'few', "it's", 'her', 'there', "shan't", 'am', 'all', 'not', "hasn't", 'its', 'same', 've', 'their', 'as', "won't", 'on', 'by', 'this', 'because', 'each', 'shan', 'are', 'only', 'can', "should've", 'such', 'when', 'ain', 'that', 'into', 'where', 'it', "haven't", 'why', 'do', 'who', 'has', 'them', 'hers', 'nor', 'until', 'down', 'shouldn', 'his', 'itself', 'ourselves', 'those', 'she', 'had', 'further', 'too', 'more', 'm', 'with', 'wouldn', 'if', 'll', 'yours', 'being', 'having', 'own', 'these', 'how', 'couldn', 'now', 'needn', 'off', 'my', 'again', 'so', 'which', "you've", "aren't", 'were', 'be', 'they', 'myself', 'our', 'yourself', "wasn't", 'over', 'no', 'up', 'isn', 'or', 'any', 'd', 'y', "mightn't", 'won', 'very', 'while', 'herself', 'have', 'above', 'should', 'both', 'doing', 'been', 'theirs', "don't", "that'll", 'we', "hadn't", 'don'}
    words = list(set(words))
    for w in words:
        if w not in stop_words \
                and w[0] not in string.punctuation \
                and w[-1] not in string.punctuation \
                and not w[0].isdigit()\
                and len(w) > 2:
            cleaned_words.append(w)
    return cleaned_words


def add_to_user(message, words):
    words_without_desc = []
    words_added = []
    words_already_known = []
    user_id = db.get_user_id(message.from_user.id)
    for word in words:
        print(word)
        word_id = db.find_word_in_dict(word)
        if not word_id:
            scraped_desc = scrap_word(word)
            if not scraped_desc:
                words_without_desc.append(word)
            elif scraped_desc:
                word_id = db.insert_word(scraped_desc[0], scraped_desc[1], scraped_desc[2], scraped_desc[3], scraped_desc[4], user_id)
                db.upsert_word_user_dict(user_id, word_id, 'to_learn', added_by_user=1)
                words_added.append(word)
        elif word_id:
            in_user_dict = db.check_if_word_in_user_dict(word_id)
            if not in_user_dict:
                db.upsert_word_user_dict(user_id, word_id, 'to_learn', added_by_user=1)
                words_added.append(word)
            elif in_user_dict:
                words_already_known.append(word)
    count_words_without_desc = len(words_without_desc)
    count_words_added = len(words_added)
    count_words_already_known = len(words_already_known)
    return count_words_without_desc, count_words_added, count_words_already_known


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
